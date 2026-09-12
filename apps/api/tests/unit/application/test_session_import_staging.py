"""Staging outcomes: separate name failures, no future bookings, replay safety."""

from datetime import UTC, date, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.application.services.session_import_staging import (
    FILE_ROW_KEY_STRATEGY,
    SOURCE_KEY_STRATEGY,
    NameOutcome,
    NameResolution,
    SessionImportStagingService,
    SourceRow,
    preflight_source_keys,
    replay_key_strategy,
)
from app.domain.entities.provider_affiliation import ProviderAffiliationEntity
from app.domain.entities.session_import import SessionImportBatchEntity
from app.domain.enums import (
    ClientType,
    SessionAttendance,
    SessionCategory,
    SessionClinicalStatus,
    SessionStatus,
    SessionType,
)
from app.domain.enums.provider_network import DeliveryContext, ImportRowOutcome
from app.domain.exceptions import DomainError
from app.domain.value_objects.core import (
    ClientId,
    EligibleMemberId,
    ProviderId,
    ServiceId,
    TenantId,
    UserId,
)
from app.domain.value_objects.provider_network import (
    ProviderAffiliationId,
    ProviderOrganisationId,
    SessionImportBatchId,
)

TENANT = TenantId("t-1")
SOURCE = "sessions-csv"
HASH = "sha256:abc"
NOW = datetime(2026, 9, 6, 12, 0, tzinfo=UTC)
PROV = ProviderId("prov-1")


def _service(
    *,
    resolution=None,
    affiliation=None,
    existing_row=None,
    member="default",
    affiliations_on_date=(),
    practitioners=None,
):
    """A staging service whose directory holds one practitioner by default.

    `practitioners` names the directory the matcher sees; `resolution` is the
    older lever and now seeds that directory so the existing cases still read
    as "this name resolves / does not resolve".
    """
    providers = AsyncMock()
    providers.list_for_tenant.return_value = _directory(practitioners, resolution)
    affiliations = AsyncMock()
    affiliations.get_valid_affiliation.return_value = affiliation
    affiliations.list_affiliations.return_value = (
        tuple(affiliations_on_date),
        len(affiliations_on_date),
    )
    imports = AsyncMock()
    imports.find_row_by_replay_key.return_value = existing_row
    imports.find_rows_by_replay_keys.return_value = {}
    imports.find_imported_row_matching.return_value = None
    clients = AsyncMock()
    clients.get_by_name_or_alias.return_value = SimpleNamespace(
        id=ClientId("cli-1"), name="Stanbic Bank", tenant_id=TENANT
    )
    members = AsyncMock()
    resolved = SimpleNamespace(id=EligibleMemberId("mem-1")) if member == "default" else member
    members.find_by_employer_member_id.return_value = resolved
    # The batch lookup answers the same thing the singular one does, keyed by
    # the member reference the rows carry.
    members.find_by_employer_member_ids.return_value = {"HR-1": resolved} if resolved else {}
    services = AsyncMock()
    services.get_by_name.return_value = SimpleNamespace(id=ServiceId("svc-1"))
    diagnoses = AsyncMock()
    diagnoses.alias_lookup.return_value = {}
    users = AsyncMock()
    users.list_all.return_value = []
    return (
        SessionImportStagingService(
            providers, affiliations, imports, clients, members, services, diagnoses, users
        ),
        imports,
    )


def _practitioner(provider_id: str, display_name: str):
    return SimpleNamespace(id=ProviderId(provider_id), display_name=display_name)


def _directory(practitioners, resolution):
    """Translate the older `resolution` lever into a directory of practitioners.

    A resolution that is anything but RESOLVED means the name matches nobody,
    which is now an empty directory rather than an absent alias.
    """
    if practitioners is not None:
        return list(practitioners)
    if resolution is None or resolution.outcome is NameOutcome.RESOLVED:
        return [_practitioner(PROV.value, "Dr Alice Nakato")]
    return []


