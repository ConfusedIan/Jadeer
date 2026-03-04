from fastapi import FastAPI, Depends,Request
from fastapi.security import HTTPBearer
from fastapi.openapi.utils import get_openapi
from core.middleware import log_requests, auth_guard
from config import APP_NAME

from routes.profile_proxy import router as profile_router
from routes.assessment_proxy import router as assessment_router
from routes.cv_proxy import router as cv_router
from routes.recommendation_proxy import router as recommendation_router
from routes.ranking_proxy import router as ranking_router

bearer_scheme = HTTPBearer()

app = FastAPI(title=APP_NAME)

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
