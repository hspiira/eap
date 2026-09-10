"""Employment details flatten to columns and rehydrate as a value object."""

from datetime import UTC, datetime

from app.domain.entities.eligible_member import EligibleMember
from app.domain.enums import EligibilityStatus, MemberRelation
from app.domain.value_objects.core import ClientId, EligibleMemberId, TenantId
from app.domain.value_objects.staffing import EmploymentDetails
from app.infrastructure.mappers.eligible_member_mapper import EligibleMemberMapper
from app.infrastructure.models.eligible_member_model import EligibleMemberModel

COLUMNS = ("job_title", "job_classification", "skill", "department", "unit", "employment_type")


def _entity(employment: EmploymentDetails | None) -> EligibleMember:
    now = datetime.now(UTC)
    return EligibleMember(
        id=EligibleMemberId("em-1"),
        tenant_id=TenantId("t-1"),
        client_id=ClientId("client-1"),
        employer_member_id="HR-1",
        relation=MemberRelation.EMPLOYEE,
        status=EligibilityStatus.ACTIVE,
        employment=employment,
        created_at=now,
        updated_at=now,
    )


def _model(**employment: str | None) -> EligibleMemberModel:
    now = datetime.now(UTC)
    return EligibleMemberModel(
        id="em-1",
        tenant_id="t-1",
        client_id="client-1",
        employer_member_id="HR-1",
        relation=MemberRelation.EMPLOYEE,
        status=EligibilityStatus.ACTIVE,
        created_at=now,
        updated_at=now,
        **employment,
    )


def test_details_flatten_onto_their_own_columns() -> None:
    details = EmploymentDetails(
        job_title="Branch Manager",
        job_classification="Manager",
        skill="Officer",
        department="Operations",
        unit="Kampala Road branch",
        employment_type="Permanent",
    )
    model = EligibleMemberMapper.to_model(_entity(details))
    for column in COLUMNS:
        assert getattr(model, column) == getattr(details, column), column


def test_a_member_without_details_writes_null_columns() -> None:
    model = EligibleMemberMapper.to_model(_entity(None))
    for column in COLUMNS:
        assert getattr(model, column) is None, column


def test_columns_rehydrate_into_a_value_object() -> None:
    entity = EligibleMemberMapper.to_entity(_model(department="Treasury", unit="Credit"))
    assert entity.employment is not None
    assert entity.employment.department == "Treasury"
    assert entity.employment.unit == "Credit"
    assert entity.employment.job_title is None


def test_all_null_columns_rehydrate_as_no_details() -> None:
    assert EligibleMemberMapper.to_entity(_model()).employment is None


def test_the_mapping_round_trips() -> None:
    details = EmploymentDetails(job_title="Officer", department="Risk", employment_type="FTC")
    model = EligibleMemberMapper.to_model(_entity(details))
    assert EligibleMemberMapper.to_entity(model).employment == details
