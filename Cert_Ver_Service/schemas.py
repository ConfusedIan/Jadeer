from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from database import VerificationStatus
from uuid import UUID


class CertificateRequest(BaseModel):
    candidate_id     : UUID
    issuer_id        : str
    certificate_id   : str
    certificate_name : Optional[str] = None
    issue_date       : Optional[str] = None
    expiration_date  : Optional[str] = None
    first_name       : Optional[str] = None
    last_name        : Optional[str] = None


class CertificateResponse(BaseModel):
    certificate_id       : str
    candidate_id         : UUID
    issuer_id            : str
    certificate_name     : str
    status               : VerificationStatus
    verification_details : Optional[str] = None
    created_at           : datetime

    class Config:
        from_attributes = True
