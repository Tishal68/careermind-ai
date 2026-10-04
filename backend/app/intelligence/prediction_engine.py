from typing import Dict, Any


class CareerPredictionEngine:
    """Estimates realistic candidate career readiness and velocity."""

    def predict_growth(self, current_nex_score: float, completed_milestones_count: int) -> Dict[str, Any]:
        projected_score = min(98.0, current_nex_score + (completed_milestones_count * 2.5))
        return {
            "current_score": current_nex_score,
            "projected_score_4_weeks": projected_score,
            "estimated_interview_callback_increase": f"+{int((projected_score - current_nex_score) * 1.8)}%",
            "readiness_forecast": "Top 10% Candidate" if projected_score >= 90 else "Competitive Candidate"
        }


prediction_engine = CareerPredictionEngine()
