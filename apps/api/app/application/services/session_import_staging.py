"""Stage historical session rows for review. Writes no sessions.

Decision 7 keeps historical acceptance separate from booking eligibility: a row
may name a practitioner who is suspended or unaccredited today, because the
delivery already happened. What it may not do is create future work, so a row
dated after the import day is rejected rather than staged as acceptable.

Applying a staged batch is not implemented here. It requires the historical
write entry point agent 1 owns, and calling the live session use case would
merge the two rule sets that this separation exists to keep apart.
"""

import hashlib
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import date, datetime

from app.application.services.provider_alias_reconciliation import (
    NameOutcome,
    NameResolution,
    ProviderAliasReconciliationService,
)
from app.domain.entities.client import ClientEntity
from app.domain.entities.eligible_member import EligibleMember
from app.domain.entities.service import ServiceEntity
from app.domain.entities.session_import import SessionImportRowEntity
from app.domain.enums import (
    ClientType,
    SessionAttendance,
    SessionCategory,
    SessionClinicalStatus,
    SessionStatus,
    SessionType,
    UserStatus,
)
from app.domain.enums.provider_network import DeliveryContext, ImportRowOutcome
from app.domain.exceptions import DomainError
from app.domain.repositories.client_repository import ClientRepository
from app.domain.repositories.diagnosis_repository import DiagnosisRepository
from app.domain.repositories.eligible_member_repository import EligibleMemberRepository
from app.domain.repositories.provider_network_repository import (
    ProviderAffiliationRepository,
    SessionImportRepository,
)
from app.domain.repositories.service_repository import ServiceRepository
from app.domain.repositories.user_repository import UserRepository
from app.domain.services.diagnosis_alias import normalise_diagnosis_value
from app.domain.services.provider_alias_normalisation import normalise_practitioner_name
from app.domain.services.provider_network_calendar import boundary_day
from app.domain.value_objects.core import ClientId, TenantId
from app.domain.value_objects.provider_network import (
    ProviderAffiliationId,
    SessionImportBatchId,
    SessionImportRowId,
)
from app.shared.utils.generators import generate_cuid
from app.shared.utils.replay_key import DUPLICATE_PREFIX, deferred_key
from app.shared.utils.session_import_normalisation import (
    Unmapped,
    classify_gender,
    map_category,
    map_client_type,
    map_intervention,
    map_session_type,
    map_status,
)

#: An approver name matching more than one active user in the tenant. Distinct
#: from a `str` UserId so a preloaded ambiguous name is never mistaken for one.
_AMBIGUOUS_APPROVER = object()

_NAME_OUTCOMES = {
    NameOutcome.MISSING: ImportRowOutcome.MISSING_PRACTITIONER,
    NameOutcome.UNMAPPED: ImportRowOutcome.UNMAPPED_PRACTITIONER,
    NameOutcome.AMBIGUOUS: ImportRowOutcome.AMBIGUOUS_PRACTITIONER,
    NameOutcome.REJECTED: ImportRowOutcome.REJECTED,
}

SOURCE_KEY_STRATEGY = "source_record_key"
FILE_ROW_KEY_STRATEGY = "file:{hash}:row:{n}"

_SAMPLE_SIZE = 3


@dataclass(frozen=True)
class SourceRow:
    """One parsed source row. Deliberately free of any live session shape.

    The raw_* fields carry the extract's own spellings; normalisation and
    resolution happen in the staging service, never in the parser.
    """

    row_number: int
    raw_practitioner_name: str | None
    session_date: date | None
    source_record_key: str | None = None
    organisation_affiliation_id: str | None = None
    member_id: str | None = None
    service_id: str | None = None
    raw_client_name: str | None = None
    raw_client_code: str | None = None
    raw_member_ref: str | None = None
    raw_gender: str | None = None
    raw_audience: str | None = None
    raw_session_type: str | None = None
    raw_category: str | None = None
    raw_status: str | None = None
    raw_intervention: str | None = None
    raw_client_type: str | None = None
    raw_rate: str | None = None
    raw_session_number: str | None = None
    raw_issue_topic: str | None = None
    raw_diagnosis: str | None = None
    raw_diagnosis_type: str | None = None
    raw_approved_by: str | None = None
    raw_organisation_session: str | None = None


