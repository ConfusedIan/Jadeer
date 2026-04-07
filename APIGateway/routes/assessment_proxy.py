from fastapi import APIRouter, Request
from typing import Optional
from pydantic import BaseModel
from services.service_registry import SERVICES
from utils.http_client import forward_request
import json

router = APIRouter(prefix="/assessment", tags=["assessment"])


def _user_header(request: Request) -> dict:
    user = getattr(request.state, "user", {}) or {}
    return {"X-User-Id": user.get("user_id", "")}


def _target(path: str) -> str:
    return f"{SERVICES['assessment'].rstrip('/')}/assessment/{path}"


# ── Request Models ────────────────────────────────────────────────────────────

class AssessmentRequest(BaseModel):
    occupation_code: str
    skill_name: str


class EvaluateRequest(BaseModel):
    occupation_code: str
    occupation_title: str
    skill_name: str
    questions: list[dict]
    answers: dict[str, str]


class FullAssessmentRequest(BaseModel):
    occupation_code: str
    skill_name: str
    answers: Optional[dict[str, str]] = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/skills-list", summary="List all 14 O*NET soft skills")
async def list_skills(request: Request):
    return forward_request(request, _target("skills-list"), None, _user_header(request))


@router.get("/occupations", summary="List all O*NET occupations")
async def list_occupations(request: Request):
    return forward_request(request, _target("occupations"), None, _user_header(request))


@router.post("/match-occupation", summary="Match user profile to closest O*NET occupation")
async def match_occupation(request: Request):
    return forward_request(request, _target("match-occupation"), None, _user_header(request))


@router.post("/generate-assessment", summary="Generate 5 MCQ questions for an occupation + skill")
async def generate_assessment(body: AssessmentRequest, request: Request):
    raw = json.dumps(body.model_dump()).encode()
    return forward_request(request, _target("generate-assessment"), raw, _user_header(request))


@router.post("/evaluate", summary="Evaluate answers and return score with pass/fail")
async def evaluate(body: EvaluateRequest, request: Request):
    raw = json.dumps(body.model_dump()).encode()
    return forward_request(request, _target("evaluate"), raw, _user_header(request))


@router.post("/full-assessment", summary="Run the full assessment pipeline in one call")
async def full_assessment(body: FullAssessmentRequest, request: Request):
    raw = json.dumps(body.model_dump()).encode()
    return forward_request(request, _target("full-assessment"), raw, _user_header(request))
