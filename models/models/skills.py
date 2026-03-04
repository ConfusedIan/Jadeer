from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID

class SkillCreate(BaseModel):
    skill_id: Optional[int] = None
    custom_skill_name: Optional[str] = Field(default=None, min_length=1)
    category: Optional[str] = None
    score: Optional[float] = Field(default=None, ge=0, le=100)

class SkillUpdate(BaseModel):
    category: Optional[str] = None
    score: Optional[float] = Field(default=None, ge=0, le=100)