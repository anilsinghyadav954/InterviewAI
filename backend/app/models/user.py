from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field


class UserModel(BaseModel):
    """Internal MongoDB document model for a User."""
    id: Optional[str] = Field(default=None, alias="_id")
    full_name: str
    email: str
    password_hash: str
    college: Optional[str] = "Stanford University"
    degree: Optional[str] = "Bachelor of Science"
    branch: Optional[str] = "Computer Science & Engineering"
    graduation_year: Optional[str] = "2025"
    skills: List[str] = Field(default_factory=lambda: [
        "JavaScript", "TypeScript", "React", "Node.js", "Python", "Tailwind CSS"
    ])
    target_role: Optional[str] = "Full Stack Developer"
    profile_image: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }
