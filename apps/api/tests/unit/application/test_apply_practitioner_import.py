"""Applying a staged practitioner batch: creation, dedupe, isolation, audit."""

from contextlib import asynccontextmanager
from datetime import UTC, datetime

import pytest

from app.application.use_cases.apply_practitioner_import import (
    ApplyPractitionerImportUseCase,
)
from app.domain.entities.practitioner_import import (
    ImportReviewReason,
    PractitionerImportBatchEntity,
    PractitionerImportRowEntity,
)
from app.domain.entities.provider_organisation import ProviderOrganisationEntity
from app.domain.enums import AccreditationStatus, BaseStatus, PanelStatus
from app.domain.enums.provider_network import (
    ImportBatchStatus,
    ImportReasonCode,
    OrganisationApprovalStatus,
    PractitionerImportOutcome,
)
from app.domain.exceptions import DomainError, NotFoundError
from app.domain.services.provider_eligibility import evaluate_practitioner
from app.domain.services.provider_network_calendar import boundary_day
from app.domain.value_objects.core import TenantId, UserId
from app.domain.value_objects.provider_network import (
    PractitionerImportBatchId,
    PractitionerImportRowId,
    ProviderOrganisationId,
)

TENANT = TenantId("t-1")
ACTOR = UserId("u-1")
BATCH_ID = PractitionerImportBatchId("b-1")
NOW = datetime(2026, 9, 7, 12, 0, tzinfo=UTC)


def _batch(status=ImportBatchStatus.STAGED) -> PractitionerImportBatchEntity:
    return PractitionerImportBatchEntity(
        id=BATCH_ID,
        tenant_id=TENANT,
        source_system="practitioners-orgs-workbook",
        file_name="wb.xlsx",
        file_hash="sha256:abc",
        row_count=0,
        staged_by=ACTOR,
        created_at=NOW,
        updated_at=NOW,
        status=status,
    )


def _row(
    number: int,
    name: str,
    *,
    organisation: str | None = None,
    outcome: PractitionerImportOutcome = PractitionerImportOutcome.ACCEPTED,
    email: str | None = None,
    provenance: dict | None = None,
) -> PractitionerImportRowEntity:
    held = outcome in (
        PractitionerImportOutcome.NEEDS_REVIEW,
        PractitionerImportOutcome.REJECTED,
    )
    reason = ImportReviewReason(ImportReasonCode.DUPLICATE_NAME_CANDIDATE, "held for review")
    return PractitionerImportRowEntity(
        id=PractitionerImportRowId(f"r-{number}"),
        batch_id=BATCH_ID,
        tenant_id=TENANT,
        sheet_name="Minet EAP Partner list",
        row_number=number,
        raw_name=name,
        normalized_name=name.lower(),
        organisation_name=organisation,
        raw_profession="Clinical Psychologist",
        mapped_profession="Clinical Psychologist",
        contact_email=email,
        outcome=outcome,
        reasons=(reason,) if held else (),
        provenance=provenance or {},
        created_at=NOW,
    )


class FakeImports:
    def __init__(self, batch, rows):
        self.batch = batch
        self.rows = list(rows)
        self.saved_batches = []
        self.recorded = []

    async def get_batch(self, tenant_id, batch_id):
        if self.batch and self.batch.id.value == batch_id.value:
            return self.batch
        return None

    async def list_rows(self, tenant_id, batch_id, *, outcome=None, limit=50, offset=0):
        return self.rows[offset : offset + limit], len(self.rows)

    async def save_batch(self, batch):
        self.saved_batches.append(batch)

    async def record_row_apply(self, row):
        self.recorded.append(row)


class FakeProviders:
    def __init__(self, fail_for: str | None = None):
        self.saved = []
        self.fail_for = fail_for

    async def save(self, provider):
        if self.fail_for and provider.display_name == self.fail_for:
            raise RuntimeError("database refused this practitioner")
        self.saved.append(provider)


class FakeOrganisations:
    def __init__(self, existing=()):
        self.existing = list(existing)
        self.saved = []

    async def find_organisation_by_name(self, tenant_id, name):
        target = name.strip().lower()
        for organisation in self.existing + self.saved:
            if organisation.name.lower() == target:
                return organisation
        return None

    async def save_organisation(self, organisation):
        self.saved.append(organisation)


class FakeAffiliations:
    def __init__(self):
        self.saved = []

    async def save_affiliation(self, affiliation):
        self.saved.append(affiliation)


@asynccontextmanager
async def _savepoint():
    yield


