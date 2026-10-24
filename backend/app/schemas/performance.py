from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class PerformanceOverviewResponse(BaseModel):
    interviews_completed: int = 0
    average_score: float = 0.0
    average_score_percentage: float = 0.0
    best_score: float = 0.0
    best_score_percentage: float = 0.0
    questions_evaluated: int = 0
    total_practice_sessions: int = 0
    latest_resume_score: float = 0.0
    technical_score: float = 0.0
    communication_score: float = 0.0
    relevance_score: float = 0.0
    completeness_score: float = 0.0
    clarity_score: float = 0.0
    has_data: bool = False


class PerformanceTrendPoint(BaseModel):
    interview_id: str
    date: str
    display_date: str
    score: float
    score_percentage: float
    role: str
    type: str
    interview_type: Optional[str] = None
    difficulty: str


class SkillPerformanceItem(BaseModel):
    skill: str
    score: float
    score_percentage: float
    questions: int
    questions_count: Optional[int] = None
    category: Optional[str] = None


class CategoryPerformanceItem(BaseModel):
    category: str
    score: float
    score_percentage: float
    questions: int
    questions_count: Optional[int] = None


class RolePerformanceItem(BaseModel):
    role: str
    score: float
    score_percentage: float
    interviews: int
    interviews_count: Optional[int] = None
    best_score: float
    average_score: Optional[float] = None


class InterviewTypePerformanceItem(BaseModel):
    type: str
    interviews_count: int
    interviews: Optional[int] = None
    average_score: float
    best_score: float
    score_percentage: Optional[float] = None


class PerformanceInsightsResponse(BaseModel):
    strengths: List[str] = Field(default_factory=list)
    weak_areas: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    resume_interview_comparison: Optional[Dict[str, Any]] = None


class RecentActivityItem(BaseModel):
    id: str
    activity_type: str  # "interview_completed", "question_generated", "resume_analyzed"
    title: str
    description: str
    date: datetime
    score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
