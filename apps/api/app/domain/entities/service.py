"""
Service Entity (Aggregate Root)

Represents a service offering in the EAP platform.
Examples: Individual Counseling, Group Therapy, Crisis Intervention, etc.
"""

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.enums import BaseStatus, ServiceCategory
from app.domain.events import DomainEvent
from app.domain.exceptions import DomainError
from app.domain.value_objects.core import ServiceId, TenantId
from app.shared.utils.datetime import utc_now


@dataclass
class ServiceEntity:
    # Required fields (no defaults)
    id: ServiceId
    tenant_id: TenantId
    name: str
    description: str | None
    status: BaseStatus
    created_at: datetime
    updated_at: datetime

    # Optional fields (with defaults)
    category: ServiceCategory | None = None
    duration_minutes: int | None = None
    is_group_service: bool = False
    max_participants: int | None = None
    deleted_at: datetime | None = None
    events: list[DomainEvent] = field(default_factory=list[DomainEvent])

    def activate(self) -> None:
        """Activate service for use"""
        if self.deleted_at:
            raise DomainError("Cannot activate deleted service")
        if self.status == BaseStatus.ACTIVE:
            raise DomainError("Service is already active")
        self.status = BaseStatus.ACTIVE
        self.updated_at = utc_now()

    def deactivate(self) -> None:
        """Deactivate service"""
        if self.deleted_at:
            raise DomainError("Cannot deactivate deleted service")
        if self.status == BaseStatus.INACTIVE:
            raise DomainError("Service is already inactive")
        self.status = BaseStatus.INACTIVE
        self.updated_at = utc_now()

    def archive(self) -> None:
        """Archive service"""
        if self.deleted_at:
            raise DomainError("Cannot archive deleted service")
        if self.status == BaseStatus.ARCHIVED:
            raise DomainError("Service is already archived")
        self.status = BaseStatus.ARCHIVED
        self.updated_at = utc_now()

    def restore(self) -> None:
        """Restore archived or soft-deleted service.

        Only restores from ARCHIVED to ACTIVE. Deleted services (DELETED status)
        cannot be restored as deletion is permanent.
        """
        if self.status == BaseStatus.ACTIVE and not self.deleted_at:
            raise DomainError("Service is already active and does not need restoration")
        if self.deleted_at:
            self.deleted_at = None
            self.status = BaseStatus.ACTIVE
        if self.status == BaseStatus.ARCHIVED:
            self.status = BaseStatus.ACTIVE
        self.updated_at = utc_now()

    def update_name(self, name: str) -> None:
        """Update service name"""
        if not name:
            raise DomainError("Service name cannot be empty")
        if self.deleted_at:
            raise DomainError("Cannot update name for deleted service")
        self.name = name
        self.updated_at = utc_now()

    def update_description(self, description: str | None) -> None:
        """Update service description"""
        if self.deleted_at:
            raise DomainError("Cannot update description for deleted service")
        self.description = description
        self.updated_at = utc_now()

    def update_category(self, category: ServiceCategory | None) -> None:
        """Update the programme category this service is delivered under."""
        if self.deleted_at:
            raise DomainError("Cannot update category for deleted service")
        self.category = category
        self.updated_at = utc_now()

    def update_duration(self, duration_minutes: int | None) -> None:
        """Update service duration"""
        if self.deleted_at:
            raise DomainError("Cannot update duration for deleted service")
        if duration_minutes is not None and duration_minutes <= 0:
            raise DomainError("Duration must be positive")
        self.duration_minutes = duration_minutes
        self.updated_at = utc_now()

    def update_group_settings(
        self, *, is_group_service: bool, max_participants: int | None = None
    ) -> None:
        """Update group service settings"""
        if self.deleted_at:
            raise DomainError("Cannot update group settings for deleted service")
        if is_group_service and max_participants is not None and max_participants <= 0:
            raise DomainError("Max participants must be positive for group services")
        self.is_group_service = is_group_service
        self.max_participants = max_participants
        self.updated_at = utc_now()

    def is_active(self) -> bool:
        """Check if service is operational"""
        return self.status == BaseStatus.ACTIVE and self.deleted_at is None

    # === Public Properties ===

    def clear_events(self) -> None:
        self.events.clear()
