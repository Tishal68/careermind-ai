from typing import Dict, Any


class UserBehaviorEngine:
    """Tracks candidate study velocity, preferred hours, & weak topics."""

    def get_behavior_profile(self, user_id: int) -> Dict[str, Any]:
        return {
            "user_id": user_id,
            "completion_rate": "84%",
            "preferred_study_time": "Evening (18:00 - 21:00)",
            "learning_speed": "Fast (1.2x average)",
            "strongest_category": "Backend Microservices",
            "needs_focus": "System Design Trade-offs"
        }


behavior_engine = UserBehaviorEngine()
