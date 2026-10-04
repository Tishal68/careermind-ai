from typing import Dict, Any, List


class DecisionEngine:
    """Decision Engine generating justified, non-random priority action directives."""

    def determine_next_priority(self, missing_skills: List[str], target_role: str) -> Dict[str, Any]:
        top_gap = missing_skills[0] if missing_skills else "System Design"
        return {
            "title": f"Master {top_gap}",
            "directive_text": f"Your next highest-impact priority is {top_gap}. Resolving this will bridge your biggest skill gap for {target_role}.",
            "justification": f"Missing {top_gap} is currently holding your ATS & interview score back by -15 points.",
            "cta_text": f"Start {top_gap} Module →",
            "cta_action": "start_learning_module"
        }


decision_engine = DecisionEngine()
