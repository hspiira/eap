"""Draw a completed session down against its programme authorization.

The session and the authorization sit on opposite sides of the pseudonymity
wall: a session carries a ``person_id``, an authorization is keyed on a
``case_id`` and a ``ClinicalSubjectId``. Nothing joins them, and the members
module is explicit that a person id is not a member id, so the case must be
supplied by a caller that already holds clinical context rather than inferred
from the session.

When no case is supplied the drawdown does not happen and the existing manual
route stays the way an authorization is consumed.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.entities.authorization import Authorization
from app.domain.enums import ServiceCategory
from app.domain.exceptions import DomainError, InvalidStateError
from app.domain.repositories.eap_programme_repository import AuthorizationRepository
from app.domain.value_objects.core import CaseId, TenantId


@dataclass(frozen=True)
class DrawdownResult:
    """Outcome of an attempted drawdown, including the reasons for not doing one."""

    authorization: Authorization | None
    reason: str | None = None

    @property
    def consumed(self) -> bool:
        return self.authorization is not None


def select_authorization(
    authorizations: list[Authorization],
    *,
    service_category: ServiceCategory,
) -> Authorization | None:
    """Pick the authorization a session of this category should draw down.

    Prefers the one closest to running out, so a client's older grant is spent
    before a newer one and an almost-exhausted grant does not linger.
    """
    candidates = [
        a
        for a in authorizations
        if a.service_category == service_category
        and a.is_active()
        and not a.is_expired()
        and a.sessions_remaining > 0
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda a: (a.sessions_remaining, a.granted_at))


class ConsumeAuthorizationForSessionUseCase:
    """Consumes one session from the matching authorization, if there is one."""

    def __init__(self, authorization_repository: AuthorizationRepository):
        self._authorizations = authorization_repository

    async def execute(
        self,
        *,
        tenant_id: TenantId,
        case_id: CaseId,
        service_category: ServiceCategory | None,
    ) -> DrawdownResult:
        if service_category is None:
            return DrawdownResult(None, "Service has no category, nothing to draw down against")

        existing = await self._authorizations.list_for_case(tenant_id, case_id)
        selected = select_authorization(existing, service_category=service_category)
        if selected is None:
            return DrawdownResult(
                None, f"No active authorization for {service_category.value} on this case"
            )

        try:
            selected.consume_session()
        except (DomainError, InvalidStateError) as exc:
            return DrawdownResult(None, str(exc))

        await self._authorizations.save(selected)
        return DrawdownResult(selected)
