import logging
from typing import Dict, Any
from app.events.bus import event_bus

logger = logging.getLogger(__name__)


def handle_resume_uploaded(payload: Dict[str, Any]):
    logger.info(f"[Event Handler] ResumeUploaded: Session UUID {payload.get('session_uuid')}")


def handle_career_profile_created(payload: Dict[str, Any]):
    logger.info(f"[Event Handler] CareerProfileCreated for User ID {payload.get('user_id')}")


def register_event_handlers():
    event_bus.subscribe("ResumeUploaded", handle_resume_uploaded)
    event_bus.subscribe("CareerProfileCreated", handle_career_profile_created)
    logger.info("Registered all domain event handlers.")
