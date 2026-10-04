"""
NexPath Event-Driven Architecture Package.
Asynchronous EventBus for pipeline decoupling.
"""

from app.events.bus import event_bus, EventBus
from app.events.handlers import register_event_handlers

__all__ = [
    "event_bus",
    "EventBus",
    "register_event_handlers"
]