def _row(**overrides) -> SourceRow:
    defaults = {
        "row_number": 1,
        "raw_practitioner_name": "Dr Alice Nakato",
        "session_date": date(2025, 4, 2),
        "raw_client_name": "Stanbic",
        "raw_member_ref": "HR-1",
        "raw_intervention": "Individual Counselling",
    }
    return SourceRow(**{**defaults, **overrides})


async def _stage(service, row):
    return await service.stage_row(TENANT, SOURCE, HASH, row, now=NOW)


class TestHistoricalAcceptance:
    async def test_a_past_session_for_a_resolved_practitioner_is_accepted(self):
        """Eligibility today is irrelevant: the delivery already happened."""
        service, _ = _service()
        staged = await _stage(service, _row())
        assert staged.outcome is ImportRowOutcome.ACCEPTED
        assert staged.provider_id == PROV

    async def test_no_supplier_evidence_stays_unknown_not_direct(self):
        """Decision 2 forbids reading an empty organisation column as direct."""
        service, _ = _service()
        staged = await _stage(service, _row())
        assert staged.delivery_context is DeliveryContext.UNKNOWN
        assert staged.provider_affiliation_id is None

    async def test_a_future_dated_row_is_rejected(self):
        service, _ = _service()
        staged = await _stage(service, _row(session_date=date(2027, 1, 1)))
        assert staged.outcome is ImportRowOutcome.REJECTED
        assert "cannot create a booking" in staged.reasons[0]

    async def test_the_import_day_itself_is_accepted(self):
        """Boundary: the day the import runs is history, not a future booking."""
        service, _ = _service()
        staged = await _stage(service, _row(session_date=date(2026, 9, 6)))
        assert staged.outcome is ImportRowOutcome.ACCEPTED

    async def test_a_row_with_no_date_is_rejected(self):
        service, _ = _service()
        staged = await _stage(service, _row(session_date=None))
        assert staged.outcome is ImportRowOutcome.REJECTED
        assert staged.reasons


class TestUnresolvedSubjects:
    """The write path needs a member and a service; staging cannot invent either.

    Member identity belongs to the members migration and service identity to
    the catalogue, so an unresolved one is quarantined with a reason rather
    than guessed. Two outcomes, because different people resolve them.
    """

    async def test_a_row_without_a_member_ref_is_not_accepted(self):
        service, _ = _service()
        staged = await _stage(service, _row(raw_member_ref=None))
        assert staged.outcome is ImportRowOutcome.UNRESOLVED_MEMBER
        assert "no member id" in staged.reasons[0]

    async def test_a_member_ref_not_on_the_roster_is_not_accepted(self):
        service, _ = _service(member=None)
        staged = await _stage(service, _row(raw_member_ref="HR-404"))
        assert staged.outcome is ImportRowOutcome.UNRESOLVED_MEMBER
        assert "not on Stanbic Bank's roster" in staged.reasons[0]

    async def test_an_unmapped_intervention_is_not_accepted(self):
        service, _ = _service()
        staged = await _stage(service, _row(raw_intervention="No show"))
        assert staged.outcome is ImportRowOutcome.UNRESOLVED_SERVICE
        assert "does not map" in staged.reasons[0]

    async def test_the_two_are_distinct_outcomes(self):
        service, _ = _service()
        no_member = await _stage(service, _row(raw_member_ref=None))
        no_service = await _stage(service, _row(raw_intervention=None))
        assert no_member.outcome is not no_service.outcome

    async def test_an_unresolved_row_carries_no_member_or_service(self):
        service, _ = _service()
        staged = await _stage(service, _row(raw_member_ref=None))
        assert (staged.member_id, staged.service_id) == (None, None)

    async def test_an_accepted_row_carries_both(self):
        service, _ = _service()
        staged = await _stage(service, _row())
        assert (staged.member_id, staged.service_id) == ("mem-1", "svc-1")

    async def test_the_practitioner_is_resolved_before_the_subject_check(self):
        """An unmapped name is reported as such, not masked by a missing member."""
        service, _ = _service(
            resolution=NameResolution(outcome=NameOutcome.UNMAPPED, reasons=("no mapping",))
        )
        staged = await _stage(service, _row(raw_member_ref=None))
        assert staged.outcome is ImportRowOutcome.UNMAPPED_PRACTITIONER


