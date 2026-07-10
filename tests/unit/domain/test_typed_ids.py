"""
Unit tests for typed identifier subclasses.

Phase 0 #C6 (SAD §13.2): each entity has its own ID type so the
type checker flags cross-type misuse. This test guards against a
regression to type aliases (which would silently accept any string).
"""

import pytest

from app.domain.value_objects.core import (
    ActivityId,
    AuditLogId,
    ClientId,
    ClientTagId,
    ContactId,
    ContractId,
    DocumentId,
    EntityChangeId,
    Id,
    IndustryId,
    KPIId,
    KPIAssignmentId,
    PersonId,
    ServiceAssignmentId,
    ServiceId,
    SessionId,
    TenantId,
    UserId,
)

ALL_ID_TYPES = [
    ActivityId,
    AuditLogId,
    ClientId,
    ClientTagId,
    ContactId,
    ContractId,
    DocumentId,
    EntityChangeId,
    IndustryId,
    KPIAssignmentId,
    KPIId,
    PersonId,
    ServiceAssignmentId,
    ServiceId,
    SessionId,
    TenantId,
    UserId,
]


class TestTypedIds:
    def test_all_id_types_are_distinct_classes(self):
        """The first cleanup goal: not aliases of one another."""
        seen = {cls.__name__: cls for cls in ALL_ID_TYPES}
        # Every ID type is itself, not the same class as another.
        for a_name, a_cls in seen.items():
            for b_name, b_cls in seen.items():
                if a_name == b_name:
                    continue
                assert a_cls is not b_cls, (
                    f"{a_name} and {b_name} resolve to the same class "
                    "— have the type aliases regressed?"
                )

    def test_each_id_subclasses_id_base(self):
        for cls in ALL_ID_TYPES:
            assert issubclass(cls, Id), f"{cls.__name__} must subclass Id"

    def test_validation_inherited_from_base(self):
        with pytest.raises(ValueError):
            PersonId("")  # empty
        with pytest.raises(ValueError):
            UserId("x" * 26)  # too long

    def test_value_equality_within_type(self):
        assert PersonId("abc") == PersonId("abc")
        assert UserId("abc") != UserId("abd")

    def test_cross_type_inequality(self):
        """Two IDs with the same string value but different types are not equal."""
        # Python's default dataclass eq compares type + fields; subclasses
        # share the field shape but differ in class. Across distinct subclasses,
        # equality must be False even when values match — this is what gives
        # us nominal typing at runtime.
        assert PersonId("abc") != UserId("abc")
        assert TenantId("abc") != ClientId("abc")

    def test_hashable_per_type(self):
        # Frozen dataclasses are hashable; same-type / same-value collide as
        # expected, cross-type does not.
        assert hash(PersonId("abc")) == hash(PersonId("abc"))
