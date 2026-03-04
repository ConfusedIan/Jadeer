from pydantic import BaseModel
from typing import Optional
from datetime import date

class ExperienceCreate(BaseModel):
    job_title: str
    company: str
    start_date: date
    end_date: Optional[date] = None
    description: Optional[str] = None

class ExperienceUpdate(BaseModel):
    job_title: Optional[str] = None
    company: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = None