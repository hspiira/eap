"""Event-bus dependency."""

from app.shared.events.event_bus import EventBus, event_bus


def get_event_bus() -> EventBus:
    """
    Dependency for getting the event bus.

    Returns the global event bus instance.

    Returns:
        EventBus instance
    """
    return event_bus