#: What the workbook's Organisation Session column says. Blank stays absent,
#: because decision 2 forbids reading a missing value as direct delivery.
_ORGANISATION_SESSION = {
    "yes": True,
    "y": True,
    "true": True,
    "1": True,
    "no": False,
    "n": False,
    "false": False,
    "0": False,
}


def _organisation_session(raw: str | None) -> bool | None:
    """True for organisation delivery, False for direct, None for no evidence."""
    if raw is None:
        return None
    return _ORGANISATION_SESSION.get(raw.strip().lower())


@dataclass(frozen=True)
class Normalised:
    """The activity-log values a staged row carries once mapped.

    An unmapped value stays None here and leaves its reason on the row; an
    optional field that will not map must not block a row whose identities all
    resolve. `issue_topic`, `diagnosis_type_id`/`diagnosis_id` and
    `approved_by` are enrichment for the same reason: a session that already
    happened is not refused for lacking a clean diagnosis code or a
    recognised approver name. There is no `feedback` field here: CLIENT
    FEEDBACK is free text that PRIV-01 forbids reaching an employer aggregate
    (session_import_normalisation.py), so it is never imported at all.
    """

    session_type: SessionType | None = None
    category: SessionCategory | None = None
    clinical_status: SessionClinicalStatus | None = None
    session_status: SessionStatus | None = None
    client_type: ClientType | None = None
    rate_ugx: int | None = None
    session_number: int | None = None
    issue_topic: str | None = None
    diagnosis_type_id: str | None = None
    diagnosis_id: str | None = None
    approved_by: str | None = None


@dataclass(frozen=True)
class StagedRow:
    """The outcome for one source row, ready to persist."""

    row_number: int
    outcome: ImportRowOutcome
    delivery_context: DeliveryContext
    provider_id: object | None
    provider_affiliation_id: ProviderAffiliationId | None
    member_id: str | None
    service_id: str | None
    reasons: tuple[str, ...]
    replay_key: str
    source_record_key: str | None
    raw_practitioner_name: str | None
    session_date: date | None
    client_id: str | None = None
    attendance: SessionAttendance | None = None
    normalised: Normalised = Normalised()


