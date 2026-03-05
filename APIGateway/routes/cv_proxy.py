from fastapi import APIRouter, Request
from services.service_registry import SERVICES
from utils.http_client import forward_request

router = APIRouter(prefix="/cv", tags=["cv"])

def _user_header(request: Request) -> dict:
    return {"X-User-Id": request.state.user["user_id"]}

def _target(path: str = "") -> str:
    base = SERVICES["cv"].rstrip("/")   # http://127.0.0.1:5004
    if path:
        return f"{base}/cv/{path}"
    return f"{base}/cv"

@router.get("/health")
async def cv_health(request: Request):
    body = await request.body()
    return forward_request(request, _target("health"), body if body else None, _user_header(request))

@router.get("/me.pdf")
async def cv_me_pdf(request: Request):
    body = await request.body()
    return forward_request(request, _target("me.pdf"), body if body else None, _user_header(request))

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def cv_proxy(request: Request, path: str):
    body = await request.body()
    return forward_request(request, _target(path), body if body else None, _user_header(request))