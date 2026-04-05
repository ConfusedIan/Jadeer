from fastapi import APIRouter, Request, Header
from fastapi.responses import JSONResponse
from typing import Optional
from pydantic import BaseModel, UUID4
from services.service_registry import SERVICES
from utils.http_client import forward_request

router = APIRouter(prefix="/certificates", tags=["certificates"])

def _user_header(request: Request) -> dict:
    user = getattr(request.state, "user", {}) or {}
    return {"X-User-Id": user.get("user_id", "")}


class CertificateRequest(BaseModel):
    candidate_id: UUID4
    issuer_id: str
    certificate_id: str
    certificate_name: Optional[str] = None
    issue_date: Optional[str] = None
    expiration_date: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


@router.post("", summary="Submit Certificate for Verification", status_code=201)
async def submit_certificate(request: Request, body: CertificateRequest):
    raw = await request.body()
    target_url = f"{SERVICES['certificates']}/certificates"
    return forward_request(request, target_url, raw, _user_header(request))


@router.get("/issuers", summary="List Trusted Issuers")
async def list_issuers(request: Request):
    target_url = f"{SERVICES['certificates']}/certificates/issuers"
    return forward_request(request, target_url, None, _user_header(request))


@router.get("/candidate/{candidate_id}", summary="Get Candidate Certificates")
async def get_candidate_certificates(request: Request, candidate_id: str):
    target_url = f"{SERVICES['certificates']}/certificates/candidate/{candidate_id}"
    return forward_request(request, target_url, None, _user_header(request))


@router.get("/{certificate_id}", summary="Get Certificate by ID")
async def get_certificate(request: Request, certificate_id: str):
    target_url = f"{SERVICES['certificates']}/certificates/{certificate_id}"
    return forward_request(request, target_url, None, _user_header(request))