class SessionImportStagingService:
    def __init__(
        self,
        aliases: ProviderAliasReconciliationService,
        affiliations: ProviderAffiliationRepository,
        imports: SessionImportRepository,
        clients: ClientRepository,
        members: EligibleMemberRepository,
        services: ServiceRepository,
        diagnoses: DiagnosisRepository,
        users: UserRepository,
    ):
        self._aliases = aliases
        self._affiliations = affiliations
        self._imports = imports
        self._clients = clients
        self._members = members
        self._services = services
        self._diagnoses = diagnoses
        self._users = users
        self._client_cache: dict[str, ClientEntity | None] = {}
        self._client_code_cache: dict[str, ClientEntity | None] = {}
        self._member_cache: dict[tuple[str, str], EligibleMember | None] = {}
        self._service_cache: dict[str, ServiceEntity | None] = {}
        self._staged_by_key: dict[str, SessionImportRowEntity | None] = {}
        self._diagnosis_aliases: dict[str, tuple[str, str | None]] | None = None
        self._approver_by_name: dict[str, str | object] | None = None

    async def preload(self, tenant_id: TenantId, rows: Sequence[SourceRow], file_hash: str) -> None:
        """Batch every lookup `stage_row` would otherwise repeat once per row.

        Only fills caches: a value it missed still falls back to its own
        query, so this changes what staging costs and never what it decides.
        """
        await self._preload_clients(tenant_id, rows)
        await self._preload_members(tenant_id, rows)
        await self._preload_services(tenant_id, rows)
        await self._preload_diagnosis_aliases()
        await self._preload_approvers(tenant_id)
        keys = [_replay_key(row, file_hash) for row in rows]
        if not keys:
            return
        found = await self._imports.find_rows_by_replay_keys(tenant_id, keys)
        for key in keys:
            self._staged_by_key.setdefault(key, found.get(key))

    async def _preload_diagnosis_aliases(self) -> None:
        if self._diagnosis_aliases is None:
            self._diagnosis_aliases = await self._diagnoses.alias_lookup()

    async def _preload_approvers(self, tenant_id: TenantId) -> None:
        """Every active user's display name, normalised, for matching `Approved By`.

        A name matching more than one active user is unusable as a lookup
        key and is dropped rather than guessed at; the row's note says so.
        """
        if self._approver_by_name is not None:
            return
        by_name: dict[str, str | object] = {}
        offset = 0
        while True:
            page = await self._users.list_all(
                tenant_id, status=UserStatus.ACTIVE, limit=200, offset=offset
            )
            for user in page:
                if not user.display_name:
                    continue
                key = normalise_practitioner_name(user.display_name)
                if not key:
                    continue
                if key in by_name and by_name[key] != user.id.value:
                    by_name[key] = _AMBIGUOUS_APPROVER
                else:
                    by_name[key] = user.id.value
            if len(page) < 200:
                break
            offset += 200
        self._approver_by_name = by_name

    async def _preload_clients(self, tenant_id: TenantId, rows: Sequence[SourceRow]) -> None:
        for code in {row.raw_client_code for row in rows if row.raw_client_code}:
            if code not in self._client_code_cache:
                self._client_code_cache[code] = await self._clients.get_by_code(tenant_id, code)
        names = {
            row.raw_client_name for row in rows if not row.raw_client_code and row.raw_client_name
        }
        for name in names:
            if name not in self._client_cache:
                self._client_cache[name] = await self._clients.get_by_name_or_alias(tenant_id, name)

    async def _preload_members(self, tenant_id: TenantId, rows: Sequence[SourceRow]) -> None:
        wanted: dict[str, set[str]] = {}
        for row in rows:
            client = self._resolved_client_from_cache(row)
            if client is None or not row.raw_member_ref:
                continue
            wanted.setdefault(client.id.value, set()).add(row.raw_member_ref)
        for client_id, refs in wanted.items():
            found = await self._members.find_by_employer_member_ids(
                tenant_id, ClientId(client_id), sorted(refs)
            )
            for ref in refs:
                self._member_cache.setdefault((client_id, ref), found.get(ref))

    async def _preload_services(self, tenant_id: TenantId, rows: Sequence[SourceRow]) -> None:
        names = set()
        for row in rows:
            canonical = map_intervention(row.raw_intervention)
            if canonical is not None and not isinstance(canonical, Unmapped):
                names.add(canonical)
        for name in names:
            self._service_cache.setdefault(name, await self._services.get_by_name(tenant_id, name))

    async def stage_row(
        self,
        tenant_id: TenantId,
        source_system: str,
        file_hash: str,
        row: SourceRow,
        *,
        now: datetime,
    ) -> StagedRow:
        replay_key = _replay_key(row, file_hash)
        existing = await self._live_row_holding(tenant_id, replay_key)
        if existing is not None:
            # The earlier row holds the key. This one records that the source
            # row was seen again, and defers rather than claiming it twice.
            return self._staged(
                row,
                ImportRowOutcome.DUPLICATE,
                DeliveryContext.UNKNOWN,
                None,
                None,
                (
                    f"Already staged as row {existing.row_number} of batch {existing.batch_id.value}",
                ),
                deferred_key(DUPLICATE_PREFIX, existing.batch_id.value, replay_key),
            )

        if row.session_date is None:
            return self._held(
                row, ImportRowOutcome.REJECTED, ("Source row has no date",), replay_key
            )
        if row.session_date > boundary_day(now):
            return self._held(
                row,
                ImportRowOutcome.REJECTED,
                (
                    f"Session date {row.session_date.isoformat()} is in the future; "
                    "the historical path cannot create a booking",
                ),
                replay_key,
            )

        resolution = await self._aliases.resolve(
            tenant_id, source_system, row.raw_practitioner_name
        )
        if not resolution.is_resolved:
            return self._held(
                row, _NAME_OUTCOMES[resolution.outcome], resolution.reasons, replay_key
            )

        subject = await self._resolve_subject(tenant_id, row)
        if subject.held is not None:
            outcome, reason = subject.held
            return self._held(row, outcome, (reason,), replay_key)

        return await self._with_delivery_context(
            tenant_id, row, resolution, replay_key, now=now, subject=subject
        )

    async def _resolve_subject(self, tenant_id: TenantId, row: SourceRow) -> "_Subject":
        """Resolve the client, the attendance, the member and the service.

        The order matters: the member is looked up within the resolved client,
        because Staff_ID is only unique per client. Each unresolved identity
        holds the row under its own outcome, so the right person fixes it; an
        unmapped optional value only leaves a note.
        """
        normalised, notes = _normalised(row)
        enrichment, enrichment_notes = await self._resolve_enrichment(tenant_id, row)
        normalised = replace(normalised, **enrichment)
        notes = notes + enrichment_notes

        client = await self._resolve_client(tenant_id, row)
        if client is None:
            return _Subject(
                held=(
                    ImportRowOutcome.UNRESOLVED_CLIENT,
                    _client_unresolved_reason(row),
                )
            )

        attendance = _attendance(row)
        member_id: str | None = None
        if attendance is SessionAttendance.INDIVIDUAL:
            if not row.raw_member_ref:
                return _Subject(
                    held=(
                        ImportRowOutcome.UNRESOLVED_MEMBER,
                        "Row names an individual but carries no member id; unresolved "
                        "identities stay staged rather than guessed",
                    )
                )
            member = await self._member_of(tenant_id, client.id, row.raw_member_ref)
            if member is None:
                return _Subject(
                    held=(
                        ImportRowOutcome.UNRESOLVED_MEMBER,
                        f"Member id {row.raw_member_ref!r} is not on {client.name}'s roster",
                    )
                )
            member_id = member.id.value

        canonical = map_intervention(row.raw_intervention)
        if canonical is None or isinstance(canonical, Unmapped):
            what = row.raw_intervention or "blank"
            return _Subject(
                held=(
                    ImportRowOutcome.UNRESOLVED_SERVICE,
                    f"Intervention {what!r} does not map to a catalogue service",
                )
            )
        service = await self._service_named(tenant_id, canonical)
        if service is None:
            return _Subject(
                held=(
                    ImportRowOutcome.UNRESOLVED_SERVICE,
                    f"No service named {canonical!r} in this tenant's catalogue",
                )
            )

        return _Subject(
            client_id=client.id.value,
            attendance=attendance,
            member_id=member_id,
            service_id=service.id.value,
            normalised=normalised,
            notes=notes,
        )

    async def _live_row_holding(
        self, tenant_id: TenantId, replay_key: str
    ) -> SessionImportRowEntity | None:
        if replay_key not in self._staged_by_key:
            self._staged_by_key[replay_key] = await self._imports.find_row_by_replay_key(
                tenant_id, replay_key
            )
        return self._staged_by_key[replay_key]

    async def _resolve_client(self, tenant_id: TenantId, row: SourceRow) -> ClientEntity | None:
        """Client Code first when the source carries one; company name is the fallback.

        A row can only be keyed one way, so a code takes priority over a name
        in the same row rather than requiring both to resolve.
        """
        if row.raw_client_code:
            if row.raw_client_code not in self._client_code_cache:
                self._client_code_cache[row.raw_client_code] = await self._clients.get_by_code(
                    tenant_id, row.raw_client_code
                )
            return self._client_code_cache[row.raw_client_code]
        if not row.raw_client_name:
            return None
        if row.raw_client_name not in self._client_cache:
            self._client_cache[row.raw_client_name] = await self._clients.get_by_name_or_alias(
                tenant_id, row.raw_client_name
            )
        return self._client_cache[row.raw_client_name]

    def _resolved_client_from_cache(self, row: SourceRow) -> ClientEntity | None:
        """A previously resolved client for this row, read-only, from `preload`'s caches."""
        if row.raw_client_code:
            return self._client_code_cache.get(row.raw_client_code)
        return self._client_cache.get(row.raw_client_name or "")

    async def _resolve_enrichment(
        self, tenant_id: TenantId, row: SourceRow
    ) -> tuple[dict[str, str | None], tuple[str, ...]]:
        """Diagnosis and approver: enrichment, never an identity the row waits on."""
        notes: list[str] = []
        fields: dict[str, str | None] = {"issue_topic": row.raw_issue_topic}

        diagnosis_type_id, diagnosis_id = None, None
        if row.raw_diagnosis:
            await self._preload_diagnosis_aliases()
            aliases = self._diagnosis_aliases or {}
            match = aliases.get(normalise_diagnosis_value(row.raw_diagnosis))
            if match is None:
                notes.append(f"Diagnosis {row.raw_diagnosis!r} has no alias and was left empty")
            else:
                diagnosis_type_id, diagnosis_id = match
        fields["diagnosis_type_id"] = diagnosis_type_id
        fields["diagnosis_id"] = diagnosis_id

        approved_by = None
        if row.raw_approved_by:
            await self._preload_approvers(tenant_id)
            by_name = self._approver_by_name or {}
            match = by_name.get(normalise_practitioner_name(row.raw_approved_by))
            if match is None:
                notes.append(f"Approver {row.raw_approved_by!r} does not match an active user")
            elif match is _AMBIGUOUS_APPROVER:
                notes.append(f"Approver {row.raw_approved_by!r} matches more than one active user")
            else:
                approved_by = match
        fields["approved_by"] = approved_by
        return fields, tuple(notes)

    async def _member_of(
        self, tenant_id: TenantId, client_id: ClientId, ref: str
    ) -> EligibleMember | None:
        key = (client_id.value, ref)
        if key not in self._member_cache:
            self._member_cache[key] = await self._members.find_by_employer_member_id(
                tenant_id, client_id, ref
            )
        return self._member_cache[key]

    async def _service_named(self, tenant_id: TenantId, name: str) -> ServiceEntity | None:
        if name not in self._service_cache:
            self._service_cache[name] = await self._services.get_by_name(tenant_id, name)
        return self._service_cache[name]

    async def _with_delivery_context(
        self,
        tenant_id: TenantId,
        row: SourceRow,
        resolution: NameResolution,
        replay_key: str,
        *,
        now: datetime,
        subject: "_Subject",
    ) -> StagedRow:
        """Organisation context needs a valid affiliation; otherwise stay unknown.

        Decision 2 forbids reading an absent organisation as direct delivery, so
        a row with no supplier evidence is staged as unknown rather than direct.
        """
        conflict = await self._same_looking_session(tenant_id, row, resolution, subject)
        if conflict is not None:
            return self._held(row, ImportRowOutcome.CONFLICTING, (conflict,), replay_key)
        if row.organisation_affiliation_id is None:
            return await self._from_organisation_column(
                tenant_id, row, resolution, replay_key, now=now, subject=subject
            )
        at = datetime.combine(row.session_date, datetime.min.time(), tzinfo=now.tzinfo)
        affiliation = await self._affiliations.get_valid_affiliation(
            tenant_id,
            ProviderAffiliationId(row.organisation_affiliation_id),
            provider_id=resolution.provider_id,
            at=at,
        )
        if affiliation is None:
            return self._held(
                row,
                ImportRowOutcome.CONFLICTING,
                (
                    f"Affiliation {row.organisation_affiliation_id} is not valid for this "
                    f"practitioner on {row.session_date.isoformat()}",
                ),
                replay_key,
            )
        return self._staged(
            row,
            ImportRowOutcome.ACCEPTED,
            DeliveryContext.ORGANISATION,
            resolution.provider_id,
            affiliation.id,
            subject.notes,
            replay_key,
            subject=subject,
        )

    async def _from_organisation_column(
        self,
        tenant_id: TenantId,
        row: SourceRow,
        resolution: NameResolution,
        replay_key: str,
        *,
        now: datetime,
        subject: "_Subject",
    ) -> StagedRow:
        """Read the workbook's Organisation Session answer.

        No names direct delivery, which the source states rather than the
        importer inferring, so decision 2 is untouched: a blank cell still
        stages as unknown. Yes must name one affiliation the practitioner
        actually held that day, because the apply path rejects organisation
        delivery without one; zero or several is a question for a person.
        """
        answer = _organisation_session(row.raw_organisation_session)
        if answer is None:
            notes = subject.notes
            if row.raw_organisation_session:
                notes = notes + (
                    f"Organisation Session {row.raw_organisation_session!r} is not Yes or No; "
                    "staged as unknown delivery",
                )
            return self._accepted(
                row, DeliveryContext.UNKNOWN, resolution, None, notes, replay_key, subject
            )
        if not answer:
            return self._accepted(
                row, DeliveryContext.DIRECT, resolution, None, subject.notes, replay_key, subject
            )

        affiliations, _ = await self._affiliations.list_affiliations(
            tenant_id,
            provider_id=resolution.provider_id,
            valid_at=row.session_date,
            limit=2,
        )
        if not affiliations:
            return self._held(
                row,
                ImportRowOutcome.CONFLICTING,
                (
                    "Row says the session was delivered under an organisation, but this "
                    f"practitioner held no affiliation on {row.session_date.isoformat()}",
                ),
                replay_key,
            )
        if len(affiliations) > 1:
            return self._held(
                row,
                ImportRowOutcome.CONFLICTING,
                (
                    "Row says the session was delivered under an organisation, but this "
                    f"practitioner held {len(affiliations)} on "
                    f"{row.session_date.isoformat()}; which one is a decision for a person",
                ),
                replay_key,
            )
        return self._accepted(
            row,
            DeliveryContext.ORGANISATION,
            resolution,
            affiliations[0].id,
            subject.notes,
            replay_key,
            subject,
        )

    def _accepted(
        self,
        row: SourceRow,
        context: DeliveryContext,
        resolution: NameResolution,
        affiliation_id: ProviderAffiliationId | None,
        notes: tuple[str, ...],
        replay_key: str,
        subject: "_Subject",
    ) -> StagedRow:
        return self._staged(
            row,
            ImportRowOutcome.ACCEPTED,
            context,
            resolution.provider_id,
            affiliation_id,
            notes,
            replay_key,
            subject=subject,
        )

    def _held(
        self,
        row: SourceRow,
        outcome: ImportRowOutcome,
        reasons: tuple[str, ...],
        replay_key: str,
    ) -> StagedRow:
        return self._staged(row, outcome, DeliveryContext.UNKNOWN, None, None, reasons, replay_key)

    async def _same_looking_session(
        self,
        tenant_id: TenantId,
        row: SourceRow,
        resolution: NameResolution,
        subject: "_Subject",
    ) -> str | None:
        """Flags a row that looks like it names an already-imported session.

        Only runs for a batch keyed by `file:{hash}:row:{n}`, because that key
        is a function of the file's bytes: any edit to the source between
        staging passes, even one unrelated to this row, changes every row's
        replay key and defeats the ordinary duplicate check above entirely. A
        source-keyed batch's key survives a file edit, so it does not need
        this. See "Tenth defect" / the session import stress-test findings in
        docs/reviews/SESSIONS_REVIEW.md for the scenario this closes.

        Matches on date, practitioner, client, service and member: the finest
        grain this extract's columns support, since it carries no
        time-of-day. Two genuinely distinct sessions can share all of these
        on the same day, so this holds the row for a person to confirm rather
        than silently calling it a duplicate or silently importing it twice.
        This is an adopted policy, not a verified one: the product owner
        should confirm the match grain is right once real re-staged data
        exercises it.
        """
        if row.source_record_key or resolution.provider_id is None or row.session_date is None:
            return None
        if subject.client_id is None or subject.service_id is None:
            return None
        existing = await self._imports.find_imported_row_matching(
            tenant_id,
            session_date=row.session_date,
            provider_id=resolution.provider_id,
            client_id=subject.client_id,
            service_id=subject.service_id,
            member_id=subject.member_id,
        )
        if existing is None:
            return None
        return (
            f"Same date, practitioner, client and service as an already-imported session "
            f"from batch {existing.batch_id.value} row {existing.row_number}. Confirm this is "
            "a separate session, not the same one restaged under a different file hash."
        )

    def _staged(
        self,
        row: SourceRow,
        outcome: ImportRowOutcome,
        context: DeliveryContext,
        provider_id: object | None,
        affiliation_id: ProviderAffiliationId | None,
        reasons: tuple[str, ...],
        replay_key: str,
        subject: "_Subject | None" = None,
    ) -> StagedRow:
        accepted = outcome is ImportRowOutcome.ACCEPTED
        resolved = subject if (accepted and subject is not None) else _Subject()
        return StagedRow(
            row_number=row.row_number,
            outcome=outcome,
            delivery_context=context,
            provider_id=provider_id,
            provider_affiliation_id=affiliation_id,
            member_id=resolved.member_id,
            service_id=resolved.service_id,
            client_id=resolved.client_id,
            attendance=resolved.attendance,
            normalised=resolved.normalised,
            reasons=reasons,
            replay_key=replay_key,
            source_record_key=row.source_record_key,
            raw_practitioner_name=row.raw_practitioner_name,
            session_date=row.session_date,
        )


