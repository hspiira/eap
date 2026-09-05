"""Repository port for restricted member next-of-kin contacts."""

from abc import abstractmethod

from app.domain.entities.member_next_of_kin import MemberNextOfKin
from app.domain.repositories.base_repository import BaseRepository
from app.domain.value_objects.core import EligibleMemberId, MemberNextOfKinId, TenantId


class MemberNextOfKinRepository(BaseRepository[MemberNextOfKin, MemberNextOfKinId]):
    @abstractmethod
    async def list_for_member(
        self, tenant_id: TenantId, member_id: EligibleMemberId
    ) -> list[MemberNextOfKin]: ...