class TestNameOutcomesStaySeparate:
    """Each way a name can fail keeps its own outcome, so the fix is obvious.

    `Rejected` is no longer reachable from the name: it described an alias a
    person had ruled out, and there are no aliases. A name either matches one
    practitioner, none, or several.
    """

    async def test_a_name_matching_nobody_is_unmapped(self):
        service, _ = _service(practitioners=[])
        staged = await _stage(service, _row())
        assert staged.outcome is ImportRowOutcome.UNMAPPED_PRACTITIONER
        assert staged.provider_id is None

    async def test_a_name_matching_several_practitioners_is_ambiguous(self):
        service, _ = _service(
            practitioners=[
                _practitioner("prov-1", "Alice Nakato"),
                _practitioner("prov-2", "Dr Alice Nakato"),
            ]
        )
        staged = await _stage(service, _row())
        assert staged.outcome is ImportRowOutcome.AMBIGUOUS_PRACTITIONER
        assert staged.provider_id is None

    async def test_a_row_naming_nobody_is_missing_not_unmapped(self):
        service, _ = _service()
        staged = await _stage(service, _row(raw_practitioner_name=None))
        assert staged.outcome is ImportRowOutcome.MISSING_PRACTITIONER

    async def test_an_unmapped_row_says_what_would_fix_it(self):
        service, _ = _service(practitioners=[])
        staged = await _stage(service, _row())
        assert "Add them, then stage the file again" in staged.reasons[0]

    async def test_the_same_practitioner_listed_twice_is_not_ambiguous(self):
        """Paging returns each practitioner once, but the guard is on identity."""
        service, _ = _service(
            practitioners=[
                _practitioner("prov-1", "Alice Nakato"),
                _practitioner("prov-1", "Dr. Alice Nakato"),
            ]
        )
        staged = await _stage(service, _row())
        assert staged.outcome is ImportRowOutcome.ACCEPTED

    async def test_no_practitioner_is_invented_for_an_unmapped_name(self):
        service, _ = _service(
            resolution=NameResolution(outcome=NameOutcome.UNMAPPED, reasons=("no mapping",))
        )
        staged = await _stage(service, _row())
        assert staged.provider_id is None
        assert staged.outcome is ImportRowOutcome.UNMAPPED_PRACTITIONER


class TestOrganisationContext:
    def _affiliation(self):
        return ProviderAffiliationEntity(
            id=ProviderAffiliationId("aff-1"),
            tenant_id=TENANT,
            provider_id=PROV,
            organisation_id=ProviderOrganisationId("org-1"),
            valid_from=date(2025, 1, 1),
            valid_until=None,
            created_at=NOW,
            updated_at=NOW,
        )

    async def test_a_valid_affiliation_gives_organisation_context(self):
        service, _ = _service(affiliation=self._affiliation())
        staged = await _stage(service, _row(organisation_affiliation_id="aff-1"))
        assert staged.outcome is ImportRowOutcome.ACCEPTED
        assert staged.delivery_context is DeliveryContext.ORGANISATION
        assert staged.provider_affiliation_id == ProviderAffiliationId("aff-1")

    async def test_an_affiliation_invalid_at_the_session_date_conflicts(self):
        """Not accepted as unknown: the source asserted a firm that does not hold."""
        service, _ = _service(affiliation=None)
        staged = await _stage(service, _row(organisation_affiliation_id="aff-1"))
        assert staged.outcome is ImportRowOutcome.CONFLICTING
        assert "not valid for this practitioner" in staged.reasons[0]

    async def test_the_affiliation_is_checked_at_the_session_date_not_today(self):
        service, _ = _service(affiliation=self._affiliation())
        affiliations = service._affiliations
        await _stage(
            service, _row(session_date=date(2025, 4, 2), organisation_affiliation_id="aff-1")
        )
        _, kwargs = affiliations.get_valid_affiliation.call_args
        assert kwargs["at"].date() == date(2025, 4, 2)


