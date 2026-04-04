import json
import logging
import time
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from typing import List

from clients.profile_client import get_profile_bundle
from services.advisor_service import analyze_cv
from services.bio_service import generate_bio


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

app = FastAPI(title="Recommendation Service", version="0.1.0")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail, "code": exc.status_code})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": "Internal server error", "code": 500})


@app.get("/recommendation/health", tags=["system"])
def health():
    return {"status": "ok", "service": "recommendation"}


class AnalyzeRequest(BaseModel):
    job_description: str


class BioRequest(BaseModel):
    keywords: List[str]


@app.post("/recommendation/analyze", tags=["recommendation"])
async def analyze(
    body: AnalyzeRequest,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
):
    """
    Analyze the user's profile against a job description and return CV recommendations.

    Returns:
    - relevant_skills: skills the user has that match the job
    - matching_experiences: work history relevant to the role
    - recommended_certifications: certs to pursue based on job requirements
    - areas_for_development: skills/tech the user lacks but the job needs
    """
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id")

    bundle = await get_profile_bundle(x_user_id)
    result = await analyze_cv(x_user_id, bundle, body.job_description)
    return result


@app.post("/recommendation/generate-bio", tags=["recommendation"])
async def generate_bio_endpoint(
    body: BioRequest,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
):
    """
    Generate a professional bio from the user's profile and optional keywords.
    Returns plain text to be used in CV generation or shown in the CV editor for review/editing.
    """
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id")

    bundle = await get_profile_bundle(x_user_id)
    bio = await generate_bio(bundle, body.keywords)
    return {"bio": bio}
