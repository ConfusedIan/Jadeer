from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import date


def _validate_https_url(v: Optional[str]) -> Optional[str]:
    if v is not None and not v.startswith("https://"):
        raise ValueError("credential_url must start with https://")
    return v


class CertificateCreate(BaseModel):
    supported_cert_id: Optional[int] = None
    certificate_name: str
    issuer: str
    issue_date: Optional[date] = None
    credential_url: Optional[str] = None

    @field_validator("credential_url")
    @classmethod
    def credential_url_must_be_https(cls, v: Optional[str]) -> Optional[str]:
        return _validate_https_url(v)


class CertificateUpdate(BaseModel):
    supported_cert_id: Optional[int] = None
    certificate_name: Optional[str] = None
    issuer: Optional[str] = None
    issue_date: Optional[date] = None
    credential_url: Optional[str] = None

    @field_validator("credential_url")
    @classmethod
    def credential_url_must_be_https(cls, v: Optional[str]) -> Optional[str]:
        return _validate_https_url(v)