import time
from fastapi import Request

async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start) * 1000

    # Simple console log (good enough for now)
    print(f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms:.1f} ms)")
    return response