class TestOrganisationSessionColumn:
    """The workbook's Yes/No answer, and what a blank one may not be read as."""

    def _affiliation(self, affiliation_id="aff-1"):
        return ProviderAffiliationEntity(
            id=ProviderAffiliationId(affiliation_id),
            tenant_id=TENANT,
            provider_id=PROV,
            organisation_id=ProviderOrganisationId("org-1"),
            valid_from=date(2025, 1, 1),
            valid_until=None,
            created_at=NOW,
            updated_at=NOW,
        )

    async def test_yes_links_the_affiliation_the_practitioner_held_that_day(self):
        service, _ = _service(affiliations_on_date=[self._affiliation()])
        staged = await _stage(service, _row(raw_organisation_session="Yes"))
        assert staged.outcome is ImportRowOutcome.ACCEPTED
        assert staged.delivery_context is DeliveryContext.ORGANISATION
        assert staged.provider_affiliation_id == ProviderAffiliationId("aff-1")

    async def test_the_affiliation_is_looked_up_at_the_session_date(self):
        service, _ = _service(affiliations_on_date=[self._affiliation()])
        await _stage(service, _row(session_date=date(2025, 4, 2), raw_organisation_session="Yes"))
        _, kwargs = service._affiliations.list_affiliations.call_args
        assert kwargs["valid_at"] == date(2025, 4, 2)
        assert kwargs["provider_id"] == PROV

    async def test_no_states_direct_delivery_rather_than_leaving_it_unknown(self):
        service, _ = _service()
        staged = await _stage(service, _row(raw_organisation_session="No"))
        assert staged.outcome is ImportRowOutcome.ACCEPTED
        assert staged.delivery_context is DeliveryContext.DIRECT
        assert staged.provider_affiliation_id is None

    async def test_a_blank_column_stays_unknown_and_is_never_read_as_direct(self):
        """Decision 2: an absent answer is missing evidence, not a statement."""
        service, _ = _service()
        staged = await _stage(service, _row(raw_organisation_session=None))
        assert staged.outcome is ImportRowOutcome.ACCEPTED
        assert staged.delivery_context is DeliveryContext.UNKNOWN

    async def test_yes_with_no_affiliation_that_day_is_a_conflict_not_an_accept(self):
        """The apply path rejects organisation delivery carrying no affiliation."""
        service, _ = _service(affiliations_on_date=[])
        staged = await _stage(service, _row(raw_organisation_session="Yes"))
        assert staged.outcome is ImportRowOutcome.CONFLICTING
        assert "held no affiliation" in staged.reasons[0]

    async def test_yes_with_several_affiliations_is_a_question_for_a_person(self):
        service, _ = _service(
            affiliations_on_date=[self._affiliation("aff-1"), self._affiliation("aff-2")]
        )
        staged = await _stage(service, _row(raw_organisation_session="Yes"))
        assert staged.outcome is ImportRowOutcome.CONFLICTING
        assert "decision for a person" in staged.reasons[0]

    async def test_an_unrecognised_answer_stays_unknown_and_says_so(self):
        service, _ = _service()
        staged = await _stage(service, _row(raw_organisation_session="maybe"))
        assert staged.outcome is ImportRowOutcome.ACCEPTED
        assert staged.delivery_context is DeliveryContext.UNKNOWN
        assert any("is not Yes or No" in note for note in staged.reasons)

    async def test_an_explicit_affiliation_id_still_wins_over_the_column(self):
        """The older, precise path keeps working for files that carry an id."""
        service, _ = _service(affiliation=self._affiliation())
        staged = await _stage(
            service,
            _row(organisation_affiliation_id="aff-1", raw_organisation_session="No"),
        )
        assert staged.delivery_context is DeliveryContext.ORGANISATION


