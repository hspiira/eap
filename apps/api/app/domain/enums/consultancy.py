from enum import Enum


class EngagementStatus(str, Enum):
    """Cluster B consultancy engagement lifecycle (SAD §5.2.8)."""

    DRAFT = "Draft"
    ACTIVE = "Active"
    DELIVERED = "Delivered"
    INVOICED = "Invoiced"
    CLOSED = "Closed"


class DeliverableStatus(str, Enum):
    """Per-deliverable lifecycle within an Engagement."""

    PENDING = "Pending"
    IN_PROGRESS = "InProgress"
    DELIVERED = "Delivered"
    ACCEPTED = "Accepted"
