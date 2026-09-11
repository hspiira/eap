"""Mapper-level evidence that MemberNextOfKin.name/phone/email are
encrypted at rest, matching the sibling contact/PII fields."""

from datetime import UTC, datetime

import pytest

from app.core.encryption import EncryptionError, KeyProvider, set_key_provider
from app.domain.entities.member_next_of_kin import MemberNextOfKin
from app.domain.value_objects.core import EligibleMemberId, Email, MemberNextOfKinId, TenantId
from app.infrastructure.mappers.member_next_of_kin_mapper import MemberNextOfKinMapper
from app.infrastructure.models.member_next_of_kin_model import MemberNextOfKinModel


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


def _make_kin(
    tenant: str,
    *,
    name: str = "Jane Doe",
    phone: str | None = "+256700000000",
    email: Email | None = None,
) -> MemberNextOfKin:
    now = datetime.now(UTC)
    return MemberNextOfKin(
        id=MemberNextOfKinId("nok-1"),
        tenant_id=TenantId(tenant),
        member_id=EligibleMemberId("member-1"),
        name=name,
        relationship="Spouse",
        phone=phone,
        email=email,
        is_primary=True,
        created_at=now,
        updated_at=now,
    )


class TestMemberNextOfKinEncryptionWiring:
    def test_to_model_persists_ciphertext_not_plaintext(self):
        entity = _make_kin("t-1", email=Email("jane@example.com"))

        model = MemberNextOfKinMapper.to_model(entity)

        assert model.name != "Jane Doe"
        assert model.phone != "+256700000000"
        assert model.email != "jane@example.com"
        assert "Jane" not in model.name
        assert "jane@example.com" not in model.email

    def test_round_trip_preserves_plaintext(self):
        entity = _make_kin("t-1", email=Email("jane@example.com"))
        model = MemberNextOfKinMapper.to_model(entity)

        rehydrated = MemberNextOfKinMapper.to_entity(model)
        assert rehydrated.name == "Jane Doe"
        assert rehydrated.phone == "+256700000000"
        assert rehydrated.email == Email("jane@example.com")

    def test_none_phone_and_email_remain_none(self):
        entity = _make_kin("t-1", phone=None, email=Email("jane@example.com"))
        model = MemberNextOfKinMapper.to_model(entity)
        rehydrated = MemberNextOfKinMapper.to_entity(model)
        assert rehydrated.phone is None

    def test_ciphertext_is_tenant_bound(self):
        entity_a = _make_kin("t-A")
        entity_b = _make_kin("t-B")
        model_a = MemberNextOfKinMapper.to_model(entity_a)
        model_b = MemberNextOfKinMapper.to_model(entity_b)
        assert model_a.name != model_b.name

        forged = MemberNextOfKinModel(
            id=model_a.id,
            tenant_id="t-B",
            member_id=model_a.member_id,
            name=model_a.name,
            relationship=model_a.relationship,
            phone=model_a.phone,
            is_primary=model_a.is_primary,
            created_at=model_a.created_at,
            updated_at=model_a.updated_at,
        )
        with pytest.raises(EncryptionError):
            MemberNextOfKinMapper.to_entity(forged)
