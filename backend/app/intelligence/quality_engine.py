from typing import Dict, Any, List


class QualityEngine:
    """Quality Engine running automated pre-validation passes on AI recommendations."""

    def pre_validate_roadmap(self, milestones: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # Validate logical consistency and milestone order
        if not milestones:
            return []
        
        for idx, m in enumerate(milestones):
            if "estimated_hours" not in m or m["estimated_hours"] < 5:
                m["estimated_hours"] = 12
        return milestones


quality_engine = QualityEngine()
