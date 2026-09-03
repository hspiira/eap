"""Event handling package."""

from app.shared.events.event_bus import EventBus, event_bus
from app.shared.events.handlers import register_default_handlers

__all__ = ["EventBus", "event_bus", "register_default_handlers"]
