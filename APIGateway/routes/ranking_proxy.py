import json
from enum import Enum
from typing import List, Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from services.service_registry import SERVICES
from utils.http_client import forward_request

router = APIRouter(prefix="/ranking", tags=["ranking"])


class SortBy(str, Enum):
    score = "score"
    years_experience = "years_experience"


class SortOrder(str, Enum):
    desc = "desc"
    asc = "asc"


# Mirrors the ranking service request model so Swagger renders the input box
class SkillFilter(BaseModel):
    name: str
    min_score: float = Field(default=0, ge=0, le=100)


class SearchRequest(BaseModel):
    major: Optional[str] = None
    location: Optional[str] = None
    min_years_experience: Optional[float] = Field(default=None, ge=0)
    soft_skills: List[SkillFilter] = Field(default_factory=list)
    tech_skills: List[str] = Field(default_factory=list)
    graduation_year: Optional[int] = None
    sort_by: SortBy = SortBy.score
    sort_order: SortOrder = SortOrder.desc


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
        body=json.dumps(body.model_dump(exclude_none=True)).encode(),
        extra_headers=_user_header(request),
    )