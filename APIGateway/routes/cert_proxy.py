from fastapi import APIRouter, Request
from services.service_registry import SERVICES
from utils.http_client import forward_request

router = APIRouter(prefix="/certificates", tags=["certificates"])

def _user_header(request: Request) -> dict:
    user = getattr(request.state, "user", {}) or {}
    return {"X-User-Id": user.get("user_id", "")}


@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def cert_proxy(request: Request, path: str):
    body = await request.body()
    target_url = f"{SERVICES['certificates']}/certificates/{path}"
    return forward_request(request, target_url, body if body else None, _user_header(request))


@router.get("")
async def cert_root_proxy(request: Request):
    body = await request.body()
    target_url = f"{SERVICES['certificates']}/certificates"
    return forward_request(request, target_url, body if body else None, _user_header(request))
