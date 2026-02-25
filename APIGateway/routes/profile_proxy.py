from fastapi import APIRouter, Request
from utils.http_client import forward_request
from services.service_registry import SERVICES
from pydantic import BaseModel
from typing import Optional
from datetime import date
from fastapi.encoders import jsonable_encoder
import json

router = APIRouter(prefix="/profile", tags=["profile"])

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    linkedin_url: Optional[str] = None
    location: Optional[str] = None

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

def _user_header(request: Request) -> dict:
    user = getattr(request.state, "user", {}) or {}
    return {"X-User-Id": user.get("user_id", "")}


@router.get("/me")
async def get_me(request: Request):
    # GET should not send a body
    return forward_request(
        request,
        f"{SERVICES['profile']}/profile/me",
        body=None,
        extra_headers=_user_header(request),
    )

@router.patch("/me")
async def patch_me(payload: ProfileUpdate, request: Request):
    body = json.dumps(jsonable_encoder(payload)).encode("utf-8")
    headers = _user_header(request)
    headers["content-type"] = "application/json"

    return forward_request(
        request,
        f"{SERVICES['profile']}/profile/me",
        body=body,
        extra_headers=headers,
    )

@router.get("/me/experiences")
async def list_my_experiences(request: Request):
    return forward_request(
        request,
        f"{SERVICES['profile']}/profile/me/experiences",
        body=None,
        extra_headers=_user_header(request),
    )

@router.post("/me/experiences")
async def add_experience(payload: ExperienceCreate, request: Request):
    body = json.dumps(jsonable_encoder(payload)).encode("utf-8")
    headers = _user_header(request)
    headers["content-type"] = "application/json"

    return forward_request(
        request,
        f"{SERVICES['profile']}/profile/me/experiences",
        body=body,
        extra_headers=headers,
    )

@router.put("/me/experiences/{exp_id}")
async def update_experience(exp_id: str, payload: ExperienceUpdate, request: Request):
    body = json.dumps(jsonable_encoder(payload)).encode("utf-8")
    headers = _user_header(request)
    headers["content-type"] = "application/json"

    return forward_request(
        request,
        f"{SERVICES['profile']}/profile/me/experiences/{exp_id}",
        body=body,
        extra_headers=headers,
    )

@router.delete("/me/experiences/{exp_id}")
async def delete_experience(request: Request, exp_id: str):
    return forward_request(
        request,
        f"{SERVICES['profile']}/profile/me/experiences/{exp_id}",
        body=None,
        extra_headers=_user_header(request),
    )