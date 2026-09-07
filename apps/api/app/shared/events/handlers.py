"""
Default Event Handlers

Register handlers for domain events that need cross-cutting concerns
like logging, notifications, or audit trails.
"""

import logging
from typing import TYPE_CHECKING

from app.domain.events import (
    ClientActivated,
    ClientSuspended,
    ClientTerminated,
    ContractTerminated,
    DomainEvent,
    SessionCancelled,
    SessionCompleted,
    UserActivated,
    UserBanned,
    UserSuspended,
    UserTerminated,
)
from app.shared.events.event_bus import event_bus

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


# =============================================================================
# LOGGING HANDLERS
# =============================================================================


async def log_all_events(event: DomainEvent) -> None:
    """Log all domain events for debugging and audit purposes."""
    event_type = type(event).__name__
    logger.info(f"Domain Event: {event_type} at {event.occurred_at}")


async def log_user_events(
    event: UserActivated | UserSuspended | UserBanned | UserTerminated,
) -> None:
    """Log user lifecycle events."""
    event_type = type(event).__name__
    user_id = event.user_id.value

    if isinstance(event, (UserSuspended, UserBanned, UserTerminated)):
        logger.warning(f"{event_type}: User {user_id} - Reason: {event.reason}")
    else:
        logger.info(f"{event_type}: User {user_id}")


async def log_client_events(event: ClientActivated | ClientSuspended | ClientTerminated) -> None:
    """Log client lifecycle events."""
    event_type = type(event).__name__
    client_id = event.client_id.value

    if isinstance(event, (ClientSuspended, ClientTerminated)):
        logger.warning(f"{event_type}: Client {client_id} - Reason: {event.reason}")
    else:
        logger.info(f"{event_type}: Client {client_id}")


async def log_session_events(event: SessionCompleted | SessionCancelled) -> None:
    """Log session events."""
    event_type = type(event).__name__
    session_id = event.session_id.value

    if isinstance(event, SessionCancelled):
        logger.info(f"{event_type}: Session {session_id} - Reason: {event.reason}")
    elif isinstance(event, SessionCompleted):
        subject = event.member_id.value if event.member_id else "a company-wide audience"
        logger.info(f"{event_type}: Session {session_id} for {subject}")


# =============================================================================
# NOTIFICATION HANDLERS (PLACEHOLDER)
# =============================================================================


async def notify_user_suspended(event: UserSuspended) -> None:
    """
    Send notification when user is suspended.

    In production, this would integrate with:
    - Email service
    - Push notifications
    - Slack/Teams webhooks
    """
    logger.debug(f"Would notify user {event.user_id.value} of suspension")
    # TODO: Implement actual notification
    # await email_service.send(
    #     to=user.email,
    #     template="user_suspended",
    #     context={"reason": event.reason}
    # )


async def notify_contract_terminated(event: ContractTerminated) -> None:
    """
    Send notification when contract is terminated.

    In production, this would notify:
    - Client administrators
    - Account managers
    - Finance team
    """
    logger.debug(f"Would notify stakeholders of contract {event.contract_id.value} termination")
    # TODO: Implement actual notification


# =============================================================================
# ANALYTICS HANDLERS (PLACEHOLDER)
# =============================================================================


async def track_session_completion(event: SessionCompleted) -> None:
    """
    Track session completion for analytics.

    In production, this would:
    - Update KPI metrics
    - Send to analytics platform
    - Update utilization reports
    """
    member = event.member_id.value if event.member_id else None
    logger.debug(
        f"Would track session completion: session={event.session_id.value}, member={member}"
    )
    # TODO: Implement analytics tracking


# =============================================================================
# REGISTRATION
# =============================================================================


def register_default_handlers() -> None:
    """
    Register all default event handlers.

    Call this during application startup.
    """
    # Log all events (subscribing to base class catches everything)
    event_bus.subscribe(DomainEvent, log_all_events, "log_all_events")

    # User events
    event_bus.subscribe(UserActivated, log_user_events, "log_user_activated")
    event_bus.subscribe(UserSuspended, log_user_events, "log_user_suspended")
    event_bus.subscribe(UserSuspended, notify_user_suspended, "notify_user_suspended")
    event_bus.subscribe(UserBanned, log_user_events, "log_user_banned")
    event_bus.subscribe(UserTerminated, log_user_events, "log_user_terminated")

    # Client events
    event_bus.subscribe(ClientActivated, log_client_events, "log_client_activated")
    event_bus.subscribe(ClientSuspended, log_client_events, "log_client_suspended")
    event_bus.subscribe(ClientTerminated, log_client_events, "log_client_terminated")

    # Contract events
    event_bus.subscribe(
        ContractTerminated, notify_contract_terminated, "notify_contract_terminated"
    )

    # Session events
    event_bus.subscribe(SessionCompleted, log_session_events, "log_session_completed")
    event_bus.subscribe(SessionCompleted, track_session_completion, "track_session_completion")
    event_bus.subscribe(SessionCancelled, log_session_events, "log_session_cancelled")

    logger.info("Registered default event handlers")
