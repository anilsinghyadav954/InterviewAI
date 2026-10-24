from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.schemas.interview import AnswerEvaluationResponse, QuestionItem


class VoiceSessionStartRequest(BaseModel):
    question_set_id: str = Field(..., description="ID of the interview question set")

    @field_validator("question_set_id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("question_set_id cannot be empty")
        return cleaned


class VoiceAnswerSubmitRequest(BaseModel):
    session_id: str = Field(..., description="Active voice session ID")
    question_number: int = Field(..., ge=1, description="Question number (1-based)")
    transcript: str = Field(..., description="Candidate transcribed voice answer")

    @field_validator("transcript")
    @classmethod
    def validate_transcript(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Transcript cannot be empty. Please record or speak an answer before submitting.")
        return cleaned


class VoiceAnswerItem(BaseModel):
    question_number: int
    transcript: str
    submitted_at: datetime
    evaluation_id: Optional[str] = None
    overall_score: Optional[float] = None


class VoiceSessionResponse(BaseModel):
    session_id: str
    question_set_id: str
    total_questions: int
    status: str  # "active" | "completed" | "abandoned"
    current_question: int = 1
    target_role: Optional[str] = None
    interview_type: Optional[str] = None
    difficulty: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    answers: List[VoiceAnswerItem] = Field(default_factory=list)
    questions: Optional[List[Dict[str, Any]]] = None
    mode: str = "Voice"


class VoiceAnswerResponse(BaseModel):
    question_number: int
    transcript: str
    evaluation: AnswerEvaluationResponse
    is_last_question: bool = False
    session_status: str = "active"


class VoiceHistoryItem(BaseModel):
    id: str
    session_id: str
    role: str
    interview_type: str
    difficulty: str
    score: Optional[float] = None
    date: datetime
    questions_count: int
    status: str
    mode: str = "Voice"


class VoiceNextQuestionRequest(BaseModel):
    session_id: str = Field(..., description="Active voice session ID")
    question_number: int = Field(..., ge=1, description="Question number currently being answered (1-based)")
    transcript: str = Field(..., description="Candidate transcribed voice answer")

    @field_validator("transcript")
    @classmethod
    def validate_transcript(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Transcript cannot be empty. Please record or speak an answer before submitting.")
        return cleaned


class VoiceNextQuestionResponse(BaseModel):
    session_id: str
    question_number: int
    interview_complete: bool = False
    next_question: Optional[QuestionItem] = None
    acknowledgement: Optional[str] = None
    reason: Optional[str] = None
    evaluation: Optional[AnswerEvaluationResponse] = None
    is_last_question: bool = False
    session_status: str = "active"

