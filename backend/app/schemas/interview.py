from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime

VALID_ROLES = [
    "Software Developer",
    "Frontend Developer",
    "Backend Developer",
    "Full Stack Developer",
    "Python Developer",
    "Java Developer",
    "Data Analyst",
    "AI/ML Engineer",
]

VALID_TYPES = ["Technical", "HR", "Mixed"]
VALID_DIFFICULTIES = ["Beginner", "Intermediate", "Advanced"]
VALID_QUESTION_COUNTS = [5, 10, 15]

VALID_CATEGORIES = [
    "Technical",
    "Coding",
    "Database",
    "Web Development",
    "Programming",
    "System Design",
    "Problem Solving",
    "HR",
    "Behavioral",
    "Situational",
]


class QuestionGenerationRequest(BaseModel):
    target_role: str = Field(..., description="Target job role")
    interview_type: str = Field(..., description="Technical, HR, or Mixed")
    difficulty: str = Field(..., description="Beginner, Intermediate, or Advanced")
    number_of_questions: int = Field(..., description="5, 10, or 15 questions")

    @field_validator("target_role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        cleaned = v.strip()
        if cleaned not in VALID_ROLES:
            raise ValueError(f"Target role must be one of: {', '.join(VALID_ROLES)}")
        return cleaned

    @field_validator("interview_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        cleaned = v.strip()
        if cleaned not in VALID_TYPES:
            raise ValueError(f"Interview type must be one of: {', '.join(VALID_TYPES)}")
        return cleaned

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, v: str) -> str:
        cleaned = v.strip()
        if cleaned not in VALID_DIFFICULTIES:
            raise ValueError(f"Difficulty must be one of: {', '.join(VALID_DIFFICULTIES)}")
        return cleaned

    @field_validator("number_of_questions")
    @classmethod
    def validate_count(cls, v: int) -> int:
        if v not in VALID_QUESTION_COUNTS:
            raise ValueError(f"Number of questions must be one of: {VALID_QUESTION_COUNTS}")
        return v


class QuestionItem(BaseModel):
    question_number: int = Field(..., ge=1)
    question: str = Field(..., min_length=5)
    category: str = Field(..., description="Category of the question")
    topic: str = Field(..., min_length=2)
    difficulty: str = Field(..., description="Difficulty level")
    expected_focus: List[str] = Field(default_factory=list, description="Key concepts candidate should cover")

    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Question cannot be empty")
        return cleaned

    @field_validator("topic")
    @classmethod
    def validate_topic(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Topic cannot be empty")
        return cleaned

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        cleaned = v.strip()
        if cleaned in VALID_CATEGORIES:
            return cleaned
        # Safe normalization for AI aliases
        lower = cleaned.lower()
        if any(term in lower for term in ["code", "algo", "implement", "program"]):
            return "Coding"
        if any(term in lower for term in ["db", "data", "sql", "mongo"]):
            return "Database"
        if any(term in lower for term in ["web", "front", "react", "html", "css", "api"]):
            return "Web Development"
        if any(term in lower for term in ["arch", "system", "design", "scale"]):
            return "System Design"
        if any(term in lower for term in ["problem", "debug", "troubleshoot"]):
            return "Problem Solving"
        if any(term in lower for term in ["behavior", "team", "conflict", "work"]):
            return "Behavioral"
        if any(term in lower for term in ["situation", "scenario", "deadline"]):
            return "Situational"
        if any(term in lower for term in ["hr", "culture", "career", "leadership", "intro"]):
            return "HR"
        return "Technical"

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, v: str) -> str:
        cleaned = v.strip()
        if cleaned not in VALID_DIFFICULTIES:
            return "Intermediate"
        return cleaned

    @field_validator("expected_focus")
    @classmethod
    def validate_expected_focus(cls, v: List[str]) -> List[str]:
        if not isinstance(v, list):
            return ["Core principles", "Practical application"]
        cleaned = [item.strip() for item in v if isinstance(item, str) and item.strip()]
        return cleaned if cleaned else ["Core principles", "Practical application"]


class QuestionSetResponse(BaseModel):
    id: str
    user_id: str
    target_role: str
    interview_type: str
    difficulty: str
    number_of_questions: int
    resume_based: bool
    questions: List[QuestionItem]
    created_at: datetime


class QuestionHistoryItem(BaseModel):
    id: str
    target_role: str
    interview_type: str
    difficulty: str
    number_of_questions: int
    resume_based: bool
    created_at: datetime
    evaluated_questions: Optional[int] = 0
    overall_score: Optional[float] = None
    completion_rate: Optional[float] = None
    mode: Optional[str] = "Text"


# ==============================================================================
# Phase 5: AI Answer Evaluation & Interview Report Schemas
# ==============================================================================

class AnswerEvaluationRequest(BaseModel):
    question_set_id: str = Field(..., description="ID of the stored interview question set")
    question_number: int = Field(..., ge=1, description="Question number (1-based)")
    candidate_answer: str = Field(..., description="Candidate's submitted answer text")
    # Optional client-passed metadata (backend verifies against actual DB doc)
    question: Optional[str] = None
    category: Optional[str] = None
    topic: Optional[str] = None
    difficulty: Optional[str] = None
    expected_focus: Optional[List[str]] = None

    @field_validator("candidate_answer")
    @classmethod
    def validate_answer(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Please provide an answer before evaluating.")
        return cleaned


class AnswerEvaluationResponse(BaseModel):
    id: str
    question_set_id: str
    question_number: int
    candidate_answer: str
    overall_score: float = Field(..., ge=0.0, le=10.0, description="Overall score 0-10")
    technical_accuracy: Optional[float] = Field(None, ge=0.0, le=10.0, description="Technical accuracy 0-10")
    relevance: float = Field(..., ge=0.0, le=10.0, description="Relevance 0-10")
    completeness: float = Field(..., ge=0.0, le=10.0, description="Completeness 0-10")
    clarity: float = Field(..., ge=0.0, le=10.0, description="Clarity 0-10")
    communication: float = Field(..., ge=0.0, le=10.0, description="Communication 0-10")
    strengths: List[str] = Field(default_factory=list, description="Demonstrated strengths")
    weaknesses: List[str] = Field(default_factory=list, description="Constructive weaknesses")
    missing_points: List[str] = Field(default_factory=list, description="Omitted expected concepts")
    improvement_suggestions: List[str] = Field(default_factory=list, description="Actionable improvement tips")
    model_answer_outline: str = Field("", description="Suggested outline for ideal response")
    summary: str = Field("", description="Interviewer professional summary")
    created_at: datetime
    updated_at: Optional[datetime] = None


class FinalInterviewReportResponse(BaseModel):
    question_set_id: str
    target_role: str
    interview_type: str
    difficulty: str
    total_questions: int
    answered_questions: int
    unanswered_questions: int
    evaluated_questions: int
    completion_rate: float
    overall_score: float
    score_percentage: float
    average_technical_accuracy: Optional[float] = None
    average_relevance: float
    average_completeness: float
    average_clarity: float
    average_communication: float
    strong_areas: List[str]
    weak_areas: List[str]
    top_improvements: List[str]
    evaluations: List[AnswerEvaluationResponse]
    created_at: datetime


class InterviewDashboardMetricsResponse(BaseModel):
    total_interviews_created: int
    total_evaluations_count: int
    completed_interviews_count: int
    average_score: float
    average_score_percentage: float
    has_completed_interviews: bool

