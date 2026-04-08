"""
Jadeer Ranking Service.

Provides candidate search & ranking for employers (FR.24, FR.25).
The employer sends a set of filters; the service returns a ranked list of
candidates that satisfy those filters, ordered by their match score.
"""
import json
import logging
import time
from typing import List, Optional

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from supabase import create_client, Client

from config import (
    PORT,
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY,
    MAX_RESULTS,
)
from services.ranking import (
    build_skill_lookup,
    passes_hard_filters,
    score_candidate,
    build_candidate_card,
)


# ---------- logging (matches the other services in the project) ----------
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
logger = logging.getLogger("ranking")


# ---------- supabase ----------
if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY env vars")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


# ---------- app ----------
app = FastAPI(title="Ranking Service", version="0.1.0")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "code": exc.status_code},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "code": 500},
    )


@app.get("/ranking/health", tags=["system"])
def health():
    return {"status": "ok", "service": "ranking"}


# ---------- helpers ----------
def _load_standard_skill_names() -> dict[int, str]:
    """
    Pull the standard_skills library once per request. It's small (~132 rows
    per the assessment service) so this is cheap, and it lets us resolve
    `skills.skill_id` -> name without N+1 queries.
    """
    rows = supabase.table("standard_skills").select("skill_id,name").execute().data or []
    return {int(r["skill_id"]): r["name"] for r in rows if r.get("skill_id") is not None and r.get("name")}


def _emails_for(candidate_ids: list[str]) -> dict[str, str]:
    """
    Look up emails from auth.users for a small set of already-ranked
    candidates. We page through admin.list_users until we've found them all
    or exhausted the user list. This is only called for the top results, so
    the cost stays bounded.
    """
    if not candidate_ids:
        return {}
    wanted = set(candidate_ids)
    found: dict[str, str] = {}
    try:
        page = 1
        while wanted and page <= 20:  # hard cap so we never loop forever
            users = supabase.auth.admin.list_users(page=page, per_page=200) or []
            if not users:
                break
            for u in users:
                uid = getattr(u, "id", None)
                if uid in wanted:
                    found[uid] = getattr(u, "email", None) or ""
                    wanted.discard(uid)
            if len(users) < 200:
                break
            page += 1
    except Exception as exc:
        logger.warning("Could not fetch emails from auth.users: %s", exc)
    return found


# ---------- request / response models ----------
class SearchRequest(BaseModel):
    major: Optional[str] = None
    graduation_year: Optional[int] = None
    location: Optional[str] = None
    min_years_experience: Optional[float] = Field(default=None, ge=0)
    skills: Optional[List[str]] = None
    min_skill_score: Optional[float] = Field(default=None, ge=0, le=100)
    limit: int = Field(default=20, ge=1, le=MAX_RESULTS)


# ---------- endpoint ----------
@app.post("/ranking/search", tags=["ranking"])
def search_candidates(
    body: SearchRequest,
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
):
    """
    Search and rank candidates against the employer's criteria.

    Hard filters narrow the pool; the score is the average assessment score
    across the requested skills (or the candidate's overall average if the
    employer didn't request any specific skill).
    """
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id")

    filters = body.model_dump(exclude_none=True)
    filters.pop("limit", None)

    # 1. Pull candidate profiles. Only role='candidate' so employers/admins
    #    don't show up in the search results. Pre-filter location at the DB
    #    level when possible to keep the working set small.
    profile_query = supabase.table("profiles").select("*").eq("role", "candidate")
    if body.location:
        profile_query = profile_query.ilike("location", f"%{body.location}%")

    profiles = profile_query.execute().data or []
    if not profiles:
        return {"results": [], "count": 0}

    candidate_ids = [p["id"] for p in profiles if p.get("id")]

    # 2. Resolve skill_id -> name from the standard_skills library so verified
    #    skills (which only carry skill_id) get a display name.
    standard_skill_names = _load_standard_skill_names()

    # 3. Bulk-fetch related data for all candidates in three round-trips.
    def _bulk(table: str) -> dict[str, list[dict]]:
        rows = (
            supabase.table(table)
            .select("*")
            .in_("candidate_id", candidate_ids)
            .execute()
            .data
            or []
        )
        grouped: dict[str, list[dict]] = {cid: [] for cid in candidate_ids}
        for row in rows:
            cid = row.get("candidate_id")
            if cid in grouped:
                grouped[cid].append(row)
        return grouped

    experiences_by_cand = _bulk("experiences")
    education_by_cand = _bulk("education")
    skills_by_cand = _bulk("skills")

    # 4. Filter + score each candidate.
    ranked: list[dict] = []
    for profile in profiles:
        cid = profile["id"]
        experiences = experiences_by_cand.get(cid, [])
        education = education_by_cand.get(cid, [])
        skills = skills_by_cand.get(cid, [])
        skill_map = build_skill_lookup(skills, standard_skill_names)

        if not passes_hard_filters(profile, experiences, education, skill_map, filters):
            continue

        score = score_candidate(profile, experiences, education, skill_map, filters)
        ranked.append({
            "profile": profile,
            "experiences": experiences,
            "education": education,
            "skill_map": skill_map,
            "score": score,
        })

    # 5. Sort by score descending and trim to the requested limit.
    ranked.sort(key=lambda c: c["score"], reverse=True)
    ranked = ranked[: body.limit]

    # 6. Fetch emails ONLY for the final ranked set.
    emails = _emails_for([r["profile"]["id"] for r in ranked])

    results = [
        build_candidate_card(
            r["profile"],
            r["experiences"],
            r["education"],
            r["skill_map"],
            r["score"],
            email=emails.get(r["profile"]["id"]),
        )
        for r in ranked
    ]

    logger.info(
        "Ranking search by employer=%s -> %d candidates", x_user_id, len(results)
    )
    return {"results": results, "count": len(results)}
