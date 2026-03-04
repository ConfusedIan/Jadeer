from fastapi import APIRouter, Request
from fastapi.encoders import jsonable_encoder

from utils.http_client import forward_request
from services.service_registry import SERVICES
import json

from models.profile import ProfileUpdate
from models.experiences import ExperienceCreate, ExperienceUpdate
from models.education import EducationCreate, EducationUpdate
from models.certificates import CertificateCreate, CertificateUpdate
from models.skills import SkillCreate, SkillUpdate

router = APIRouter(prefix="/profile", tags=["profile"])

def _user_header(request: Request) -> dict:
    user = getattr(request.state, "user", {}) or {}
    return {"X-User-Id": user.get("user_id", "")}


@router.get("/me")
async def get_me(request: Request):
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

@router.get("/me/education")
async def list_my_education(request: Request):
    return forward_request(
        request,
        f"{SERVICES['profile']}/profile/me/education",
        body=None,
        extra_headers=_user_header(request),
    )

@router.post("/me/education")
async def add_education(payload: EducationCreate, request: Request):
    body = json.dumps(jsonable_encoder(payload)).encode("utf-8")
    return forward_request(
        request,
        f"{SERVICES['profile']}/profile/me/education",
        body=body,
        extra_headers=_user_header(request),
    )

@router.put("/me/education/{edu_id}")
async def update_education(edu_id: str, payload: EducationUpdate, request: Request):
    body = json.dumps(jsonable_encoder(payload)).encode("utf-8")
    return forward_request(
        request,
        f"{SERVICES['profile']}/profile/me/education/{edu_id}",
        body=body,
        extra_headers=_user_header(request),
    )

@router.delete("/me/education/{edu_id}")
async def delete_education(edu_id: str, request: Request):
    return forward_request(
        request,
        f"{SERVICES['profile']}/profile/me/education/{edu_id}",
        body=None,
        extra_headers=_user_header(request),
    )

@router.get("/me/certificates")
async def list_my_certificates(request: Request):
    return forward_request(
        request,
        f"{SERVICES['profile']}/profile/me/certificates",
        body=None,
        extra_headers=_user_header(request),
    )

@router.post("/me/certificates")
async def add_certificate(payload: CertificateCreate, request: Request):
    body = json.dumps(jsonable_encoder(payload)).encode("utf-8")
    return forward_request(
        request,
        f"{SERVICES['profile']}/profile/me/certificates",
        body=body,
        extra_headers=_user_header(request),
    )

@router.put("/me/certificates/{cert_id}")
async def update_certificate(cert_id: str, payload: CertificateUpdate, request: Request):
    body = json.dumps(jsonable_encoder(payload)).encode("utf-8")
    return forward_request(
        request,
        f"{SERVICES['profile']}/profile/me/certificates/{cert_id}",
        body=body,
        extra_headers=_user_header(request),
    )

@router.delete("/me/certificates/{cert_id}")
async def delete_certificate(cert_id: str, request: Request):
    return forward_request(
        request,
        f"{SERVICES['profile']}/profile/me/certificates/{cert_id}",
        body=None,
        extra_headers=_user_header(request),
    )

@router.get("/me/skills")
async def list_my_skills(request: Request):
    return forward_request(
        request,
        f"{SERVICES['profile']}/profile/me/skills",
        body=None,
        extra_headers=_user_header(request),
    )

@router.post("/me/skills")
async def add_skill(payload: SkillCreate, request: Request):
    body = json.dumps(jsonable_encoder(payload)).encode("utf-8")
    return forward_request(
        request,
        f"{SERVICES['profile']}/profile/me/skills",
        body=body,
        extra_headers=_user_header(request),
    )

@router.put("/me/skills/{row_id}")
async def update_skill(row_id: str, payload: SkillUpdate, request: Request):
    body = json.dumps(jsonable_encoder(payload)).encode("utf-8")
    return forward_request(
        request,
        f"{SERVICES['profile']}/profile/me/skills/{row_id}",
        body=body,
        extra_headers=_user_header(request),
    )

@router.delete("/me/skills/{row_id}")
async def delete_skill(row_id: str, request: Request):
    return forward_request(
        request,
        f"{SERVICES['profile']}/profile/me/skills/{row_id}",
        body=None,
        extra_headers=_user_header(request),
    )