from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field, ConfigDict, model_validator


# Auth
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, json_schema_extra={"example": "Password123!"})


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    target_job_role: Optional[str] = "AI Engineer"
    preferred_ai_model: Optional[str] = "gemini-2.5-flash"
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UserAdminItem(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Resume
class ContactInfo(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    location: Optional[str] = None


class EducationItem(BaseModel):
    degree: str
    institution: str
    year: Optional[str] = None
    gpa: Optional[str] = None


class ExperienceItem(BaseModel):
    title: str
    company: str
    duration: Optional[str] = None
    description: List[str] = Field(default_factory=list)


class ProjectItem(BaseModel):
    title: str
    technologies: List[str] = Field(default_factory=list)
    description: str


class ParsedResumeSchema(BaseModel):
    contact: ContactInfo
    technical_skills: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    tools_frameworks: List[str] = Field(default_factory=list)
    education: List[EducationItem] = Field(default_factory=list)
    experience: List[ExperienceItem] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    projects: List[ProjectItem] = Field(default_factory=list)


class ResumeResponse(BaseModel):
    id: int
    user_id: int
    file_name: str
    file_type: str
    parsed_data: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Analysis
class AnalysisRequest(BaseModel):
    resume_id: int
    field: str = Field(..., json_schema_extra={"example": "Software Development"})
    job_role: str = Field(..., json_schema_extra={"example": "AI Engineer"})
    experience_level: str = Field(..., json_schema_extra={"example": "Mid-Level"})


class CareerReportResponse(BaseModel):
    id: int
    user_id: int
    resume_id: Optional[int] = None
    field: str
    job_role: str
    experience_level: str
    resume_score: float
    ats_score: float
    readiness_score: float
    nex_score: Optional[float] = 89.0
    analysis_data: Optional[Dict[str, Any]] = None
    gap_analysis: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResearchRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    resume_id: int = Field(gt=0)
    job_role: str = Field(min_length=2, max_length=100)
    location: str = Field(min_length=2, max_length=150)
    experience_level: str = Field(min_length=2, max_length=50)
    remote: bool = False
    company: str = Field(default="", max_length=150)
    job_url: str = Field(default="", max_length=2000)
    job_description: str = Field(default="", max_length=16000)
    search_market: bool = True
    refresh: bool = False

    @model_validator(mode="after")
    def require_source(self):
        if not self.search_market and not (self.job_url or self.job_description):
            raise ValueError("Add a company job URL or paste its job description, or enable market research.")
        if self.job_description and len(self.job_description) < 80:
            raise ValueError("Paste the full job description (at least 80 characters).")
        return self


# Roadmap & Projects
class RoadmapTask(BaseModel):
    id: str
    task_name: str
    is_completed: bool = False


class RoadmapMilestone(BaseModel):
    week_number: int
    title: str
    focus_topic: str
    resources: List[str] = Field(default_factory=list)
    tasks: List[RoadmapTask] = Field(default_factory=list)
    estimated_hours: int = 10


class RoadmapResponse(BaseModel):
    report_id: int
    job_role: str
    total_weeks: int
    milestones: List[RoadmapMilestone] = Field(default_factory=list)


class ProjectRecommendation(BaseModel):
    id: str
    title: str
    description: str
    required_skills: List[str]
    learning_outcomes: List[str]
    difficulty: str
    estimated_time: str


# Chat Assistant
class ChatMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000, json_schema_extra={"example": "How can I prepare for a Senior AI Engineer interview?"})


class ChatMessageResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    role: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatHistoryResponse(BaseModel):
    messages: List[ChatMessageResponse] = Field(default_factory=list)


# Interview Simulator
class StartInterviewRequest(BaseModel):
    interview_type: str = Field("Technical", json_schema_extra={"example": "Technical"})
    target_role: str = Field("AI Engineer", json_schema_extra={"example": "AI Engineer"})


class InterviewQuestionItem(BaseModel):
    question: str
    answer: Optional[str] = None
    evaluation: Optional[Dict[str, Any]] = None


class InterviewSessionResponse(BaseModel):
    id: int
    user_id: int
    interview_type: str
    target_role: str
    overall_score: float
    history: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EvaluateAnswerRequest(BaseModel):
    session_id: int
    question: str
    user_answer: str


class AnswerFeedbackResponse(BaseModel):
    question: str
    user_answer: str
    score: float
    strengths: List[str] = Field(default_factory=list)
    mistakes: List[str] = Field(default_factory=list)
    suggested_answer: str
    next_question: Optional[str] = None


# Dashboard Overview
class RecentReportSummary(BaseModel):
    id: int
    job_role: str
    experience_level: str
    ats_score: float
    created_at: datetime


class DashboardOverviewResponse(BaseModel):
    ats_score: float
    resume_score: float
    readiness_score: float
    interview_score: float
    learning_progress_percent: float
    completed_projects_count: int
    resumes_count: int
    reports_count: int
    recent_reports: List[RecentReportSummary] = Field(default_factory=list)


# Admin Special Access
class AdminStatsResponse(BaseModel):
    total_users: int
    total_resumes: int
    total_reports: int
    total_interviews: int
    active_admins: int


class HealthCheck(BaseModel):
    status: str
    project: str
    version: str
