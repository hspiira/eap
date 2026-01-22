"""
Service Entity (Aggregate Root)

Represents a service offering in the EAP platform.
Examples: Individual Counseling, Group Therapy, Crisis Intervention, etc.
"""

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.enums import BaseStatus
from app.domain.events import DomainEvent
from app.domain.exceptions import DomainError
from app.domain.value_objects.core import ServiceId, TenantId
from app.shared.utils.datetime import utc_now


@dataclass
class ServiceEntity:
    # Required fields (no defaults)
    _id: ServiceId
    _tenant_id: TenantId
    _name: str
    _description: str | None
    _status: BaseStatus
    _created_at: datetime
    _updated_at: datetime

    # Optional fields (with defaults)
    _category: str | None = None
    _duration_minutes: int | None = None
    _is_group_service: bool = False
    _max_participants: int | None = None
    _deleted_at: datetime | None = None
    _events: list[DomainEvent] = field(default_factory=list)

    def activate(self) -> None:
        """Activate service for use"""
        if self._deleted_at:
            raise DomainError("Cannot activate deleted service")
        if self._status == BaseStatus.ACTIVE:
            raise DomainError("Service is already active")
        self._status = BaseStatus.ACTIVE
        self._updated_at = utc_now()

    def deactivate(self, reason: str | None = None) -> None:
        """Deactivate service"""
        if self._deleted_at:
            raise DomainError("Cannot deactivate deleted service")
        if self._status == BaseStatus.INACTIVE:
            raise DomainError("Service is already inactive")
        self._status = BaseStatus.INACTIVE
        self._updated_at = utc_now()

    def archive(self) -> None:
        """Archive service"""
        if self._deleted_at:
            raise DomainError("Cannot archive deleted service")
        if self._status == BaseStatus.ARCHIVED:
            raise DomainError("Service is already archived")
        self._status = BaseStatus.ARCHIVED
        self._updated_at = utc_now()

    def restore(self) -> None:
        """Restore archived or soft-deleted service"""
        if self._deleted_at:
            raise DomainError("Cannot restore deleted service")
        # Check if service is already active and not deleted
        if self._status == BaseStatus.ACTIVE and self._deleted_at is None:
            raise DomainError("Service is already active and does not need restoration")
        # Restore soft-deleted service
        if self._deleted_at:
            self._deleted_at = None
        # Restore archived service
        if self._status == BaseStatus.ARCHIVED:
            self._status = BaseStatus.ACTIVE
        self._updated_at = utc_now()

    def update_name(self, name: str) -> None:
        """Update service name"""
        if not name:
            raise DomainError("Service name cannot be empty")
        if self._deleted_at:
            raise DomainError("Cannot update name for deleted service")
        self._name = name
        self._updated_at = utc_now()

    def update_description(self, description: str | None) -> None:
        """Update service description"""
        if self._deleted_at:
            raise DomainError("Cannot update description for deleted service")
        self._description = description
        self._updated_at = utc_now()

    def update_category(self, category: str | None) -> None:
        """Update service category"""
        if self._deleted_at:
            raise DomainError("Cannot update category for deleted service")
        self._category = category
        self._updated_at = utc_now()

    def update_duration(self, duration_minutes: int | None) -> None:
        """Update service duration"""
        if self._deleted_at:
            raise DomainError("Cannot update duration for deleted service")
        if duration_minutes is not None and duration_minutes <= 0:
            raise DomainError("Duration must be positive")
        self._duration_minutes = duration_minutes
        self._updated_at = utc_now()

    def update_group_settings(
        self, is_group_service: bool, max_participants: int | None = None
    ) -> None:
        """Update group service settings"""
        if self._deleted_at:
            raise DomainError("Cannot update group settings for deleted service")
        if is_group_service and max_participants is not None and max_participants <= 0:
            raise DomainError("Max participants must be positive for group services")
        self._is_group_service = is_group_service
        self._max_participants = max_participants
        self._updated_at = utc_now()

    def is_active(self) -> bool:
        """Check if service is operational"""
        return self._status == BaseStatus.ACTIVE and self._deleted_at is None

    # === Public Properties ===

    @property
    def id(self) -> ServiceId:
        return self._id

    @property
    def tenant_id(self) -> TenantId:
        return self._tenant_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str | None:
        return self._description

    @property
    def status(self) -> BaseStatus:
        return self._status

    @property
    def category(self) -> str | None:
        return self._category

    @property
    def duration_minutes(self) -> int | None:
        return self._duration_minutes

    @property
    def is_group_service(self) -> bool:
        return self._is_group_service

    @property
    def max_participants(self) -> int | None:
        return self._max_participants

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def deleted_at(self) -> datetime | None:
        return self._deleted_at

    @property
    def events(self) -> list[DomainEvent]:
        return list(self._events)

    def clear_events(self) -> None:
        self._events.clear()