class Harness:
    def __init__(self, rows, *, batch=None, existing_orgs=(), fail_for=None):
        self.imports = FakeImports(batch if batch is not None else _batch(), rows)
        self.providers = FakeProviders(fail_for=fail_for)
        self.organisations = FakeOrganisations(existing_orgs)
        self.affiliations = FakeAffiliations()
        self.audited = []

    async def execute(self):
        async def _audit(entity):
            self.audited.append((entity, tuple(type(e).__name__ for e in entity.events)))

        use_case = ApplyPractitionerImportUseCase(
            self.imports,
            self.providers,
            self.organisations,
            self.affiliations,
            savepoint=lambda: _savepoint(),
            audit=_audit,
        )
        return await use_case.execute(TENANT, BATCH_ID, ACTOR, now=NOW)


class TestBatchGuards:
    async def test_an_unknown_batch_is_not_found(self):
        harness = Harness([], batch=None)
        harness.imports.batch = None
        with pytest.raises(NotFoundError):
            await harness.execute()

    async def test_an_applied_batch_is_refused_with_a_conflict(self):
        harness = Harness([], batch=_batch(status=ImportBatchStatus.APPLIED))
        with pytest.raises(DomainError) as error:
            await harness.execute()
        assert error.value.http_status == 409

    async def test_zero_accepted_rows_applies_and_creates_nothing(self):
        rows = [
            _row(3, "Jane Doe", outcome=PractitionerImportOutcome.NEEDS_REVIEW),
            _row(4, "John Okello", outcome=PractitionerImportOutcome.DUPLICATE),
            _row(5, "Ann Achen", outcome=PractitionerImportOutcome.REJECTED),
        ]
        harness = Harness(rows)
        result = await harness.execute()
        assert result.created_providers == 0
        assert result.not_applicable == 3
        assert harness.providers.saved == []
        assert harness.organisations.saved == []
        assert harness.affiliations.saved == []
        assert harness.imports.batch.status is ImportBatchStatus.APPLIED


class TestCreation:
    async def test_the_reference_mix_creates_only_the_accepted_rows(self):
        """Mirror the reference workbook: 60 Accepted of 168 staged rows."""
        rows = [
            _row(n, f"Accepted Person {n}", organisation="ICFC" if n % 3 == 0 else None)
            for n in range(1, 61)
        ]
        rows += [
            _row(n, f"Held Person {n}", outcome=PractitionerImportOutcome.NEEDS_REVIEW)
            for n in range(61, 151)
        ]
        rows += [
            _row(n, f"Dup Person {n}", outcome=PractitionerImportOutcome.DUPLICATE)
            for n in range(151, 161)
        ]
        rows += [
            _row(n, f"Bad Row {n}", outcome=PractitionerImportOutcome.REJECTED)
            for n in range(161, 169)
        ]
        harness = Harness(rows)
        result = await harness.execute()
        assert result.created_providers == 60
        assert result.created_organisations == 1
        assert result.created_affiliations == 20
        assert result.not_applicable == 108
        assert result.failed == 0
        assert len(harness.providers.saved) == 60
        recorded = {r.raw_name for r in harness.imports.recorded}
        assert not any(name.startswith(("Held", "Dup", "Bad")) for name in recorded)

    async def test_created_practitioners_are_unbookable_and_pending(self):
        harness = Harness([_row(3, "Jane Doe", email="jane@example.com")])
        await harness.execute()
        provider = harness.providers.saved[0]
        assert provider.display_name == "Jane Doe"
        assert provider.contact_email == "jane@example.com"
        assert provider.status is BaseStatus.PENDING
        profile = provider.provider_profile
        assert profile.tier is None
        assert profile.region is None
        assert profile.panel_status is PanelStatus.PENDING
        assert profile.accreditation_status is AccreditationStatus.PENDING
        assert profile.gender is None
        assert profile.specialties == ()
        decision = evaluate_practitioner(provider, scheduled_at=NOW, now=NOW)
        assert not decision.eligible

    async def test_the_first_mobile_column_becomes_contact_phone(self):
        harness = Harness([_row(3, "Jane Doe", provenance={"CONTACT MOBILE 1": "0700000001"})])
        await harness.execute()
        assert harness.providers.saved[0].contact_phone == "0700000001"

    async def test_the_second_mobile_column_is_used_only_when_the_first_is_blank(self):
        harness = Harness([_row(3, "Jane Doe", provenance={"MOBILE CONTACT 2": "0700000002"})])
        await harness.execute()
        assert harness.providers.saved[0].contact_phone == "0700000002"

    async def test_the_two_mobile_columns_are_never_concatenated(self):
        harness = Harness(
            [
                _row(
                    3,
                    "Jane Doe",
                    provenance={
                        "CONTACT MOBILE 1": "0700000001",
                        "MOBILE CONTACT 2": "0700000002",
                    },
                )
            ]
        )
        await harness.execute()
        assert harness.providers.saved[0].contact_phone == "0700000001"

    async def test_no_mobile_column_leaves_contact_phone_unset(self):
        harness = Harness([_row(3, "Jane Doe")])
        await harness.execute()
        assert harness.providers.saved[0].contact_phone is None

    async def test_created_ids_are_recorded_on_the_row(self):
        harness = Harness([_row(3, "Jane Doe", organisation="Safe Places")])
        result = await harness.execute()
        row = harness.imports.recorded[0]
        assert row.imported_provider_id == harness.providers.saved[0].id.value
        assert row.imported_organisation_id == harness.organisations.saved[0].id.value
        assert row.imported_affiliation_id == harness.affiliations.saved[0].id.value
        assert result.rows[0].status == "applied"


