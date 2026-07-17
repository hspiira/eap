"""
Person SQLAlchemy Model

Database representation of Person aggregate.
This is a data container only - no business logic.
"""

from datetime import date

from sqlalchemy import JSON, CheckConstraint, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, validates

from app.domain.enums import BaseStatus, PersonType, RelationType, StaffRole, WorkStatus
from app.infrastructure.models.base import (
    Base,
    CuidMixin,
    SoftDeleteMixin,
    TenantMixin,
    TimestampMixin,
)
from app.infrastructure.models.json_schemas import (
    DependentInfoDict,
    EmergencyContactDict,
    EmploymentInfoDict,
    LicenseInfoDict,
    ProviderProfileDict,
    StaffInfoDict,
)


class PersonModel(CuidMixin, TenantMixin, Base, TimestampMixin, SoftDeleteMixin):
    """
    SQLAlchemy Model for Person aggregate.

    This is a data container for persistence only.
    Business logic lives in PersonEntity.
    """

    __tablename__ = "persons"
    __table_args__ = (
        CheckConstraint(
            "person_type IN (" + ", ".join(f"'{e.value}'" for e in PersonType) + ")",
            name="person_type_check",
        ),
        CheckConstraint(
            "secondary_person_type IS NULL OR secondary_person_type IN ("
            + ", ".join(f"'{e.value}'" for e in PersonType)
            + ")",
            name="person_secondary_type_check",
        ),
        CheckConstraint(
            "status IN (" + ", ".join(f"'{e.value}'" for e in BaseStatus) + ")",
            name="person_status_check",
        ),
    )

    # Type discriminator - use native PG enum (create_type=False)
    person_type: Mapped[PersonType] = mapped_column(
        Enum(
            PersonType,
            name="persontype",
            create_type=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )
    is_dual_role: Mapped[bool] = mapped_column(default=False, nullable=False)
    secondary_person_type: Mapped[PersonType | None] = mapped_column(
        Enum(
            PersonType,
            name="persontype",
            create_type=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=True,
    )

    # Core relationships
    user_id: Mapped[str] = mapped_column(
        String(25),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    family_id: Mapped[str | None] = mapped_column(
        String(25),
        ForeignKey("persons.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Type-specific info (stored as JSON value objects)
    employment_info: Mapped[EmploymentInfoDict | None] = mapped_column(JSON, nullable=True)
    """
    Employment information for CLIENT_EMPLOYEE person types.
    
    Schema: {
        "client_id": str,
        "employee_code": str (format: CLIENT-FAMILY-MEMBER, e.g., "MNT-00-00"),
        "role": str,
        "start_date": str (ISO date: YYYY-MM-DD),
        "status": str (WorkStatus enum value),
        "department": str | None,
        "employee_id": str | None,
        "end_date": str | None (ISO date: YYYY-MM-DD)
    }
    """

    license_info: Mapped[LicenseInfoDict | None] = mapped_column(JSON, nullable=True)
    """
    Professional license information for SERVICE_PROVIDER person types.

    Schema: {
        "number": str,
        "issuing_authority": str,
        "expiry_date": str | None (ISO date: YYYY-MM-DD)
    }
    """

    provider_profile: Mapped["ProviderProfileDict | None"] = mapped_column(JSON, nullable=True)
    """Panel metadata for SERVICE_PROVIDER persons (tier, region, accreditation)."""

    staff_info: Mapped[StaffInfoDict | None] = mapped_column(JSON, nullable=True)
    """
    Staff information for PLATFORM_STAFF person types.
    
    Schema: {
        "role": str (StaffRole enum value),
        "client_id": str,
        "department": str | None,
        "can_manage_clients": bool,
        "can_manage_services": bool,
        "can_view_reports": bool
    }
    """

    dependent_info: Mapped[DependentInfoDict | None] = mapped_column(JSON, nullable=True)
    """
    Dependent information for DEPENDENT person types.
    
    Schema: {
        "primary_employee_id": str,
        "relationship": str (RelationType enum value),
        "guardian_id": str | None
    }
    """

    # Shared
    status: Mapped[BaseStatus] = mapped_column(
        Enum(
            BaseStatus,
            name="basestatus",
            create_type=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=BaseStatus.PENDING,
    )

    emergency_contact: Mapped[EmergencyContactDict | None] = mapped_column(JSON, nullable=True)
    """
    Emergency contact information (shared across person types).
    
    Schema: {
        "name": str,
        "phone": str | None,
        "email": str | None
    }
    Note: At least one of phone or email must be provided.
    """
    last_service_date: Mapped[date | None] = mapped_column(nullable=True)

    # Validation methods
    @validates("employment_info")
    def validate_employment_info(
        self, key: str, value: EmploymentInfoDict | None
    ) -> EmploymentInfoDict | None:
        """Validate employment_info JSON structure."""
        if value is None:
            return None

        # Check required fields
        required_fields = ["role", "start_date", "status"]
        for field in required_fields:
            if field not in value:
                raise ValueError(f"employment_info missing required field: {field}")

        # Validate status is a valid WorkStatus value
        if value["status"] not in [e.value for e in WorkStatus]:
            raise ValueError(f"Invalid WorkStatus value: {value['status']}")

        # Validate date formats (basic check)
        for date_field in ["start_date", "end_date"]:
            if date_field in value and value[date_field] is not None:
                try:
                    date.fromisoformat(value[date_field])
                except (ValueError, TypeError) as e:
                    raise ValueError(
                        f"employment_info.{date_field} must be in ISO format (YYYY-MM-DD)"
                    ) from e

        return value

    @validates("license_info")
    def validate_license_info(
        self, key: str, value: LicenseInfoDict | None
    ) -> LicenseInfoDict | None:
        """Validate license_info JSON structure."""
        if value is None:
            return None

        # Check required fields
        required_fields = ["number", "issuing_authority"]
        for field in required_fields:
            if field not in value:
                raise ValueError(f"license_info missing required field: {field}")

        # Validate expiry_date format if present
        if "expiry_date" in value and value["expiry_date"] is not None:
            try:
                date.fromisoformat(value["expiry_date"])
            except (ValueError, TypeError) as err:
                raise ValueError(
                    "license_info.expiry_date must be in ISO format (YYYY-MM-DD)"
                ) from err

        return value

    @validates("staff_info")
    def validate_staff_info(self, key: str, value: StaffInfoDict | None) -> StaffInfoDict | None:
        """Validate staff_info JSON structure."""
        if value is None:
            return None

        # Check required fields
        required_fields = ["role", "client_id"]
        for field in required_fields:
            if field not in value:
                raise ValueError(f"staff_info missing required field: {field}")

        # Validate role is a valid StaffRole value
        if value["role"] not in [e.value for e in StaffRole]:
            raise ValueError(f"Invalid StaffRole value: {value['role']}")

        # Ensure boolean fields are booleans
        for bool_field in ["can_manage_clients", "can_manage_services", "can_view_reports"]:
            if bool_field in value and not isinstance(value[bool_field], bool):
                raise ValueError(f"staff_info.{bool_field} must be a boolean")

        return value

    @validates("dependent_info")
    def validate_dependent_info(
        self, key: str, value: DependentInfoDict | None
    ) -> DependentInfoDict | None:
        """Validate dependent_info JSON structure."""
        if value is None:
            return None

        # Check required fields
        required_fields = ["primary_employee_id", "relationship"]
        for field in required_fields:
            if field not in value:
                raise ValueError(f"dependent_info missing required field: {field}")

        # Validate relationship is a valid RelationType value
        if value["relationship"] not in [e.value for e in RelationType]:
            raise ValueError(f"Invalid RelationType value: {value['relationship']}")

        return value

    @validates("emergency_contact")
    def validate_emergency_contact(
        self, key: str, value: EmergencyContactDict | None
    ) -> EmergencyContactDict | None:
        """
        Validate emergency_contact JSON structure.

        Note: The "phone or email required" rule is enforced by the
        EmergencyContact value object constructor when converting from
        EmergencyContactDict to domain value object in the mapper.
        This validator only checks basic structure (name field presence).
        """
        if value is None:
            return None

        # Check required fields
        if "name" not in value:
            raise ValueError("emergency_contact missing required field: name")

        # Note: "phone or email required" validation is handled by
        # EmergencyContact.__post_init__() when the mapper converts
        # EmergencyContactDict to EmergencyContact value object in
        # PersonMapper.to_entity(). This ensures domain-level validation
        # is centralized in the value object.

        return value

    def __repr__(self) -> str:
        return (
            f"<PersonModel(id={self.id}, person_type={self.person_type}, user_id={self.user_id})>"
        )
