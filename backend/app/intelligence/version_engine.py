from typing import Dict, Any


class ResumeVersionEngine:
    """Tracks resume versions and delta changes."""

    def compute_delta(self, old_parsed: Dict[str, Any], new_parsed: Dict[str, Any]) -> Dict[str, Any]:
        old_skills = set(old_parsed.get("technical_skills", []))
        new_skills = set(new_parsed.get("technical_skills", []))

        added = list(new_skills - old_skills)
        removed = list(old_skills - new_skills)

        return {
            "skills_added": added,
            "skills_removed": removed,
            "net_impact": f"+{len(added) * 2.0}% ATS Score Improvement" if added else "No significant change"
        }


version_engine = ResumeVersionEngine()
