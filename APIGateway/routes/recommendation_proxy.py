from fastapi import APIRouter, Request
from services.service_registry import SERVICES
from utils.http_client import forward_request

router = APIRouter(prefix="/recommendation", tags=["recommendation"])

def _user_header(request: Request) -> dict:
    user = getattr(request.state, "user", {}) or {}
    return {"X-User-Id": user.get("user_id", "")}

def _target(path: str) -> str:
    return f"{SERVICES['recommendation'].rstrip('/')}/recommendation/{path}"


@router.get("/health")
async def recommendation_health(request: Request):
    return forward_request(request, _target("health"), None, _user_header(request))


@router.post("/analyze")
async def recommendation_analyze(request: Request):
    body = await request.body()
    return forward_request(request, _target("analyze"), body, _user_header(request))


@router.post("/generate-bio")
async def recommendation_generate_bio(request: Request):
    body = await request.body()
    return forward_request(request, _target("generate-bio"), body, _user_header(request))
