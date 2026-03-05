from pydantic import BaseModel, field_validator
from typing import Optional, List

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    linkedin_url: Optional[str] = None
    location: Optional[str] = None
    languages: Optional[List[str]] = None

    @field_validator("linkedin_url")
    @classmethod
    def linkedin_url_must_be_https(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.startswith("https://"):
            raise ValueError("linkedin_url must start with https://")
        return v