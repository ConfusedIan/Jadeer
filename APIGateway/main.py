from fastapi import FastAPI, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from fastapi import Request
from core.middleware import log_requests, auth_guard
from config import APP_NAME

from routes.auth_proxy import router as auth_router
from routes.assessment_proxy import router as assessment_router
from routes.cv_proxy import router as cv_router
from routes.recommendation_proxy import router as recommendation_router
from routes.ranking_proxy import router as ranking_router

bearer_scheme = HTTPBearer()

app = FastAPI(title=APP_NAME)

app.middleware("http")(log_requests)
app.middleware("http")(auth_guard)

@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "service": "api-gateway"}

@app.get("/whoami", tags=["system"])
def whoami(auth: HTTPAuthorizationCredentials = Depends(bearer_scheme), request: Request = None):
    user = getattr(request.state, "user", None)
    return {"ok": True, "user_from_middleware": user}

# register routes
app.include_router(auth_router)
app.include_router(assessment_router)
app.include_router(cv_router)
app.include_router(recommendation_router)
app.include_router(ranking_router)
