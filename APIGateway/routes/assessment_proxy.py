from fastapi import APIRouter, Request
from services.service_registry import SERVICES
from utils.http_client import forward_request

router = APIRouter(prefix="/assessment", tags=["assessment"])

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def assessment_proxy(request: Request, path: str):
    body = await request.body()
    target_url = f"{SERVICES['assessment']}/assessment/{path}"
    return forward_request(request, target_url, body)