def _client_unresolved_reason(row: SourceRow) -> str:
    if row.raw_client_code:
        return f"Client code {row.raw_client_code!r} does not resolve to a client in this tenant"
    return f"Company {row.raw_client_name!r} does not resolve to a client by name or alias"


def _attendance(row: SourceRow) -> SessionAttendance:
    """Company-wide when either signal says so; a member row otherwise.

    The extract marks a room-of-people session two ways: an audience column
    saying Group/Event, and Group standing where a gender would be. Either is
    sufficient, and neither is ever read as a gender.
    """
    if (row.raw_audience or "").strip().casefold() == "group/event":
        return SessionAttendance.COMPANY_WIDE
    if classify_gender(row.raw_gender) is SessionAttendance.COMPANY_WIDE:
        return SessionAttendance.COMPANY_WIDE
    return SessionAttendance.INDIVIDUAL


@dataclass(frozen=True)
class _Subject:
    """Who and what a row resolved to, or why it is held."""

    client_id: str | None = None
    attendance: SessionAttendance | None = None
    member_id: str | None = None
    service_id: str | None = None
    normalised: Normalised = Normalised()
    notes: tuple[str, ...] = ()
    held: tuple[ImportRowOutcome, str] | None = None


def _int_or_none(raw: str | None) -> int | None:
    if raw is None:
        return None
    digits = raw.replace(",", "").strip()
    return int(digits) if digits.isdigit() else None


