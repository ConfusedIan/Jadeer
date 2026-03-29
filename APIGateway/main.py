import json
import logging
import time
from fastapi import FastAPI, Depends,Request
from fastapi.security import HTTPBearer
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
from core.middleware import log_requests, auth_guard
from config import APP_NAME, CORS_ORIGINS


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return json.dumps({
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        })

_handler = logging.StreamHandler()
_handler.setFormatter(_JsonFormatter())
logging.basicConfig(level=logging.INFO, handlers=[_handler])

from routes.profile_proxy import router as profile_router
from routes.assessment_proxy import router as assessment_router
from routes.cv_proxy import router as cv_router
from routes.recommendation_proxy import router as recommendation_router
from routes.ranking_proxy import router as ranking_router
from routes.cert_proxy import router as cert_router


bearer_scheme = HTTPBearer()

app = FastAPI(title=APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )

    schema.setdefault("components", {}).setdefault("securitySchemes", {})
    schema["components"]["securitySchemes"]["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }

    schema["security"] = [{"BearerAuth": []}]

    public_paths = ["/health", "/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"]
    for p in public_paths:
        if p in schema["paths"]:
            for method in schema["paths"][p].values():
                method.pop("security", None)

    app.openapi_schema = schema
    return app.openapi_schema

app.openapi = custom_openapi

app.middleware("http")(log_requests)
app.middleware("http")(auth_guard)

@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "service": "api-gateway"}

@app.get("/whoami", tags=["system"])
def whoami(request: Request):
    user = getattr(request.state, "user", None) or {}
    raw = user.get("raw", {}) or {}
    return {
        "user_id": user.get("user_id"),
        "email": raw.get("email"),
        "role": raw.get("role"),
    }

# register routes
app.include_router(profile_router)
app.include_router(assessment_router)
app.include_router(cv_router)
app.include_router(recommendation_router)
app.include_router(ranking_router)
app.include_router(cert_router)