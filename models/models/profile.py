from pydantic import BaseModel
from typing import Optional, List

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    linkedin_url: Optional[str] = None
    location: Optional[str] = None
    languages: Optional[List[str]] = None