"""
Person Mapper

Converts between PersonEntity (domain) and PersonModel (persistence).
"""

from datetime import date

from app.domain.entities.person import PersonEntity
from app.domain.entities.user import UserEntity
from app.domain.enums import BaseStatus, PersonType, RelationType, StaffRole, WorkStatus
from app.domain.value_objects.core import (
    ClientId,
    DependentInfo,
    Email,
    EmergencyContact,
    EmploymentInfo,
    LicenseInfo,
    PersonId,
    StaffInfo,
    TenantId,
    UserId,
)
from app.infrastructure.models.person_model import PersonModel
from app.shared.utils.datetime import ensure_utc


class PersonMapper:
    """Mapper for PersonEntity ↔ PersonModel conversion"""

    @staticmethod
    def to_entity(model: PersonModel, profile: UserEntity) -> PersonEntity:
        """
        Convert database model to domain entity.

        Args:
            model: PersonModel from database
            profile: UserEntity profile

        Returns:
            PersonEntity with business logic
        """
        # Reconstruct value objects
        person_id = PersonId(model.id)
        tenant_id = TenantId(model.tenant_id)
        user_id = UserId(model.user_id)

        # Reconstruct enums
        person_type = PersonType(model.person_type)
        secondary_person_type = (
            PersonType(model.secondary_person_type)
            if model.secondary_person_type
            else None
        )
        status = BaseStatus(model.status)

        # Reconstruct value objects from JSON
        employment_info = None
        if model.employment_info:
            emp_dict = model.employment_info
            employment_info = EmploymentInfo(
                role=emp_dict["role"],
                start_date=date.fromisoformat(emp_dict["start_date"])
                if isinstance(emp_dict["start_date"], str)
                else emp_dict["start_date"],
                status=WorkStatus(emp_dict["status"]),
                department=emp_dict.get("department"),
                employee_id=emp_dict.get("employee_id"),
                end_date=date.fromisoformat(emp_dict["end_date"])
                if emp_dict.get("end_date") and isinstance(emp_dict["end_date"], str)
                else emp_dict.get("end_date"),
            )

        license_info = None
        if model.license_info:
            lic_dict = model.license_info
            license_info = LicenseInfo(
                number=lic_dict["number"],
                issuing_authority=lic_dict["issuing_authority"],
                expiry_date=date.fromisoformat(lic_dict["expiry_date"])
                if lic_dict.get("expiry_date")
                and isinstance(lic_dict["expiry_date"], str)
                else lic_dict.get("expiry_date"),
            )

        staff_info = None
        if model.staff_info:
            staff_dict = model.staff_info
            staff_info = StaffInfo(
                role=StaffRole(staff_dict["role"]),
                client_id=ClientId(staff_dict["client_id"]),
                department=staff_dict.get("department"),
                can_manage_clients=staff_dict.get("can_manage_clients", False),
                can_manage_services=staff_dict.get("can_manage_services", False),
                can_view_reports=staff_dict.get("can_view_reports", False),
            )

        dependent_info = None
        if model.dependent_info:
            dep_dict = model.dependent_info
            dependent_info = DependentInfo(
                primary_employee_id=PersonId(dep_dict["primary_employee_id"]),
                relationship=RelationType(dep_dict["relationship"]),
                guardian_id=UserId(dep_dict["guardian_id"])
                if dep_dict.get("guardian_id")
                else None,
            )

        emergency_contact = None
        if model.emergency_contact:
            ec_dict = model.emergency_contact

            # Normalize empty strings to None for validation
            phone = ec_dict.get("phone")
            phone = phone if phone and phone.strip() else None
            
            email_str = ec_dict.get("email")
            email = Email(email_str) if email_str and email_str.strip() else None

            # EmergencyContact.__post_init__() validates that at least one of
            # phone or email is non-empty (not None and not empty string)
            emergency_contact = EmergencyContact(
                name=ec_dict["name"],
                phone=phone,
                email=email,
            )

        # Note: profile is required and should be loaded separately via UserRepository

        # Create entity
        return PersonEntity(
            _id=person_id,
            _tenant_id=tenant_id,
            _person_type=person_type,
            _is_dual_role=model.is_dual_role,
            _secondary_person_type=secondary_person_type,
            _user_id=user_id,
            _profile=profile,
            _employment_info=employment_info,
            _license_info=license_info,
            _staff_info=staff_info,
            _dependent_info=dependent_info,
            _status=status,
            _emergency_contact=emergency_contact,
            _last_service_date=model.last_service_date,
            _created_at=ensure_utc(model.created_at),
            _updated_at=ensure_utc(model.updated_at),
            _deleted_at=ensure_utc(model.deleted_at),
        )

    @staticmethod
    def to_model(entity: PersonEntity) -> PersonModel:
        """
        Convert domain entity to database model.

        Args:
            entity: PersonEntity with business logic

        Returns:
            PersonModel for persistence
        """
        # Convert value objects to JSON
        employment_info = None
        if entity._employment_info:
            employment_info = {
                "role": entity._employment_info.role,
                "start_date": entity._employment_info.start_date.isoformat(),
                "status": entity._employment_info.status.value,
                "department": entity._employment_info.department,
                "employee_id": entity._employment_info.employee_id,
                "end_date": entity._employment_info.end_date.isoformat()
                if entity._employment_info.end_date
                else None,
            }

        license_info = None
        if entity._license_info:
            license_info = {
                "number": entity._license_info.number,
                "issuing_authority": entity._license_info.issuing_authority,
                "expiry_date": entity._license_info.expiry_date.isoformat()
                if entity._license_info.expiry_date
                else None,
            }

        staff_info = None
        if entity._staff_info:
            staff_info = {
                "role": entity._staff_info.role.value,
                "client_id": entity._staff_info.client_id.value,
                "department": entity._staff_info.department,
                "can_manage_clients": entity._staff_info.can_manage_clients,
                "can_manage_services": entity._staff_info.can_manage_services,
                "can_view_reports": entity._staff_info.can_view_reports,
            }

        dependent_info = None
        if entity._dependent_info:
            dependent_info = {
                "primary_employee_id": entity._dependent_info.primary_employee_id.value,
                "relationship": entity._dependent_info.relationship.value,
                "guardian_id": entity._dependent_info.guardian_id.value
                if entity._dependent_info.guardian_id
                else None,
            }

        emergency_contact = None
        if entity._emergency_contact:
            emergency_contact = {
                "name": entity._emergency_contact.name,
                "phone": entity._emergency_contact.phone,
                "email": entity._emergency_contact.email.value
                if entity._emergency_contact.email
                else None,
            }

        # Create model
        model = PersonModel(
            id=entity._id.value,
            tenant_id=entity._tenant_id.value,
            person_type=entity._person_type.value,
            is_dual_role=entity._is_dual_role,
            secondary_person_type=entity._secondary_person_type.value
            if entity._secondary_person_type
            else None,
            user_id=entity._user_id.value,
            employment_info=employment_info,
            license_info=license_info,
            staff_info=staff_info,
            dependent_info=dependent_info,
            status=entity._status.value,
            emergency_contact=emergency_contact,
            last_service_date=entity._last_service_date,
            deleted_at=entity._deleted_at,
        )

        # Set timestamps explicitly to ensure they're available in-memory after merge()
        # session.merge() doesn't automatically refresh database-generated values
        if entity._created_at:
            model.created_at = entity._created_at
        if entity._updated_at:
            model.updated_at = entity._updated_at

        return model
