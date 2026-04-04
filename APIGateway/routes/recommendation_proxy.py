import json
from typing import Dict, List, Optional
from fastapi import APIRouter, Request
from pydantic import BaseModel
from services.service_registry import SERVICES
from utils.http_client import forward_request

router = APIRouter(prefix="/recommendation", tags=["recommendation"])

def _user_header(request: Request) -> dict:
    user = getattr(request.state, "user", {}) or {}
    return {"X-User-Id": user.get("user_id", "")}

def _target(path: str) -> str:
    return f"{SERVICES['recommendation'].rstrip('/')}/recommendation/{path}"


class AnalyzeRequest(BaseModel):
    job_description: str


class BioRequest(BaseModel):
    keywords: Optional[List[str]] = []


@router.get("/health")
async def recommendation_health(request: Request):
    return forward_request(request, _target("health"), None, _user_header(request))


@router.post("/analyze")
async def recommendation_analyze(body: AnalyzeRequest, request: Request):
    return forward_request(request, _target("analyze"), json.dumps(body.model_dump()).encode(), _user_header(request))


@router.post("/generate-bio")
async def recommendation_generate_bio(body: BioRequest, request: Request):
    return forward_request(request, _target("generate-bio"), json.dumps(body.model_dump()).encode(), _user_header(request))