class TestOrganisations:
    async def test_organisations_dedupe_within_the_batch_and_against_existing(self):
        existing = ProviderOrganisationEntity(
            id=ProviderOrganisationId("org-1"),
            tenant_id=TENANT,
            name="Minders",
            created_at=NOW,
            updated_at=NOW,
        )
        rows = [
            _row(3, "Jane Doe", organisation="ICFC"),
            _row(4, "John Okello", organisation="icfc"),
            _row(5, "Ann Achen", organisation="MINDERS"),
        ]
        harness = Harness(rows, existing_orgs=[existing])
        result = await harness.execute()
        assert result.created_organisations == 1
        assert result.reused_organisations == 1
        assert [o.name for o in harness.organisations.saved] == ["ICFC"]
        assert harness.affiliations.saved[2].organisation_id.value == "org-1"

    async def test_a_created_organisation_arrives_pending_approval(self):
        harness = Harness([_row(3, "Jane Doe", organisation="Safe Places")])
        await harness.execute()
        organisation = harness.organisations.saved[0]
        assert organisation.approval_status is OrganisationApprovalStatus.PENDING


class TestAffiliations:
    async def test_affiliation_valid_from_is_the_apply_day(self):
        harness = Harness([_row(3, "Jane Doe", organisation="Safe Places")])
        await harness.execute()
        affiliation = harness.affiliations.saved[0]
        assert affiliation.valid_from == boundary_day(NOW)
        assert affiliation.valid_until is None

    async def test_a_row_without_an_organisation_creates_no_affiliation(self):
        harness = Harness([_row(3, "Jane Doe")])
        result = await harness.execute()
        assert harness.affiliations.saved == []
        assert result.created_affiliations == 0


class TestIdempotencyAndIsolation:
    async def test_an_already_applied_row_is_skipped(self):
        row = _row(3, "Jane Doe")
        row.mark_applied("p-existing", None, None)
        harness = Harness([row])
        result = await harness.execute()
        assert result.skipped_already_applied == 1
        assert result.created_providers == 0
        assert harness.providers.saved == []
        assert result.rows[0].status == "skipped_already_applied"

    async def test_a_failing_row_is_quarantined_without_sinking_the_batch(self):
        rows = [_row(3, "Jane Doe"), _row(4, "Broken Person"), _row(5, "Ann Achen")]
        harness = Harness(rows, fail_for="Broken Person")
        result = await harness.execute()
        assert result.created_providers == 2
        assert result.failed == 1
        failed = next(r for r in harness.imports.recorded if r.raw_name == "Broken Person")
        assert failed.outcome is PractitionerImportOutcome.NEEDS_REVIEW
        assert any(
            reason.code is ImportReasonCode.APPLY_FAILED and "database refused" in reason.message
            for reason in failed.reasons
        )
        assert failed.imported_provider_id is None
        assert harness.imports.batch.status is ImportBatchStatus.APPLIED


class TestAudit:
    async def test_every_created_record_and_the_batch_are_audited_with_events(self):
        harness = Harness([_row(3, "Jane Doe", organisation="Safe Places")])
        await harness.execute()
        audited = {type(entity).__name__: events for entity, events in harness.audited if events}
        assert audited["ProviderOrganisationEntity"] == ("ProviderOrganisationCreated",)
        assert audited["ProviderEntity"] == ("ProviderCreated",)
        assert audited["ProviderAffiliationEntity"] == ("ProviderAffiliationCreated",)
        assert audited["PractitionerImportBatchEntity"] == ("PractitionerImportBatchApplied",)
