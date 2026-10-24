from pydantic import BaseModel, EmailStr
from typing import List, Optional


class UserProfileResponse(BaseModel):
    id: str
    full_name: str
    email: EmailStr
    college: Optional[str] = None
    degree: Optional[str] = None
    branch: Optional[str] = None
    graduation_year: Optional[str] = None
    skills: List[str] = []
    target_role: Optional[str] = None
    profile_image: Optional[str] = None


class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    college: Optional[str] = None
    degree: Optional[str] = None
    branch: Optional[str] = None
    graduation_year: Optional[str] = None
    skills: Optional[List[str]] = None
    target_role: Optional[str] = None
