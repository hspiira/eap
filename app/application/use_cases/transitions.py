"""Per-aggregate transition use cases (Phase 1 #C3 / ADR-004).

A single ``Transition<Aggregate>UseCase`` replaces the historical pile of
per-verb classes (ActivateXUseCase, SuspendXUseCase, …). Callers pass a
``<Aggregate>Transition`` enum value — one per business action — plus the
keyword arguments that action requires. The use case loads the aggregate
by id, dispatches to the matching method on the entity, persists, and
publishes any collected domain events.

Why an enum (not a string): the enum value *is* the entity method name,
so the dispatcher is a single ``getattr``. Adding a new transition is
"add an enum member + entity method" — no new use-case class required.

Invalid transitions are rejected by the entity itself (it raises
``InvalidStateError`` / ``DomainError``); the FSM lives on the entity, not
on this dispatcher.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Generic, TypeVar

from app.application.use_cases.base import BaseUseCase, RepositoryProtocol
from app.domain.exceptions import DomainError, NotFoundError
from app.shared.utils.datetime import utc_now

TEntity = TypeVar("TEntity")
TId = TypeVar("TId")
TTransition = TypeVar("TTransition", bound=Enum)


class TransitionUseCase(BaseUseCase[TEntity, TId], Generic[TEntity, TId, TTransition]):
    """Generic dispatcher mapping a transition enum to the entity method."""

    entity_name: str = "Entity"

    def __init__(self, repository: RepositoryProtocol[TEntity, TId]) -> None:
        super().__init__(repository)

    async def execute(
        self,
        entity_id: TId,
        transition: TTransition,
        **kwargs: Any,
    ) -> TEntity:
        entity = await self.repository.get_by_id(entity_id)
        if entity is None:
            id_value = getattr(entity_id, "value", str(entity_id))
            raise NotFoundError(
                f"{self.entity_name} not found: {id_value}",
                resource_type=self.entity_name,
                resource_id=str(id_value),
            )

        method_name = transition.value
        method = getattr(entity, method_name, None)
        if not callable(method):
            raise DomainError(
                f"{self.entity_name} does not support transition '{method_name}'"
            )

        method(**kwargs)
        if hasattr(entity, "updated_at"):
            entity.updated_at = utc_now()
        return await self._save_and_publish_events(entity)


# === Aggregate transition enums ===


class TenantTransition(str, Enum):
    ACTIVATE = "activate"
    SUSPEND = "suspend"
    TERMINATE = "terminate"
    ARCHIVE = "archive"
    RESTORE = "restore"
    UPDATE_NAME = "update_name"
    UPDATE_SETTINGS = "update_settings"
    UPDATE_SUBSCRIPTION_TIER = "update_subscription_tier"


class UserTransition(str, Enum):
    ACTIVATE = "activate"
    SUSPEND = "suspend"
    BAN = "ban"
    DEACTIVATE = "deactivate"
    TERMINATE = "terminate"
    VERIFY_EMAIL = "verify_email"
    UPDATE_PASSWORD = "update_password"
    UPDATE_PREFERENCES = "update_preferences"
    ENABLE_TWO_FACTOR = "enable_two_factor"
    DISABLE_TWO_FACTOR = "disable_two_factor"
    RECORD_LOGIN = "record_login"


class ClientTransition(str, Enum):
    ACTIVATE = "activate"
    DEACTIVATE = "deactivate"
    SUSPEND = "suspend"
    TERMINATE = "terminate"
    VERIFY = "verify"
    ARCHIVE = "archive"
    RESTORE = "restore"
    UPDATE_CONTACT_INFO = "update_contact_info"
    UPDATE_BILLING_ADDRESS = "update_billing_address"
    UPDATE_INDUSTRY = "update_industry"
    UPDATE_NAME = "update_name"
    UPDATE_PREFERRED_CONTACT_METHOD = "update_preferred_contact_method"
    UPDATE_TIER = "update_tier"


class PersonTransition(str, Enum):
    ACTIVATE = "activate"
    DEACTIVATE = "deactivate"
    TERMINATE = "terminate"
    ARCHIVE = "archive"
    RESTORE = "restore"
    UPDATE_EMERGENCY_CONTACT = "update_emergency_contact"
    UPDATE_EMPLOYMENT_INFO = "update_employment_info"
    UPDATE_DEPENDENT_INFO = "update_dependent_info"
    UPDATE_LICENSE_INFO = "update_license_info"
    UPDATE_STAFF_INFO = "update_staff_info"
    ADD_SECONDARY_ROLE = "add_secondary_role"
    REMOVE_SECONDARY_ROLE = "remove_secondary_role"


class ContractTransition(str, Enum):
    ACTIVATE = "activate"
    SIGN = "sign"
    RENEW = "renew"
    TERMINATE = "terminate"
    ARCHIVE = "archive"
    RESTORE = "restore"
    UPDATE_BILLING_RATE = "update_billing_rate"
    UPDATE_PAYMENT_FREQUENCY = "update_payment_frequency"
    UPDATE_PAYMENT_STATUS = "update_payment_status"
    UPDATE_AUTO_RENEW = "update_auto_renew"


class ServiceTransition(str, Enum):
    ACTIVATE = "activate"
    DEACTIVATE = "deactivate"
    ARCHIVE = "archive"
    RESTORE = "restore"
    UPDATE_DESCRIPTION = "update_description"
    UPDATE_DURATION = "update_duration"
    UPDATE_MAX_PARTICIPANTS = "update_max_participants"


class ServiceSessionTransition(str, Enum):
    COMPLETE = "complete"
    CANCEL = "cancel"
    RESCHEDULE = "reschedule"
    MARK_NO_SHOW = "mark_no_show"
    ARCHIVE = "archive"
    RESTORE = "restore"
    UPDATE_NOTES = "update_notes"
    UPDATE_FEEDBACK = "update_feedback"
    UPDATE_LOCATION = "update_location"


class DocumentTransition(str, Enum):
    PUBLISH = "publish"
    ARCHIVE = "archive"
    RESTORE = "restore"
    UPDATE_DESCRIPTION = "update_description"


class KPITransition(str, Enum):
    ACTIVATE = "activate"
    DEACTIVATE = "deactivate"
    UPDATE_TARGET_VALUE = "update_target_value"
    UPDATE_THRESHOLDS = "update_thresholds"
    UPDATE_DESCRIPTION = "update_description"


class KPIAssignmentTransition(str, Enum):
    ACTIVATE = "activate"
    DEACTIVATE = "deactivate"


class IndustryTransition(str, Enum):
    ACTIVATE = "activate"
    DEACTIVATE = "deactivate"
    UPDATE_NAME = "update_name"
    UPDATE_DESCRIPTION = "update_description"


class ClientTagTransition(str, Enum):
    ACTIVATE = "activate"
    DEACTIVATE = "deactivate"
    UPDATE_NAME = "update_name"
    UPDATE_DESCRIPTION = "update_description"


class ContactTransition(str, Enum):
    ACTIVATE = "activate"
    DEACTIVATE = "deactivate"
    UPDATE_PHONE = "update_phone"
    UPDATE_EMAIL = "update_email"
    UPDATE_NAME = "update_name"


class ServiceAssignmentTransition(str, Enum):
    ACTIVATE = "activate"
    DEACTIVATE = "deactivate"
    UPDATE_NOTES = "update_notes"


class ActivityTransition(str, Enum):
    UPDATE_OUTCOME = "update_outcome"
    UPDATE_NEXT_FOLLOW_UP = "update_next_follow_up"
    MARK_IMPORTANT = "mark_important"
