"""Mapper-level evidence that Case.referral_notes is encrypted at rest,
matching the sibling ServiceSession/EligibleMember/ClinicalNote fields."""

from datetime import UTC, datetime

import pytest

from app.core.encryption import EncryptionError, KeyProvider, set_key_provider
from app.domain.entities.case import Case
from app.domain.enums import CaseStatus
from app.domain.value_objects.core import CaseId, ClientId, ClinicalSubjectId, TenantId
from app.infrastructure.mappers.case_mapper import CaseMapper
from app.infrastructure.models.case_model import CaseModel


class _FixedKeyProvider(KeyProvider):
    def __init__(self, raw: bytes):
        self._raw = raw

    def get_kek(self) -> bytes:
        return self._raw


@pytest.fixture(autouse=True)
def isolate_provider():
    set_key_provider(_FixedKeyProvider(b"x" * 32))
    yield
    set_key_provider(_FixedKeyProvider(b"x" * 32))


def _make_case(tenant: str, *, referral_notes: str | None = None) -> Case:
    now = datetime.now(UTC)
    return Case(
        id=CaseId("case-1"),
        tenant_id=TenantId(tenant),
        clinical_subject_id=ClinicalSubjectId("subj-1"),
        client_id=ClientId("client-1"),
        presenting_problem="Anxiety",
        referral_source="SelfReferral",
        status=CaseStatus.INTAKE,
        opened_at=now,
        created_at=now,
        updated_at=now,
        referral_notes=referral_notes,
    )


class TestCaseReferralNotesEncryptionWiring:
    def test_to_model_persists_ciphertext_not_plaintext(self):
        plaintext = "Referred by line manager after a difficult performance review."
        entity = _make_case("t-1", referral_notes=plaintext)

        model = CaseMapper.to_model(entity)

        assert model.referral_notes is not None
        assert plaintext not in model.referral_notes

    def test_round_trip_preserves_plaintext(self):
        entity = _make_case("t-1", referral_notes="Sensitive detail about the referral")
        model = CaseMapper.to_model(entity)

        rehydrated = CaseMapper.to_entity(model)
        assert rehydrated.referral_notes == "Sensitive detail about the referral"

    def test_none_remains_none_through_mapper(self):
        entity = _make_case("t-1")
        model = CaseMapper.to_model(entity)
        assert model.referral_notes is None
        rehydrated = CaseMapper.to_entity(model)
        assert rehydrated.referral_notes is None

    def test_ciphertext_is_tenant_bound(self):
        entity_a = _make_case("t-A", referral_notes="shared text")
        entity_b = _make_case("t-B", referral_notes="shared text")
        model_a = CaseMapper.to_model(entity_a)
        model_b = CaseMapper.to_model(entity_b)
        assert model_a.referral_notes != model_b.referral_notes

        forged = CaseModel(
            id=model_a.id,
            tenant_id="t-B",
            clinical_subject_id=model_a.clinical_subject_id,
            client_id=model_a.client_id,
            presenting_problem=model_a.presenting_problem,
            referral_source=model_a.referral_source,
            referral_notes=model_a.referral_notes,
            status=model_a.status,
            opened_at=model_a.opened_at,
            created_at=model_a.created_at,
            updated_at=model_a.updated_at,
        )
        with pytest.raises(EncryptionError):
            CaseMapper.to_entity(forged)
