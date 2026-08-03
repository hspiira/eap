from dataclasses import dataclass


@dataclass(frozen=True)
class TenantSettings:
    """
    Represents tenant settings.

    Attributes:
    - max_users: Maximum number of users
    - max_clients: Maximum number of clients
    - features_enabled: Enabled features
    - custom_branding: Whether custom branding is enabled
    """

    max_users: int
    max_clients: int
    features_enabled: tuple[str, ...]
    custom_branding: bool = False

    def __post_init__(self) -> None:
        if self.max_users < 0:
            raise ValueError("Max users must be greater than zero")
        if self.max_clients < 0:
            raise ValueError("Max clients must be greater than zero")

    def allows_more_users(self, current_count: int) -> bool:
        return current_count < self.max_users

    def allows_more_clients(self, current_count: int) -> bool:
        return current_count < self.max_clients
