import logging
from typing import Dict, Any, List, Callable
from collections import defaultdict

logger = logging.getLogger(__name__)

EventHandler = Callable[[Dict[str, Any]], None]


class EventBus:
    """Asynchronous In-Memory EventBus for domain lifecycle events."""

    def __init__(self):
        self.subscribers: Dict[str, List[EventHandler]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: EventHandler):
        self.subscribers[event_type].append(handler)

    def publish(self, event_type: str, payload: Dict[str, Any]):
        logger.info(f"EventBus Published Event: {event_type}")
        handlers = self.subscribers.get(event_type, [])
        for handler in handlers:
            try:
                handler(payload)
            except Exception as e:
                logger.error(f"Error handling event {event_type}: {e}")


event_bus = EventBus()
