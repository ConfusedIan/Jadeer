from fastapi import APIRouter, Request
from services.service_registry import SERVICES
from utils.http_client import forward_request

router = APIRouter(prefix="/auth", tags=["auth"])

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def auth_proxy(request: Request, path: str):
    body = await request.body()
    target_url = f"{SERVICES['AUTH']}/auth/{path}"
    return forward_request(request, target_url, body)
