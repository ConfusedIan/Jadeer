from fastapi import FastAPI
from core.middleware import log_requests
from config import APP_NAME

from routes.auth_proxy import router as auth_router
from routes.assessment_proxy import router as assessment_router
from routes.cv_proxy import router as cv_router
from routes.recommendation_proxy import router as recommendation_router
from routes.ranking_proxy import router as ranking_router

app = FastAPI(title=APP_NAME)

app.middleware("http")(log_requests)

@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "service": "api-gateway"}

# register routes
app.include_router(auth_router)
app.include_router(assessment_router)
app.include_router(cv_router)
app.include_router(recommendation_router)
app.include_router(ranking_router)