def _normalised(row: SourceRow) -> tuple[Normalised, tuple[str, ...]]:
    """Map the activity-log columns, noting anything the tables do not list.

    Unmapped optional values do not hold a row; identity problems do. The note
    keeps the operator able to see what was dropped, per the no-silent-caps
    rule.
    """
    notes: list[str] = []

    def keep[T](value: T | Unmapped | None) -> T | None:
        if isinstance(value, Unmapped):
            notes.append(f"{value.column} value {value.value!r} has no mapping and was left empty")
            return None
        return value

    status = map_status(row.raw_status)
    status_note = keep(status)
    return (
        Normalised(
            session_type=keep(map_session_type(row.raw_session_type)),
            category=keep(map_category(row.raw_category)),
            clinical_status=status_note.clinical_status if status_note else None,
            session_status=status_note.session_status if status_note else None,
            client_type=keep(map_client_type(row.raw_client_type)),
            rate_ugx=_int_or_none(row.raw_rate),
            session_number=_int_or_none(row.raw_session_number),
        ),
        tuple(notes),
    )


_ROW_SIGNATURE_FIELDS = (
    "row_number",
    "raw_practitioner_name",
    "source_record_key",
    "raw_client_name",
    "raw_client_code",
    "raw_member_ref",
    "raw_gender",
    "raw_audience",
    "raw_session_type",
    "raw_category",
    "raw_status",
    "raw_intervention",
    "raw_client_type",
    "raw_rate",
    "raw_session_number",
    "raw_issue_topic",
    "raw_diagnosis",
    "raw_diagnosis_type",
    "raw_approved_by",
    "raw_organisation_session",
)


