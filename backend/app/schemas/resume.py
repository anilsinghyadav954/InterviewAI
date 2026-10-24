from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class JobMatchInfo(BaseModel):
    percentage: int = Field(..., ge=0, le=100, description="Match percentage against target role")
    match_level: str = Field(..., description="Strong Match, Moderate Match, or Potential Match")
    summary: str = Field(..., description="Concise assessment of candidate alignment with role")


class ResumeAnalysisResponse(BaseModel):
    id: str
    user_id: str
    filename: str
    job_role: str
    overall_score: int = Field(..., ge=0, le=100)
    ats_score: int = Field(..., ge=0, le=100)
    detected_skills: List[str] = []
    missing_skills: List[str] = []
    strengths: List[str] = []
    weaknesses: List[str] = []
    job_match: JobMatchInfo
    recommendations: List[str] = []
    extracted_summary: Optional[str] = ""
    created_at: datetime


class ResumeHistoryItem(BaseModel):
    id: str
    filename: str
    job_role: str
    overall_score: int
    ats_score: int
    created_at: datetime
