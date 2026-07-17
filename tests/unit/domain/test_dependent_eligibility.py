"""
Unit tests for DependentInfo VO and PersonEntity dependent eligibility.

Covers Phase 0 fix #C5 (SAD §13.2): is_eligible_for_services for DEPENDENT
must track the primary employee's eligibility, not silently return truthy.
"""

from datetime import UTC, date, datetime

from app.domain.entities.person import PersonEntity
from app.domain.entities.user import UserEntity
from app.domain.enums import (
    RelationType,
    UserStatus,
    WorkStatus,
)
from app.domain.value_objects.core import (
    ClientEmployeeCode,
    ClientId,
    DependentInfo,
    Email,
    EmploymentInfo,
    PersonId,
    TenantId,
    UserId,
)

# === DependentInfo VO ===


class TestDependentInfoIsEligible:
    def test_intrinsic_eligibility_true_for_recognised_relationships(self):
        for rel in (
            RelationType.SPOUSE,
            RelationType.CHILD,
            RelationType.PARENT,
            RelationType.SIBLING,
            RelationType.GRANDPARENT,
            RelationType.GUARDIAN,
        ):
            info = DependentInfo(
                primary_employee_id=PersonId("emp-1"),
                relationship=rel,
            )
            assert info.is_eligible() is True, f"{rel} should be eligible"

    def test_intrinsic_eligibility_false_for_other(self):
        info = DependentInfo(
            primary_employee_id=PersonId("emp-1"),
            relationship=RelationType.OTHER,
        )
        assert info.is_eligible() is False

    def test_returns_bool_not_exception(self):
        info = DependentInfo(
            primary_employee_id=PersonId("emp-1"),
            relationship=RelationType.SPOUSE,
        )
        result = info.is_eligible()
        assert isinstance(result, bool)


# === PersonEntity composed eligibility ===


def _make_user(uid: str, tid: str) -> UserEntity:
    now = datetime.now(UTC)
    return UserEntity(
        id=UserId(uid),
        tenant_id=TenantId(tid),
        email=Email(f"{uid}@example.com"),
        status=UserStatus.ACTIVE,
        is_two_factor_enabled=False,
        created_at=now,
        updated_at=now,
    )


def _make_primary_employee(active: bool) -> PersonEntity:
    user = _make_user("usr-primary", "tenant-1")
    employment = EmploymentInfo(
        client_id=ClientId("client-1"),
        employee_code=ClientEmployeeCode(
            client_code="ACM", family_code="01", member_code="01"
        ),
        role="Engineer",
        start_date=date(2024, 1, 1),
        status=WorkStatus.ACTIVE if active else WorkStatus.TERMINATED,
    )
    person = PersonEntity.create_client_employee(
        id=PersonId("primary-1"),
        tenant_id=TenantId("tenant-1"),
        user_id=UserId("usr-primary"),
        profile=user,
        employment_info=employment,
    )
    person.activate()  # PENDING -> ACTIVE
    return person


def _make_dependent(primary: PersonEntity, relation: RelationType) -> PersonEntity:
    user = _make_user("usr-dep", "tenant-1")
    info = DependentInfo(
        primary_employee_id=primary.id,
        relationship=relation,
    )
    person = PersonEntity.create_dependent(
        id=PersonId("dep-1"),
        tenant_id=TenantId("tenant-1"),
        user_id=UserId("usr-dep"),
        profile=user,
        dependent_info=info,
        primary_employee=primary,
    )
    person.activate()
    return person


class TestPersonEntityDependentEligibility:
    def test_dependent_eligible_when_primary_active(self):
        primary = _make_primary_employee(active=True)
        dependent = _make_dependent(primary, RelationType.SPOUSE)
        assert dependent.is_eligible_for_services(primary_employee=primary) is True

    def test_dependent_not_eligible_when_primary_terminated(self):
        primary = _make_primary_employee(active=False)
        dependent = _make_dependent(primary, RelationType.SPOUSE)
        assert dependent.is_eligible_for_services(primary_employee=primary) is False

    def test_dependent_fails_closed_when_primary_not_supplied(self):
        primary = _make_primary_employee(active=True)
        dependent = _make_dependent(primary, RelationType.SPOUSE)
        assert dependent.is_eligible_for_services() is False

    def test_dependent_not_eligible_when_relationship_is_other(self):
        primary = _make_primary_employee(active=True)
        dependent = _make_dependent(primary, RelationType.OTHER)
        assert dependent.is_eligible_for_services(primary_employee=primary) is False

    def test_client_employee_eligibility_unaffected_by_primary_arg(self):
        primary = _make_primary_employee(active=True)
        # CLIENT_EMPLOYEE path ignores primary_employee param.
        assert primary.is_eligible_for_services() is True
        assert primary.is_eligible_for_services(primary_employee=primary) is True

    def test_inactive_dependent_not_eligible_even_with_active_primary(self):
        primary = _make_primary_employee(active=True)
        dependent = _make_dependent(primary, RelationType.SPOUSE)
        dependent.deactivate()
        assert dependent.is_eligible_for_services(primary_employee=primary) is False
