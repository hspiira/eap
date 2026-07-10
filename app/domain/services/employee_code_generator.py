"""
Employee Code Generator Service

Generates unique employee codes for client employees following the format:
{CLIENT_CODE}-{FAMILY_CODE}-{MEMBER_CODE}

Family codes are shared among family members (employee + dependents).
Member codes increment sequentially within each family.
"""

from app.domain.repositories.person_repository import PersonRepository
from app.domain.repositories.client_repository import ClientRepository
from app.domain.value_objects.core import (
    ClientId,
    ClientEmployeeCode,
    PersonId,
    TenantId,
)
from app.domain.enums import PersonType


class EmployeeCodeGenerator:
    """Service for generating unique employee codes."""

    def __init__(
        self,
        person_repository: PersonRepository,
        client_repository: ClientRepository,
    ):
        self.person_repository = person_repository
        self.client_repository = client_repository

    async def generate_code(
        self,
        client_id: ClientId,
        tenant_id: TenantId,
        family_id: PersonId | None = None,
        person_id: PersonId | None = None,
    ) -> ClientEmployeeCode:
        """
        Generate a unique employee code for a client employee.

        Args:
            client_id: The client identifier
            tenant_id: The tenant identifier
            family_id: Optional family identifier (if adding to existing family)
            person_id: Optional person identifier (if person already exists and has family)

        Returns:
            ClientEmployeeCode with unique code

        Raises:
            ValueError: If client not found or code generation fails
        """
        client = await self.client_repository.get_by_id(client_id)
        if not client:
            raise ValueError(f"Client {client_id.value} not found")

        client_code = client.code

        if family_id:
            family_code = await self._get_family_code(
                client_id, tenant_id, family_id
            )
        elif person_id:
            person = await self.person_repository.get_by_id(person_id)
            if person and person.family_id:
                family_code = await self._get_family_code(
                    client_id, tenant_id, person.family_id
                )
            else:
                family_code = await self._get_next_family_code(client_id, tenant_id)
        else:
            family_code = await self._get_next_family_code(client_id, tenant_id)

        member_code = await self._get_next_member_code(
            client_id, tenant_id, family_code
        )

        return ClientEmployeeCode(
            client_code=client_code,
            family_code=family_code,
            member_code=member_code,
        )

    async def _get_family_code(
        self, client_id: ClientId, tenant_id: TenantId, family_id: PersonId
    ) -> str:
        """
        Get the family code for an existing family.

        Args:
            client_id: The client identifier
            tenant_id: The tenant identifier
            family_id: The family head person identifier

        Returns:
            Family code (2-digit string)

        Raises:
            ValueError: If family head not found or not a client employee
        """
        family_head = await self.person_repository.get_by_id(family_id)
        if not family_head:
            raise ValueError(f"Family head {family_id.value} not found")

        if not family_head.employment_info:
            raise ValueError(
                f"Family head {family_id.value} is not a client employee"
            )

        if family_head.employment_info.client_id != client_id:
            raise ValueError(
                "Family head belongs to different client. "
                + f"Expected {client_id.value}, got {family_head.employment_info.client_id.value}"
            )

        employee_code = family_head.employment_info.employee_code
        return employee_code.family_code

    async def _get_next_family_code(
        self, client_id: ClientId, tenant_id: TenantId
    ) -> str:
        """
        Get the next available family code for a client.

        Args:
            client_id: The client identifier
            tenant_id: The tenant identifier

        Returns:
            Next available family code (2-digit string, zero-padded)
        """
        employees = await self.person_repository.get_by_type(
            tenant_id, PersonType.CLIENT_EMPLOYEE
        )

        family_codes: set[str] = set()
        for employee in employees:
            if (
                employee.employment_info
                and employee.employment_info.client_id == client_id
            ):
                family_codes.add(employee.employment_info.employee_code.family_code)

        next_code = 0
        while True:
            family_code_str = f"{next_code:02d}"
            if family_code_str not in family_codes:
                return family_code_str
            next_code += 1
            if next_code > 99:
                raise ValueError(
                    f"Maximum family codes (99) reached for client {client_id.value}"
                )

    async def _get_next_member_code(
        self, client_id: ClientId, tenant_id: TenantId, family_code: str
    ) -> str:
        """
        Get the next available member code for a family.

        Args:
            client_id: The client identifier
            tenant_id: The tenant identifier
            family_code: The family code

        Returns:
            Next available member code (2-digit string, zero-padded)
        """
        employees = await self.person_repository.get_by_type(
            tenant_id, PersonType.CLIENT_EMPLOYEE
        )

        member_codes: set[str] = set()
        for employee in employees:
            if (
                employee.employment_info
                and employee.employment_info.client_id == client_id
                and employee.employment_info.employee_code.family_code == family_code
            ):
                member_codes.add(
                    employee.employment_info.employee_code.member_code
                )

        dependents = await self.person_repository.get_by_type(
            tenant_id, PersonType.DEPENDENT
        )
        for dependent in dependents:
            if dependent.family_id:
                family_head = await self.person_repository.get_by_id(
                    dependent.family_id
                )
                if (
                    family_head
                    and family_head.employment_info
                    and family_head.employment_info.client_id == client_id
                    and family_head.employment_info.employee_code.family_code
                    == family_code
                ):
                    pass

        next_code = 0
        while True:
            member_code_str = f"{next_code:02d}"
            if member_code_str not in member_codes:
                return member_code_str
            next_code += 1
            if next_code > 99:
                raise ValueError(
                    f"Maximum member codes (99) reached for family {family_code} "
                    + f"in client {client_id.value}"
                )
