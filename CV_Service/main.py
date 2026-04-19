import json
import logging
import time
from typing import Dict, Optional

from fastapi import FastAPI, Header, Response, Query, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel

from clients.profile_client import get_profile_bundle
from utils.merge import dummy_bundle, merge_real_with_dummy
from templates.ats_reportlab import generate_cv_pdf
from utils.cv_history import save_cv, list_cvs, get_cv_url, delete_cv
from config import SUPABASE_URL


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

app = FastAPI(title="CV Generation Service", version="0.3.0")

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail, "code": exc.status_code})

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": "Internal server error", "code": 500})


@app.get("/cv/health", tags=["system"])
def health():
    return {"status": "ok", "service": "cv"}


# ── Simple GET (backward-compatible) ─────────────────────────────────────────

@app.get("/cv/me.pdf", tags=["cv"])
async def cv_me_pdf(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    include_experience: bool = Query(True),
    include_education: bool = Query(True),
    include_certificates: bool = Query(True),
    include_skills: bool = Query(True),
    include_scores: bool = Query(True),
    include_verified_badges: bool = Query(True),
    demo: bool = Query(False),
):
    if not x_user_id and not demo:
        raise HTTPException(status_code=401, detail="Missing X-User-Id")

    if demo:
        real = {"profile": {}, "experiences": [], "education": [], "certificates": [], "skills": []}
        data = merge_real_with_dummy(real, dummy_bundle())
    else:
        real = await get_profile_bundle(x_user_id)  # type: ignore[arg-type]
        data = merge_real_with_dummy(real, dummy_bundle())

    pdf_bytes = generate_cv_pdf(
        data=data,
        include_experience=include_experience,
        include_education=include_education,
        include_certificates=include_certificates,
        include_skills=include_skills,
        include_scores=include_scores,
        include_verified_badges=include_verified_badges,
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "inline; filename=cv.pdf"},
    )


# ── Enhanced POST (customization + history) ───────────────────────────────────

class CVRequest(BaseModel):
    # Section toggles
    include_experience: bool = True
    include_education: bool = True
    include_certificates: bool = True
    include_skills: bool = True
    include_scores: bool = True
    include_verified_badges: bool = True

    # Text rewording — items must already exist in the user's profile
    custom_bio: Optional[str] = None
    experience_overrides: Optional[Dict[int, str]] = None  # {0: "reworded desc"} by index

    # Assessment badge threshold
    skill_threshold: float = 70.0

    # History
    save_to_history: bool = False
    cv_name: Optional[str] = None


@app.post("/cv/me.pdf", tags=["cv"])
async def cv_me_pdf_post(
    body: CVRequest,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
):
    """
    Generate a customized CV PDF.

    - custom_bio: replace the bio text for this CV (use POST /recommendation/generate-bio to get an AI-generated one)
    - experience_overrides: reword specific experience descriptions by their 0-based index {0: "new text"}
    - skill_threshold: skills with score >= this value get a ★ verified badge (default 70)
    - save_to_history: persist the generated PDF to CV history
    - cv_name: label for the saved CV (e.g. "Google Application")
    """
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id")

    real = await get_profile_bundle(x_user_id)
    data = merge_real_with_dummy(real, dummy_bundle())

    # Apply bio override (rewording only — profile remains unchanged)
    if body.custom_bio is not None:
        data["profile"]["bio"] = body.custom_bio

    # Apply experience description overrides (valid indices only)
    if body.experience_overrides:
        exps = data.get("experiences", [])
        for idx, new_desc in body.experience_overrides.items():
            if 0 <= idx < len(exps):
                exps[idx]["description"] = new_desc

    pdf_bytes = generate_cv_pdf(
        data=data,
        include_experience=body.include_experience,
        include_education=body.include_education,
        include_certificates=body.include_certificates,
        include_skills=body.include_skills,
        include_scores=body.include_scores,
        include_verified_badges=body.include_verified_badges,
        skill_threshold=body.skill_threshold,
    )

    if body.save_to_history:
        if not SUPABASE_URL:
            raise HTTPException(status_code=503, detail="CV history storage is not configured")
        try:
            await save_cv(
                user_id=x_user_id,
                pdf_bytes=pdf_bytes,
                cv_name=body.cv_name,
                settings=body.model_dump(exclude={"custom_bio", "experience_overrides"}),
            )
        except Exception as exc:
            logging.getLogger(__name__).warning("Failed to save CV history for %s: %s", x_user_id, exc)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "inline; filename=cv.pdf"},
    )


# ── CV History ────────────────────────────────────────────────────────────────

@app.get("/cv/history", tags=["cv"])
async def cv_history_list(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
):
    """List all saved CVs for the current user, newest first."""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id")
    if not SUPABASE_URL:
        raise HTTPException(status_code=503, detail="CV history storage is not configured")

    try:
        return await list_cvs(x_user_id)
    except Exception as exc:
        logging.getLogger(__name__).error("Failed to list CV history for %s: %s", x_user_id, exc)
        raise HTTPException(status_code=500, detail="Failed to retrieve CV history")


@app.get("/cv/history/{cv_id}", tags=["cv"])
async def cv_history_download(
    cv_id: str,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
):
    """Download a previously saved CV by ID."""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id")
    if not SUPABASE_URL:
        raise HTTPException(status_code=503, detail="CV history storage is not configured")

    try:
        url = await get_cv_url(x_user_id, cv_id)
    except Exception as exc:
        logging.getLogger(__name__).warning("CV not found %s/%s: %s", x_user_id, cv_id, exc)
        raise HTTPException(status_code=404, detail="CV not found")

    return {"download_url": url}


@app.delete("/cv/history/{cv_id}", tags=["cv"])
async def cv_history_delete(
    cv_id: str,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
):
    """Delete a saved CV by ID."""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id")
    if not SUPABASE_URL:
        raise HTTPException(status_code=503, detail="CV history storage is not configured")

    try:
        await delete_cv(x_user_id, cv_id)
    except Exception as exc:
        logging.getLogger(__name__).warning("Failed to delete CV %s/%s: %s", x_user_id, cv_id, exc)
        raise HTTPException(status_code=404, detail="CV not found or already deleted")

    return {"deleted": True}


# ── Demo ──────────────────────────────────────────────────────────────────────

@app.get("/cv/demo.pdf")
async def cv_demo_pdf(x_user_id: str | None = Header(default=None, alias="X-User-Id")):
    if x_user_id:
        real = await get_profile_bundle(x_user_id)
    else:
        real = {}

    data = merge_real_with_dummy(real, dummy_bundle())

    pdf_bytes = generate_cv_pdf(
        data=data,
        include_experience=True,
        include_education=True,
        include_certificates=True,
        include_skills=True,
        include_scores=True,
        include_verified_badges=True,
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "inline; filename=cv.pdf"},
    )
