from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class KernelState(BaseModel):
    user_id: int
    session_id: Optional[int] = None
    session_uuid: Optional[str] = None
    target_job_role: str = "AI Engineer"
    
    nex_score: float = 89.0
    ats_score: float = 92.0
    skills_match: float = 78.0
    interview_readiness: float = 74.0

    extracted_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    active_priority_directive: Dict[str, Any] = Field(default_factory=dict)
    roadmap_milestones: List[Dict[str, Any]] = Field(default_factory=list)
    project_recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    
    is_synchronized: bool = True