class TestReplay:
    async def test_a_row_already_staged_is_a_duplicate(self):
        existing = AsyncMock()
        existing.row_number = 7
        existing.batch_id = SessionImportBatchId("b-old")
        service, _ = _service(existing_row=existing)
        staged = await _stage(service, _row())
        assert staged.outcome is ImportRowOutcome.DUPLICATE
        assert "batch b-old" in staged.reasons[0]

    async def test_a_duplicate_defers_the_key_instead_of_claiming_it_again(self):
        """Exactly one row may hold a key, or the same source imports twice."""
        existing = AsyncMock()
        existing.row_number = 7
        existing.batch_id = SessionImportBatchId("b-old")
        service, _ = _service(existing_row=existing)
        staged = await _stage(service, _row(row_number=42))
        assert staged.replay_key == f"duplicate:b-old:file:{HASH}:row:42"
        assert staged.replay_key != f"file:{HASH}:row:42"

    async def test_the_replay_key_uses_file_hash_and_row_when_no_source_key(self):
        service, _ = _service()
        staged = await _stage(service, _row(row_number=42))
        assert staged.replay_key == f"file:{HASH}:row:42"

    async def test_a_stable_source_key_takes_precedence(self):
        service, _ = _service()
        staged = await _stage(service, _row(source_record_key="LOG-9"))
        assert staged.replay_key == "key:LOG-9"

    async def test_duplicate_detection_happens_before_any_resolution(self):
        """A replay must not re-run reconciliation or re-read affiliations."""
        existing = AsyncMock()
        existing.row_number = 1
        existing.batch_id = SessionImportBatchId("b-old")
        service, _ = _service(existing_row=existing)
        await _stage(service, _row())
        service._providers.list_for_tenant.assert_not_awaited()
        service._affiliations.get_valid_affiliation.assert_not_awaited()


class TestContentDuplicateAcrossFileHashes:
    """A row that looks like an already-imported session, restaged under a
    different file hash, must not silently write a second copy of it.

    The file-hash-row replay key is a function of the file's bytes: any edit
    to the source between staging passes changes every row's key and defeats
    the ordinary replay-key duplicate check in TestReplay above entirely.
    """

    async def test_a_row_matching_an_already_imported_one_is_held_as_conflicting(self):
        already_imported = AsyncMock()
        already_imported.row_number = 3
        already_imported.batch_id = SessionImportBatchId("b-old")
        service, imports = _service()
        imports.find_imported_row_matching.return_value = already_imported
        staged = await _stage(service, _row())
        assert staged.outcome is ImportRowOutcome.CONFLICTING
        assert "batch b-old row 3" in staged.reasons[0]

    async def test_a_source_keyed_row_never_runs_the_content_check(self):
        """A source key survives a file edit, so it does not need this guard."""
        service, imports = _service()
        await _stage(service, _row(source_record_key="LOG-9"))
        imports.find_imported_row_matching.assert_not_awaited()

    async def test_no_match_leaves_the_row_to_stage_normally(self):
        service, _ = _service()
        staged = await _stage(service, _row())
        assert staged.outcome is ImportRowOutcome.ACCEPTED

    async def test_the_match_is_scoped_by_client_service_provider_date_and_member(self):
        service, imports = _service()
        await _stage(service, _row())
        imports.find_imported_row_matching.assert_awaited_once_with(
            TENANT,
            session_date=date(2025, 4, 2),
            provider_id=PROV,
            client_id="cli-1",
            service_id="svc-1",
            member_id="mem-1",
        )


def _keyed_rows(*keys: str | None) -> list[SourceRow]:
    return [_row(row_number=number, source_record_key=key) for number, key in enumerate(keys, 1)]


