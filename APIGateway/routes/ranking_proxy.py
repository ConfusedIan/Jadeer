import json
from typing import Any, List, Optional
from fastapi import APIRouter, Request, Body
from pydantic import BaseModel, Field
from services.service_registry import SERVICES
from utils.http_client import forward_request

router = APIRouter(prefix="/ranking", tags=["ranking"])


# Mirrors the ranking service request model so Swagger renders the input box
class SkillFilter(BaseModel):
    name: str
    min_score: float = Field(default=0, ge=0, le=100)

class SearchRequest(BaseModel):
    major: str
    location: str
    min_years_experience: float = Field(ge=0)
    soft_skills: List[SkillFilter] = Field(min_length=1)
    tech_skills: List[str]
    graduation_year: Optional[int] = None
    sort_by: str = "score"
    sort_order: str = "desc"


def _user_header(request: Request) -> dict:
    user = getattr(request.state, "user", {}) or {}
    return {"X-User-Id": user.get("user_id", "")}


@router.get("/health", tags=["ranking"])
async def ranking_health(request: Request):
    return forward_request(request, f"{SERVICES['ranking']}/ranking/health", body=None)


@router.post("/search", tags=["ranking"])
async def ranking_search(request: Request, body: SearchRequest):
    return forward_request(
        request,
        f"{SERVICES['ranking']}/ranking/search",
        body=json.dumps(body.model_dump()).encode(),
        extra_headers=_user_header(request),
    )
