import json
from typing import Dict, Optional
from fastapi import APIRouter, Request
from pydantic import BaseModel
from services.service_registry import SERVICES
from utils.http_client import forward_request

router = APIRouter(prefix="/cv", tags=["cv"])

def _user_header(request: Request) -> dict:
    user = getattr(request.state, "user", {}) or {}
    return {"X-User-Id": user.get("user_id", "")}

def _target(path: str) -> str:
    return f"{SERVICES['cv'].rstrip('/')}/cv/{path}"


class CVRequest(BaseModel):
    include_experience: bool = True
    include_education: bool = True
    include_certificates: bool = True
    include_skills: bool = True
    include_scores: bool = True
    include_verified_badges: bool = True
    custom_bio: Optional[str] = None
    experience_overrides: Optional[Dict[int, str]] = None
    skill_threshold: float = 70.0
    save_to_history: bool = False
    cv_name: Optional[str] = None


@router.get("/health")
async def cv_health(request: Request):
    return forward_request(request, _target("health"), None, _user_header(request))


@router.get("/me.pdf")
async def cv_get_pdf(request: Request):
    return forward_request(request, _target("me.pdf"), None, _user_header(request))


@router.post("/me.pdf")
async def cv_post_pdf(body: CVRequest, request: Request):
    return forward_request(request, _target("me.pdf"), json.dumps(body.model_dump()).encode(), _user_header(request))


@router.get("/history")
async def cv_history_list(request: Request):
    return forward_request(request, _target("history"), None, _user_header(request))


@router.get("/history/{cv_id}")
async def cv_history_download(cv_id: str, request: Request):
    return forward_request(request, _target(f"history/{cv_id}"), None, _user_header(request))


@router.delete("/history/{cv_id}")
async def cv_history_delete(cv_id: str, request: Request):
    return forward_request(request, _target(f"history/{cv_id}"), None, _user_header(request))


@router.get("/demo.pdf")
async def cv_demo_pdf(request: Request):
    return forward_request(request, _target("demo.pdf"), None, _user_header(request))