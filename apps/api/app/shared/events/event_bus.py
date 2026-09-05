"""
Event Bus

Simple in-process event bus for publishing and subscribing to domain events.

In-process limits:
- Events are delivered only within this process; multiple app instances do not
  share events unless an external backend (e.g. Redis Pub/Sub) is used.
- Event history is in-memory and bounded by max_history (default 1000); no
  durability across restarts.
- Handlers run asynchronously in the same process; slow handlers can delay
  publish() and affect request latency if publish is called from request path.

Optional backend (future): To support multi-instance or durable events, add an
optional backend (e.g. Redis Pub/Sub or a queue) that implements the same
publish/subscribe contract. Keep the existing in-process bus for local
handlers and optionally fan-out to the backend on publish so existing
handlers remain compatible.
"""

import logging
from collections import defaultdict
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.domain.events import DomainEvent

logger = logging.getLogger(__name__)

# Type alias for event handlers
EventHandler = Callable[[DomainEvent], Coroutine[Any, Any, None]]


@dataclass
class EventSubscription:
    """Represents a subscription to an event type."""

    event_type: type[DomainEvent]
    handler: EventHandler
    handler_name: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class EventBus:
    """
    Simple in-process event bus for domain events.

    Features:
    - Subscribe handlers to specific event types
    - Publish events to all subscribed handlers
    - Async handler execution
    - Error isolation (one handler failure doesn't affect others)
    - Event history for debugging

    For production with multiple instances, consider:
    - Redis Pub/Sub
    - RabbitMQ
    - Apache Kafka
    - AWS SNS/SQS
    """

    def __init__(self, max_history: int = 1000):
        self._handlers: dict[type[DomainEvent], list[EventSubscription]] = defaultdict(list)
        self._history: list[tuple[DomainEvent, datetime]] = []
        self._max_history = max_history
        self._is_processing = False

    def subscribe(
        self,
        event_type: type[DomainEvent],
        handler: EventHandler,
        handler_name: str | None = None,
    ) -> None:
        """
        Subscribe a handler to an event type.

        Args:
            event_type: The type of event to subscribe to
            handler: Async function to handle the event
            handler_name: Optional name for logging/debugging
        """
        name = handler_name or handler.__name__
        subscription = EventSubscription(
            event_type=event_type,
            handler=handler,
            handler_name=name,
        )
        self._handlers[event_type].append(subscription)
        logger.debug(f"Subscribed handler '{name}' to {event_type.__name__}")

    def unsubscribe(
        self,
        event_type: type[DomainEvent],
        handler: EventHandler,
    ) -> bool:
        """
        Unsubscribe a handler from an event type.

        Args:
            event_type: The type of event
            handler: The handler to remove

        Returns:
            True if handler was found and removed, False otherwise
        """
        subscriptions = self._handlers.get(event_type, [])
        for i, sub in enumerate(subscriptions):
            if sub.handler == handler:
                subscriptions.pop(i)
                logger.debug(
                    f"Unsubscribed handler '{sub.handler_name}' from {event_type.__name__}"
                )
                return True
        return False

    async def publish(self, event: DomainEvent) -> list[Exception]:
        """
        Publish an event to all subscribed handlers.

        Args:
            event: The domain event to publish

        Returns:
            List of exceptions from failed handlers (empty if all succeeded)
        """
        event_type = type(event)
        subscriptions = self._handlers.get(event_type, [])

        # Also check for handlers subscribed to base DomainEvent
        base_subscriptions = self._handlers.get(DomainEvent, [])
        all_subscriptions = subscriptions + base_subscriptions

        if not all_subscriptions:
            logger.debug(f"No handlers for event {event_type.__name__}")
            return []

        # Record in history
        self._record_event(event)

        # Execute all handlers
        errors: list[Exception] = []

        for subscription in all_subscriptions:
            try:
                logger.debug(
                    f"Executing handler '{subscription.handler_name}' for {event_type.__name__}"
                )
                await subscription.handler(event)
            except Exception as e:
                logger.exception(
                    f"Handler '{subscription.handler_name}' failed for {event_type.__name__}: {e}"
                )
                errors.append(e)

        return errors

    async def publish_all(self, events: list[DomainEvent]) -> dict[DomainEvent, list[Exception]]:
        """
        Publish multiple events.

        Args:
            events: List of domain events to publish

        Returns:
            Dictionary mapping events to their handler errors
        """
        results: dict[DomainEvent, list[Exception]] = {}
        for event in events:
            errors = await self.publish(event)
            if errors:
                results[event] = errors
        return results

    def _record_event(self, event: DomainEvent) -> None:
        """Record event in history for debugging."""
        self._history.append((event, datetime.now(UTC)))

        # Trim history if needed
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history :]

    def get_history(
        self,
        event_type: type[DomainEvent] | None = None,
        limit: int = 100,
    ) -> list[tuple[DomainEvent, datetime]]:
        """
        Get event history for debugging.

        Args:
            event_type: Optional filter by event type
            limit: Maximum number of events to return

        Returns:
            List of (event, published_at) tuples
        """
        if event_type:
            filtered = [(e, t) for e, t in self._history if isinstance(e, event_type)]
            return filtered[-limit:]
        return self._history[-limit:]

    def get_subscriptions(
        self,
        event_type: type[DomainEvent] | None = None,
    ) -> dict[str, list[str]]:
        """
        Get current subscriptions for debugging.

        Args:
            event_type: Optional filter by event type

        Returns:
            Dictionary mapping event type names to handler names
        """
        if event_type:
            subs = self._handlers.get(event_type, [])
            return {event_type.__name__: [s.handler_name for s in subs]}

        return {
            event_type.__name__: [s.handler_name for s in subs]
            for event_type, subs in self._handlers.items()
        }

    def clear_handlers(self) -> None:
        """Remove all handlers. Useful for testing."""
        self._handlers.clear()
        logger.debug("Cleared all event handlers")

    def clear_history(self) -> None:
        """Clear event history."""
        self._history.clear()


# Global event bus instance
event_bus = EventBus()


def on_event(event_type: type[DomainEvent]):
    """
    Decorator to register an event handler.

    Usage:
        @on_event(UserActivated)
        async def handle_user_activated(event: UserActivated):
            # Handle the event
            pass
    """

    def decorator(handler: EventHandler) -> EventHandler:
        event_bus.subscribe(event_type, handler)
        return handler

    return decorator