def canonical_content_hash(rows: Sequence[SourceRow]) -> str:
    """A hash of what a file says, not the bytes it happens to be encoded as.

    An Excel workbook re-saved with no cell actually changed can still differ
    byte for byte (Excel rewrites its own internal metadata on every save),
    and a CSV re-saved with different line endings does too. Hashing the
    parsed rows instead means only a real content change produces a new hash,
    which is what "restaging the same file" and the file-hash replay key
    fallback both actually mean to guarantee.
    """
    body = "\n".join(_row_signature(row) for row in rows)
    return "sha256:" + hashlib.sha256(body.encode("utf-8")).hexdigest()


def _row_signature(row: SourceRow) -> str:
    session_date = row.session_date.isoformat() if row.session_date else None
    values = (session_date, *(getattr(row, field) for field in _ROW_SIGNATURE_FIELDS))
    return "\x1f".join("" if value is None else str(value) for value in values)


def _replay_key(row: SourceRow, file_hash: str) -> str:
    if row.source_record_key:
        return f"key:{row.source_record_key}"
    return f"file:{file_hash}:row:{row.row_number}"


def replay_key_strategy(source_record_key_field: str | None) -> str:
    """Which replay key form a batch is keyed by.

    The batch records the column it was keyed on, or nothing, so a later
    reconciliation reading a stored batch can name the strategy without the
    file. `SessionImportBatchModel.source_record_key_field` is that record.
    """
    return SOURCE_KEY_STRATEGY if source_record_key_field else FILE_ROW_KEY_STRATEGY