class TestSourceKeyPreflight:
    """S-04: a nominated key column that is not unique destroys rows silently.

    In the reference extract `ACTIVITY LOG ID` holds 7,079 distinct values over
    7,465 non-empty rows. Nominated as the source key, the second and later row
    of each colliding group is staged as Duplicate and dropped, and no rejection
    is written for anyone to review. The preflight refuses the whole batch
    instead, before a single row is staged.
    """

    def test_a_repeated_key_refuses_the_batch(self):
        with pytest.raises(DomainError) as error:
            preflight_source_keys(_keyed_rows("LOG-1", "LOG-2", "LOG-1"), "ACTIVITY LOG ID")
        assert error.value.error_code == "IMPORT_SOURCE_KEY_NOT_UNIQUE"

    def test_the_refusal_names_the_column(self):
        with pytest.raises(DomainError) as error:
            preflight_source_keys(_keyed_rows("LOG-1", "LOG-1"), "ACTIVITY LOG ID")
        assert "ACTIVITY LOG ID" in error.value.message
        assert error.value.details["source_record_key_field"] == "ACTIVITY LOG ID"

    def test_the_refusal_samples_the_colliding_values_and_their_rows(self):
        """An operator has to see which values are wrong, not only that some are."""
        with pytest.raises(DomainError) as error:
            preflight_source_keys(_keyed_rows("LOG-1", "LOG-2", "LOG-1"), "ACTIVITY LOG ID")
        assert "'LOG-1' on rows 1, 3" in error.value.message

    def test_the_refusal_counts_the_repeats_and_the_rows_they_cost(self):
        rows = _keyed_rows("A", "A", "B", "B", "B", "C")
        with pytest.raises(DomainError) as error:
            preflight_source_keys(rows, "ACTIVITY LOG ID")
        assert "Repeated values: 2 across 5 rows" in error.value.message

    def test_a_collision_at_opposite_ends_of_the_file_is_found(self):
        """The check is over the whole file, not a neighbouring window."""
        rows = _keyed_rows("LOG-1", *[f"LOG-{n}" for n in range(2, 60)], "LOG-1")
        with pytest.raises(DomainError):
            preflight_source_keys(rows, "ACTIVITY LOG ID")

    def test_unique_keys_are_accepted(self):
        assert (
            preflight_source_keys(_keyed_rows("LOG-1", "LOG-2", "LOG-3"), "ACTIVITY LOG ID")
            == SOURCE_KEY_STRATEGY
        )

    def test_no_nominated_column_falls_back_to_the_file_and_row_key(self):
        assert preflight_source_keys(_keyed_rows(None, None), None) == FILE_ROW_KEY_STRATEGY

    def test_a_blank_key_refuses_the_batch(self):
        """Fails safe: a blank falls back to file-and-row and keys the batch twice.

        `ACTIVITY LOG ID` is empty on 5 of 7,470 rows, so uniqueness and
        completeness are different rules. Allowing the blanks through would
        stage one batch under two key forms, and a re-export under a new hash
        would then restage exactly those rows while the rest came back as
        duplicates.
        """
        with pytest.raises(DomainError) as error:
            preflight_source_keys(_keyed_rows("LOG-1", None, "LOG-3"), "ACTIVITY LOG ID")
        assert "Rows with no value: 1, for example 2" in error.value.message

    def test_blank_keys_are_not_reported_as_one_repeated_value(self):
        with pytest.raises(DomainError) as error:
            preflight_source_keys(_keyed_rows(None, None), "ACTIVITY LOG ID")
        assert "Repeated values" not in error.value.message
        assert "Rows with no value: 2" in error.value.message

    def test_both_faults_are_reported_together(self):
        """One upload tells the operator everything wrong with the column."""
        with pytest.raises(DomainError) as error:
            preflight_source_keys(_keyed_rows("LOG-1", "LOG-1", None), "ACTIVITY LOG ID")
        assert "Repeated values" in error.value.message
        assert "Rows with no value" in error.value.message

    def test_an_empty_file_is_accepted_when_no_column_was_nominated(self):
        assert preflight_source_keys([], None) == FILE_ROW_KEY_STRATEGY


