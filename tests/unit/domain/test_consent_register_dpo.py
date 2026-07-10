"""Consent + DataSharingRegister + DPOContact aggregate tests."""

from datetime import UTC, date, datetime, timedelta

import pytest

from app.domain.entities.consent import Consent
from app.domain.entities.data_sharing_register import DataSharingRegisterEntry
from app.domain.entities.dpo_contact import DPOContact
from app.domain.enums import (
    ConsentPurpose,
    ConsentScope,
    ConsentStatus,
)
from app.domain.events import (
    ConsentExpired,
    ConsentGranted,
    ConsentRequested,
    DataShareLogged,
)
from app.domain.exceptions import DomainError, InvalidStateError
from app.domain.value_objects.core import (
    ClinicalSubjectId,
    ConsentId,
    DataSharingRegisterEntryId,
    DocumentId,
    DPOContactId,
    Email,
    TenantId,
    UserId,
)


def _consent(**overrides) -> Consent:
    now = datetime.now(UTC)
    base = dict(
        id=ConsentId("c-1"),
        tenant_id=TenantId("t-1"),
        subject_clinical_subject_id=ClinicalSubjectId("cs_aaaaaaaa11111111"),
        scope=ConsentScope.DIAGNOSIS,
        purpose=ConsentPurpose.SPECIALIST_HANDOFF,
        disclosure_to="Specialist Dr. Mwangi",
        status=ConsentStatus.PENDING,
        requested_at=now,
        requested_by=UserId("clin-1"),
        created_at=now,
        updated_at=now,
    )
    base.update(overrides)
    return Consent(**base)


class TestConsentLifecycle:
    def test_creation_event(self):
        c = _consent()
        assert any(isinstance(e, ConsentRequested) for e in c.events)

    def test_disclosure_to_required(self):
        with pytest.raises(DomainError):
            _consent(disclosure_to="")

    def test_other_purpose_requires_detail(self):
        with pytest.raises(DomainError):
            _consent(
                purpose=ConsentPurpose.OTHER, purpose_other_detail=None
            )

    def test_grant_then_active(self):
        c = _consent()
        c.events.clear()
        c.grant(
            granted_by_subject_reference="signed_PDF_ref:001",
            signed_artifact_document_id=DocumentId("doc-1"),
        )
        assert c.status == ConsentStatus.ACTIVE
        assert c.is_active() is True
        assert any(isinstance(e, ConsentGranted) for e in c.events)

    def test_grant_requires_reference(self):
        c = _consent()
        with pytest.raises(DomainError, match="signature reference"):
            c.grant(granted_by_subject_reference="")

    def test_cannot_grant_twice(self):
        c = _consent()
        c.grant(granted_by_subject_reference="x")
        with pytest.raises(InvalidStateError):
            c.grant(granted_by_subject_reference="y")

    def test_revoke_requires_reason(self):
        c = _consent()
        c.grant(granted_by_subject_reference="x")
        with pytest.raises(DomainError):
            c.revoke(reason="")

    def test_revoke_idempotent(self):
        c = _consent()
        c.grant(granted_by_subject_reference="x")
        c.revoke(reason="withdrew consent")
        first = c.revoked_at
        c.revoke(reason="duplicate")
        assert c.revoked_at == first

    def test_expire_if_due_after_window(self):
        c = _consent()
        c.grant(granted_by_subject_reference="x")
        c.expires_on = date.today() - timedelta(days=1)
        flipped = c.expire_if_due()
        assert flipped is True
        assert c.status == ConsentStatus.EXPIRED
        assert any(isinstance(e, ConsentExpired) for e in c.events)


class TestDataSharingRegister:
    def test_basic_entry_emits_event(self):
        now = datetime.now(UTC)
        e = DataSharingRegisterEntry(
            id=DataSharingRegisterEntryId("d-1"),
            tenant_id=TenantId("t-1"),
            subject_clinical_subject_id=ClinicalSubjectId("cs_aaaaaaaa11111111"),
            shared_with="Dr. Mwangi",
            scope=ConsentScope.DIAGNOSIS,
            summary_of_data_shared="Diagnosis summary; no notes",
            shared_at=now,
            shared_by=UserId("clin-1"),
            created_at=now,
            consent_id=ConsentId("c-1"),
        )
        assert any(isinstance(ev, DataShareLogged) for ev in e.events)

    def test_no_consent_requires_legal_basis(self):
        now = datetime.now(UTC)
        with pytest.raises(DomainError, match="legal_basis"):
            DataSharingRegisterEntry(
                id=DataSharingRegisterEntryId("d-x"),
                tenant_id=TenantId("t-1"),
                subject_clinical_subject_id=ClinicalSubjectId("cs_aaaaaaaa11111111"),
                shared_with="Police",
                scope=ConsentScope.RISK_ONLY,
                summary_of_data_shared="Suicide attempt report",
                shared_at=now,
                shared_by=UserId("clin-1"),
                created_at=now,
            )

    def test_legal_basis_path_succeeds(self):
        now = datetime.now(UTC)
        e = DataSharingRegisterEntry(
            id=DataSharingRegisterEntryId("d-2"),
            tenant_id=TenantId("t-1"),
            subject_clinical_subject_id=ClinicalSubjectId("cs_aaaaaaaa11111111"),
            shared_with="Uganda Police Family Unit",
            scope=ConsentScope.RISK_ONLY,
            summary_of_data_shared="Tarasoff disclosure",
            shared_at=now,
            shared_by=UserId("clin-1"),
            created_at=now,
            legal_basis="Statutory mandatory report — child safety",
        )
        assert e.consent_id is None


class TestDPOContact:
    def test_full_name_required(self):
        now = datetime.now(UTC)
        with pytest.raises(DomainError):
            DPOContact(
                id=DPOContactId("dpo-1"),
                tenant_id=TenantId("t-1"),
                full_name="",
                email=Email("dpo@example.com"),
                effective_from=date.today(),
                created_at=now,
                updated_at=now,
            )

    def test_effective_window_invariant(self):
        now = datetime.now(UTC)
        with pytest.raises(DomainError):
            DPOContact(
                id=DPOContactId("dpo-1"),
                tenant_id=TenantId("t-1"),
                full_name="Alice",
                email=Email("a@example.com"),
                effective_from=date.today(),
                effective_until=date.today() - timedelta(days=1),
                created_at=now,
                updated_at=now,
            )

    def test_archive(self):
        now = datetime.now(UTC)
        c = DPOContact(
            id=DPOContactId("dpo-1"),
            tenant_id=TenantId("t-1"),
            full_name="Alice",
            email=Email("a@example.com"),
            effective_from=date.today() - timedelta(days=30),
            created_at=now,
            updated_at=now,
        )
        c.archive(ending_on=date.today())
        assert c.effective_until == date.today()
        with pytest.raises(DomainError):
            c.archive(ending_on=date.today())
