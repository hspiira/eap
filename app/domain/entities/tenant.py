"""
Tenant Entity

Represents an isolated organizational boundary within the EAP platform.

Responsibilities:
- Own users and domain data
- Enforce data isolation
- Control tenant lifecycle (active, suspended)
"""

from dataclasses import dataclass, field
from datetime import datetime
from app.domain.value_objects.core import TenantCode, TenantId, TenantSettings
from app.domain.enums import SubscriptionTier, TenantStatus
from app.domain.events import DomainEvent, TenantActivated, TenantSuspended, TenantTerminated
from app.domain.exceptions import DomainError, InvariantViolation
from app.shared.utils.datetime import utc_now


@dataclass
class TenantEntity:
    id: TenantId
    name: str
    code: TenantCode
    status: TenantStatus
    settings: TenantSettings
    subscription_tier: SubscriptionTier
    deleted_at: datetime | None = None
    updated_at: datetime | None = None
    azure_tenant_id: str | None = None
    azure_sso_enabled: bool = False

    # Domain Events
    events: list[DomainEvent] = field(default_factory=list[DomainEvent])

    def __post_init__(self) -> None:
        self._ensure_invariants()

    def activate(self) -> None:
        """Activate tenant for operation"""
        if self.status == TenantStatus.TERMINATED:
            raise DomainError("Cannot activate terminated tenant")
        if self.status == TenantStatus.ACTIVE and self.deleted_at is None:
            raise DomainError("Tenant is already active")
        self.status = TenantStatus.ACTIVE
        if self.deleted_at:
            self.deleted_at = None
        self.updated_at = utc_now()
        self.events.append(TenantActivated(occurred_at=utc_now(), tenant_id=self.id))
    
    def suspend(self, reason: str) -> None:
        """Suspend tenant (e.g., payment issues)"""
        if not reason:
            raise DomainError("Suspension requires reason")
        if self.status == TenantStatus.TERMINATED:
            raise DomainError("Cannot suspend terminated tenant")
        if self.status == TenantStatus.SUSPENDED:
            raise DomainError("Tenant is already suspended")
        self.status = TenantStatus.SUSPENDED
        self.updated_at = utc_now()
        self.events.append(TenantSuspended(occurred_at=utc_now(), tenant_id=self.id, reason=reason))
    
    def terminate(self, reason: str) -> None:
        """Permanently terminate tenant"""
        if not reason:
            raise DomainError("Termination requires reason")
        if self.status == TenantStatus.TERMINATED:
            raise DomainError("Tenant is already terminated")
        self.status = TenantStatus.TERMINATED
        self.deleted_at = utc_now()
        self.updated_at = utc_now()
        self.events.append(TenantTerminated(occurred_at=utc_now(), tenant_id=self.id, reason=reason))
    
    def update_settings(
        self,
        *,
        max_users: int | None = None,
        max_clients: int | None = None,
        features_enabled: tuple[str, ...] | None = None,
        custom_branding: bool | None = None,
    ) -> None:
        """Replace any provided settings fields; unspecified fields are kept."""
        if self.status == TenantStatus.TERMINATED:
            raise DomainError("Cannot update settings for terminated tenant")
        current = self.settings
        self.settings = TenantSettings(
            max_users=max_users if max_users is not None else current.max_users,
            max_clients=max_clients if max_clients is not None else current.max_clients,
            features_enabled=features_enabled if features_enabled is not None else current.features_enabled,
            custom_branding=custom_branding if custom_branding is not None else current.custom_branding,
        )
        self.updated_at = utc_now()
    
    def update_name(self, name: str) -> None:
        """Update tenant name"""
        if not name:
            raise DomainError("Tenant name cannot be empty")
        if self.status == TenantStatus.TERMINATED:
            raise DomainError("Cannot update name for terminated tenant")
        self.name = name
        self.updated_at = utc_now()
    
    def update_subscription_tier(self, tier: SubscriptionTier) -> None:
        """Update subscription tier"""
        if self.status == TenantStatus.TERMINATED:
            raise DomainError("Cannot update subscription tier for terminated tenant")
        self.subscription_tier = tier
        self.updated_at = utc_now()
    
    def archive(self) -> None:
        """Archive tenant (softer than terminate)"""
        if self.status == TenantStatus.TERMINATED:
            raise DomainError("Cannot archive terminated tenant")
        if self.status == TenantStatus.ARCHIVED:
            raise DomainError("Tenant is already archived")
        self.status = TenantStatus.ARCHIVED
        self.updated_at = utc_now()
    
    def restore(self) -> None:
        """Restore archived or soft-deleted tenant.
        
        Only restores from ARCHIVED to ACTIVE. Terminated tenants (TERMINATED status)
        cannot be restored as termination is permanent.
        """
        if self.status == TenantStatus.TERMINATED:
            raise DomainError("Cannot restore terminated tenant")
        if self.status not in (TenantStatus.ARCHIVED, TenantStatus.ACTIVE) and self.deleted_at is None:
            raise DomainError("Tenant is not archived or deleted")
        if self.status == TenantStatus.ACTIVE and not self.deleted_at:
            raise DomainError("Tenant is already active and does not need restoration")
        if self.deleted_at:
            self.deleted_at = None
        if self.status == TenantStatus.ARCHIVED:
            self.status = TenantStatus.ACTIVE
        self.updated_at = utc_now()
    
    def is_active(self) -> bool:
        """Check if tenant is operational"""
        return self.status == TenantStatus.ACTIVE and self.deleted_at is None
    
    def can_create_users(self, current_user_count: int) -> bool:
        """Check if tenant can create new users based on subscription and settings"""
        return self.is_active() and self.settings.allows_more_users(current_user_count)

    def can_create_clients(self, current_client_count: int) -> bool:
        """Check if tenant can create new clients based on settings"""
        return self.is_active() and self.settings.allows_more_clients(current_client_count)

    def configure_azure_sso(self, azure_tenant_id: str, enabled: bool = True) -> None:
        """Set or update Azure AD SSO configuration for this tenant."""
        if self.status == TenantStatus.TERMINATED:
            raise DomainError("Cannot configure SSO for terminated tenant")
        if not azure_tenant_id or not azure_tenant_id.strip():
            raise DomainError("Azure tenant ID cannot be empty")
        self.azure_tenant_id = azure_tenant_id.strip()
        self.azure_sso_enabled = enabled
        self.updated_at = utc_now()

    def disable_azure_sso(self) -> None:
        """Disable Azure SSO without removing the stored tenant ID."""
        self.azure_sso_enabled = False
        self.updated_at = utc_now()
    
    # === Invariants ===
    
    def collect_events(self) -> list[DomainEvent]:
        """
        Collect and clear pending domain events.
        
        Returns:
            List of domain events that occurred
        """
        events = self.events.copy()
        self.events.clear()
        return events
    
    def _ensure_invariants(self) -> None:
        """Ensure tenant invariants are met"""
        if not self.code:
            raise InvariantViolation("Tenant must have a code")
        if not self.name:
            raise InvariantViolation("Tenant must have a name")

    # === Public Properties ===

    def clear_events(self) -> None:
        self.events.clear()