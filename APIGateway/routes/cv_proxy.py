from fastapi import APIRouter, Request
from services.service_registry import SERVICES
from utils.http_client import forward_request

router = APIRouter(prefix="/cv", tags=["cv"])

def _user_header(request: Request) -> dict:
    user = getattr(request.state, "user", {}) or {}
    return {"X-User-Id": user.get("user_id", "")}

def _target(path: str) -> str:
    return f"{SERVICES['cv'].rstrip('/')}/cv/{path}"


@router.get("/health")
async def cv_health(request: Request):
    return forward_request(request, _target("health"), None, _user_header(request))


@router.get("/me.pdf")
async def cv_get_pdf(request: Request):
    return forward_request(request, _target("me.pdf"), None, _user_header(request))


@router.post("/me.pdf")
async def cv_post_pdf(request: Request):
    body = await request.body()
    return forward_request(request, _target("me.pdf"), body, _user_header(request))


@router.get("/history")
async def cv_history_list(request: Request):
    return forward_request(request, _target("history"), None, _user_header(request))


@router.get("/history/{cv_id}")
async def cv_history_download(cv_id: str, request: Request):
    return forward_request(request, _target(f"history/{cv_id}"), None, _user_header(request))


@router.get("/demo.pdf")
async def cv_demo_pdf(request: Request):
    return forward_request(request, _target("demo.pdf"), None, _user_header(request))