class TestTheBatchRecordsHowItWasKeyed:
    """A later reconciliation has to be able to tell how a batch was keyed."""

    def _batch(self, key_field: str | None) -> SessionImportBatchEntity:
        return SessionImportBatchEntity(
            id=SessionImportBatchId("b-1"),
            tenant_id=TENANT,
            source_system=SOURCE,
            file_name="sessions.csv",
            file_hash=HASH,
            row_count=3,
            source_record_key_field=key_field,
            staged_by=UserId("u-1"),
            created_at=NOW,
            updated_at=NOW,
        )

    def test_the_file_hash_is_recorded(self):
        assert self._batch(None).file_hash == HASH

    def test_a_nominated_column_records_the_source_key_strategy(self):
        batch = self._batch("ACTIVITY LOG ID")
        assert replay_key_strategy(batch.source_record_key_field) == SOURCE_KEY_STRATEGY
        assert batch.uses_file_hash_replay_key is False

    def test_no_nominated_column_records_the_file_and_row_strategy(self):
        batch = self._batch(None)
        assert replay_key_strategy(batch.source_record_key_field) == FILE_ROW_KEY_STRATEGY
        assert batch.uses_file_hash_replay_key is True

    async def test_a_staged_row_is_keyed_the_way_the_batch_records(self):
        batch = self._batch(None)
        service, _ = _service()
        staged = await service.stage_row(
            TENANT, SOURCE, batch.file_hash, _row(row_number=9), now=NOW
        )
        assert replay_key_strategy(batch.source_record_key_field) == FILE_ROW_KEY_STRATEGY
        assert staged.replay_key == f"file:{batch.file_hash}:row:9"


class TestSubjectResolution:
    """A session belongs to a client, and staging resolves who it was for."""

    async def test_a_company_that_resolves_no_client_holds_the_row(self):
        service, _ = _service()
        service._clients.get_by_name_or_alias.return_value = None
        staged = await _stage(service, _row(raw_client_name="Unknown Ltd"))
        assert staged.outcome is ImportRowOutcome.UNRESOLVED_CLIENT
        assert "'Unknown Ltd'" in staged.reasons[0]

    async def test_a_group_event_row_is_company_wide_and_needs_no_member(self):
        """A health talk is delivered to the client, with nobody to name."""
        service, _ = _service(member=None)
        staged = await _stage(service, _row(raw_audience="Group/Event", raw_member_ref=None))
        assert staged.outcome is ImportRowOutcome.ACCEPTED
        assert staged.attendance is SessionAttendance.COMPANY_WIDE
        assert staged.member_id is None
        assert staged.client_id == "cli-1"

    async def test_group_standing_as_a_gender_means_company_wide_not_a_gender(self):
        service, _ = _service(member=None)
        staged = await _stage(service, _row(raw_gender="Group", raw_member_ref=None))
        assert staged.outcome is ImportRowOutcome.ACCEPTED
        assert staged.attendance is SessionAttendance.COMPANY_WIDE

    async def test_an_accepted_individual_row_carries_the_resolved_subject(self):
        service, _ = _service()
        staged = await _stage(service, _row())
        assert staged.client_id == "cli-1"
        assert staged.attendance is SessionAttendance.INDIVIDUAL
        assert (staged.member_id, staged.service_id) == ("mem-1", "svc-1")

    async def test_the_member_is_looked_up_within_the_resolved_client(self):
        """Staff_ID is only unique per client, so the client scopes the lookup."""
        service, _ = _service()
        await _stage(service, _row(raw_member_ref="HR-7"))
        args = service._members.find_by_employer_member_id.await_args.args
        assert args[1].value == "cli-1"
        assert args[2] == "HR-7"


