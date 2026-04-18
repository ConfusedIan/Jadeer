from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import date


def _validate_https_url(v: Optional[str]) -> Optional[str]:
    if v is not None and not v.startswith("https://"):
        raise ValueError("credential_url must start with https://")
    return v


class CertificateCreate(BaseModel):
    certificate_id:   Optional[str] = None
    issuer_id:        Optional[str] = None
    issuer:           Optional[str] = None
    certificate_name: Optional[str] = None
    status:           Optional[str] = None
    issue_date:       Optional[str] = None
    expiration_date:  Optional[str] = None
    first_name:       Optional[str] = None
    last_name:        Optional[str] = None
    credential_url:   Optional[str] = None
    pdf_url:          Optional[str] = None

    @field_validator("credential_url")
    @classmethod
    def credential_url_must_be_https(cls, v: Optional[str]) -> Optional[str]:
        return _validate_https_url(v)

    @field_validator("pdf_url")
    @classmethod
    def pdf_url_must_be_https(cls, v: Optional[str]) -> Optional[str]:
        return _validate_https_url(v)


class CertificateUpdate(BaseModel):
    certificate_id:       Optional[str] = None
    issuer_id:            Optional[str] = None
    issuer:               Optional[str] = None
    certificate_name:     Optional[str] = None
    issue_date:           Optional[str] = None
    expiration_date:      Optional[str] = None
    first_name:           Optional[str] = None
    last_name:            Optional[str] = None
    credential_url:       Optional[str] = None
    pdf_url:              Optional[str] = None
    verification_details: Optional[str] = None

    @field_validator("credential_url")
    @classmethod
    def credential_url_must_be_https(cls, v: Optional[str]) -> Optional[str]:
        return _validate_https_url(v)

    @field_validator("pdf_url")
    @classmethod
    def pdf_url_must_be_https(cls, v: Optional[str]) -> Optional[str]:
        return _validate_https_url(v)