"""Mapper-level evidence that national_id, passport_number and date_of_birth
are encrypted at rest, matching the sibling ServiceSession fields."""

from datetime import UTC, date, datetime

import pytest

from app.core.encryption import EncryptionError, KeyProvider, set_key_provider
from app.domain.entities.eligible_member import EligibleMember
from app.domain.enums import EligibilityStatus, MemberRelation
from app.domain.value_objects.core import ClientId, EligibleMemberId, TenantId
from app.infrastructure.mappers.eligible_member_mapper import EligibleMemberMapper
from app.infrastructure.models.eligible_member_model import EligibleMemberModel


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


def _make_entity(
    tenant: str,
    *,
    national_id: str | None = None,
    passport_number: str | None = None,
    date_of_birth: date | None = None,
) -> EligibleMember:
    now = datetime.now(UTC)
    return EligibleMember(
        id=EligibleMemberId("em-1"),
        tenant_id=TenantId(tenant),
        client_id=ClientId("client-1"),
        employer_member_id="HR-1",
        relation=MemberRelation.EMPLOYEE,
        status=EligibilityStatus.ACTIVE,
        national_id=national_id,
        passport_number=passport_number,
        date_of_birth=date_of_birth,
        created_at=now,
        updated_at=now,
    )


class TestEligibleMemberEncryptionWiring:
    def test_to_model_persists_ciphertext_not_plaintext(self):
        entity = _make_entity(
            "t-1",
            national_id="CM12345678AB",
            passport_number="P0987654",
            date_of_birth=date(1990, 4, 12),
        )

        model = EligibleMemberMapper.to_model(entity)

        assert model.national_id is not None
        assert model.passport_number is not None
        assert model.date_of_birth is not None
        assert model.national_id != "CM12345678AB"
        assert model.passport_number != "P0987654"
        assert model.date_of_birth != "1990-04-12"
        assert "CM12345678AB" not in model.national_id
        assert "P0987654" not in model.passport_number
        assert "1990-04-12" not in model.date_of_birth

    def test_round_trip_preserves_plaintext(self):
        entity = _make_entity(
            "t-1",
            national_id="CM12345678AB",
            passport_number="P0987654",
            date_of_birth=date(1990, 4, 12),
        )
        model = EligibleMemberMapper.to_model(entity)

        rehydrated = EligibleMemberMapper.to_entity(model)
        assert rehydrated.national_id == "CM12345678AB"
        assert rehydrated.passport_number == "P0987654"
        assert rehydrated.date_of_birth == date(1990, 4, 12)

    def test_none_remains_none_through_mapper(self):
        entity = _make_entity("t-1")
        model = EligibleMemberMapper.to_model(entity)
        assert model.national_id is None
        assert model.passport_number is None
        assert model.date_of_birth is None
        rehydrated = EligibleMemberMapper.to_entity(model)
        assert rehydrated.national_id is None
        assert rehydrated.passport_number is None
        assert rehydrated.date_of_birth is None

    def test_ciphertext_is_tenant_bound(self):
        entity_a = _make_entity("t-A", national_id="shared-id")
        entity_b = _make_entity("t-B", national_id="shared-id")
        model_a = EligibleMemberMapper.to_model(entity_a)
        model_b = EligibleMemberMapper.to_model(entity_b)
        assert model_a.national_id != model_b.national_id

        forged = EligibleMemberModel(
            id=model_a.id,
            tenant_id="t-B",
            client_id=model_a.client_id,
            employer_member_id=model_a.employer_member_id,
            relation=model_a.relation,
            status=model_a.status,
            national_id=model_a.national_id,
            created_at=model_a.created_at,
            updated_at=model_a.updated_at,
        )
        with pytest.raises(EncryptionError):
            EligibleMemberMapper.to_entity(forged)