def preflight_source_keys(rows: Sequence[SourceRow], source_record_key_field: str | None) -> str:
    """Check a nominated key column over the whole file and name the strategy.

    Runs before any row is staged. A repeated key makes `_replay_key` collide,
    and the second row is staged as Duplicate and lost without a rejection an
    operator would think to look at.
    """
    if source_record_key_field:
        _refuse_unusable_key(rows, source_record_key_field)
    return replay_key_strategy(source_record_key_field)


def _refuse_unusable_key(rows: Sequence[SourceRow], column: str) -> None:
    """Uniqueness and completeness are both required, because a blank fails open.

    A row with no key falls back to `file:{hash}:row:{n}` while its neighbours
    use `key:{...}`, leaving one batch keyed two ways: a re-export under a new
    hash then restages exactly those rows and returns the rest as duplicates.
    """
    collisions = _colliding_keys(rows)
    blanks = tuple(row.row_number for row in rows if not row.source_record_key)
    if not collisions and not blanks:
        return
    raise DomainError(
        _preflight_message(column, collisions, blanks),
        error_code="IMPORT_SOURCE_KEY_NOT_UNIQUE",
        http_status=422,
        details={"source_record_key_field": column},
    )


def _colliding_keys(rows: Sequence[SourceRow]) -> tuple[tuple[str, tuple[int, ...]], ...]:
    grouped: dict[str, list[int]] = defaultdict(list)
    for row in rows:
        if row.source_record_key:
            grouped[row.source_record_key].append(row.row_number)
    return tuple((key, tuple(numbers)) for key, numbers in grouped.items() if len(numbers) > 1)


def _preflight_message(
    column: str,
    collisions: tuple[tuple[str, tuple[int, ...]], ...],
    blanks: tuple[int, ...],
) -> str:
    parts = [f"Column {column!r} cannot be the source record key."]
    if collisions:
        affected = sum(len(numbers) for _, numbers in collisions)
        parts.append(
            f"Repeated values: {len(collisions)} across {affected} rows, "
            f"for example {_collision_sample(collisions)}."
        )
    if blanks:
        parts.append(f"Rows with no value: {len(blanks)}, for example {_row_sample(blanks)}.")
    return " ".join(parts)


def _collision_sample(collisions: tuple[tuple[str, tuple[int, ...]], ...]) -> str:
    return "; ".join(
        f"{key!r} on rows {_row_sample(numbers)}" for key, numbers in collisions[:_SAMPLE_SIZE]
    )


def _row_sample(numbers: tuple[int, ...]) -> str:
    return ", ".join(str(number) for number in numbers[:_SAMPLE_SIZE])


def new_row_id() -> SessionImportRowId:
    return SessionImportRowId(generate_cuid())


def new_batch_id() -> SessionImportBatchId:
    return SessionImportBatchId(generate_cuid())
