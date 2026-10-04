from datetime import datetime, timezone
from typing import Dict, Any, List


class ActivityEngine:
    """Logs candidate timeline events."""

    def format_event(self, event_type: str, title: str, description: str) -> Dict[str, Any]:
        return {
            "event_type": event_type,
            "title": title,
            "description": description,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


activity_engine = ActivityEngine()
