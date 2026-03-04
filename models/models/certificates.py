from pydantic import BaseModel
from typing import Optional
from datetime import date

class CertificateCreate(BaseModel):
    supported_cert_id: Optional[int] = None
    certificate_name: str
    issuer: str
    issue_date: Optional[date] = None
    credential_url: Optional[str] = None

class CertificateUpdate(BaseModel):
    supported_cert_id: Optional[int] = None
    certificate_name: Optional[str] = None
    issuer: Optional[str] = None
    issue_date: Optional[date] = None
    credential_url: Optional[str] = None
    is_verified: Optional[bool] = None