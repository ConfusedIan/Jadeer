import time
from fastapi import Request
from fastapi.responses import JSONResponse
from core.security import get_bearer_token, verify_supabase_jwt
from core.exceptions import UnauthorizedError

async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start) * 1000

    print(f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms:.1f} ms)")
    return response

PUBLIC_PATH_PREFIXES = ("/docs", "/openapi.json", "/redoc", "/health", "/status", "/dev")

async def auth_guard(request: Request, call_next):
    if request.method == "OPTIONS":
        return await call_next(request)
    
    path = request.url.path
    if path.startswith(PUBLIC_PATH_PREFIXES):
        return await call_next(request)

    try:
        token = get_bearer_token(request)
        payload = verify_supabase_jwt(token)

        request.state.user = {
            "user_id": payload.get("sub"),
            "role": payload.get("role"),
            "raw": payload,
        }

        return await call_next(request)

    except UnauthorizedError as e:
        return JSONResponse(status_code=401, content={"detail": str(e.detail) if hasattr(e, "detail") else str(e)})