class TestNormalisedValues:
    async def test_mapped_activity_log_values_ride_on_the_accepted_row(self):
        service, _ = _service()
        staged = await _stage(
            service,
            _row(
                raw_session_type="physical",
                raw_category="Group session",
                raw_status="Terminated",
                raw_client_type="Repeat",
                raw_rate=" 100,000 ",
                raw_session_number="3",
            ),
        )
        n = staged.normalised
        assert n.session_type is SessionType.PHYSICAL
        assert n.category is SessionCategory.GROUP
        assert n.clinical_status is SessionClinicalStatus.TERMINATED
        assert n.client_type is ClientType.REPEAT
        assert n.rate_ugx == 100000
        assert n.session_number == 3

    async def test_a_no_show_maps_to_the_scheduling_status_not_a_clinical_one(self):
        service, _ = _service()
        staged = await _stage(service, _row(raw_status="No Show"))
        assert staged.normalised.session_status is SessionStatus.NO_SHOW
        assert staged.normalised.clinical_status is None

    async def test_an_unmapped_optional_value_leaves_a_note_but_does_not_hold_the_row(self):
        service, _ = _service()
        staged = await _stage(service, _row(raw_category="Depression"))
        assert staged.outcome is ImportRowOutcome.ACCEPTED
        assert staged.normalised.category is None
        assert any("'Depression'" in reason for reason in staged.reasons)


class TestVisitInterventions:
    """The catalogue refuses Site/Hospital/Home Visit rows, so the mapper
    must not canonicalise onto them: the reason would invite recreating a
    banned service. What a visit row delivered is a review decision.
    """

    @pytest.mark.parametrize("spelling", ["site visit", "Hospital Visit", "Home Visit"])
    async def test_a_visit_row_is_held_as_unmapped_not_dead_ended(self, spelling):
        service, _ = _service()
        staged = await _stage(service, _row(raw_intervention=spelling))
        assert staged.outcome is ImportRowOutcome.UNRESOLVED_SERVICE
        assert "does not map" in staged.reasons[0]


class TestPreload:
    """A preloaded run must reach the same outcomes while asking far less."""

    async def test_preloaded_rows_reach_the_same_outcome_without_per_row_queries(self):
        service, imports = _service()
        imports.find_rows_by_replay_keys.return_value = {}
        rows = [_row(row_number=n) for n in range(1, 21)]

        await service.preload(TENANT, rows, HASH)
        staged = [await _stage(service, row) for row in rows]

        assert all(s.outcome is ImportRowOutcome.ACCEPTED for s in staged)
        imports.find_row_by_replay_key.assert_not_awaited()
        assert service._clients.get_by_name_or_alias.await_count == 1
        assert service._services.get_by_name.await_count == 1
        assert service._members.find_by_employer_member_ids.await_count == 1
        service._members.find_by_employer_member_id.assert_not_awaited()

    async def test_a_key_another_batch_already_holds_is_still_a_duplicate(self):
        service, imports = _service()
        held = SimpleNamespace(row_number=7, batch_id=SessionImportBatchId("b-earlier"))
        rows = [_row(row_number=1)]
        imports.find_rows_by_replay_keys.return_value = {f"file:{HASH}:row:1": held}

        await service.preload(TENANT, rows, HASH)
        staged = await _stage(service, rows[0])

        assert staged.outcome is ImportRowOutcome.DUPLICATE
        assert "row 7 of batch b-earlier" in staged.reasons[0]
        imports.find_row_by_replay_key.assert_not_awaited()

    async def test_a_member_the_batch_lookup_missed_still_holds_its_row(self):
        """A preload miss must read as unresolved, never as a resolved member."""
        service, imports = _service()
        imports.find_rows_by_replay_keys.return_value = {}
        service._members.find_by_employer_member_ids.return_value = {}
        rows = [_row(row_number=1)]

        await service.preload(TENANT, rows, HASH)
        staged = await _stage(service, rows[0])

        assert staged.outcome is ImportRowOutcome.UNRESOLVED_MEMBER
        assert staged.member_id is None

    async def test_staging_without_preload_still_resolves_every_row(self):
        """`preload` is an optimisation, not a precondition."""
        service, imports = _service()
        staged = await _stage(service, _row())
        assert staged.outcome is ImportRowOutcome.ACCEPTED
        imports.find_row_by_replay_key.assert_awaited_once()
