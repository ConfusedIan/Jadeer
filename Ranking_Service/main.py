import logging
from enum import Enum
from typing import List, Optional

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from supabase import create_client, Client

from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
from ranking import (
    build_skill_lookup, passes_hard_filters,
    score_candidate, build_candidate_card, _years_of_experience,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ranking")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY env vars")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
app = FastAPI(title="Ranking Service", version="0.1.0")


@app.exception_handler(Exception)
async def _handle_error(_request: Request, exc: Exception):
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(status_code=500, content={"error": "Internal server error"})


@app.get("/ranking/health", tags=["system"])
def health():
    return {"status": "ok", "service": "ranking"}


# ---------- models ----------

class SortBy(str, Enum):
    score            = "score"
    years_experience = "years_experience"

class SortOrder(str, Enum):
    desc = "desc"
    asc  = "asc"

class SkillFilter(BaseModel):
    name: str
    min_score: float = Field(default=0, ge=0, le=100)

class SearchRequest(BaseModel):
    major:                str
    location:             str
    min_years_experience: float = Field(ge=0)
    soft_skills:          List[SkillFilter] = Field(min_length=1)
    tech_skills:          List[str]
    graduation_year:      Optional[int] = None
    sort_by:              SortBy    = SortBy.score
    sort_order:           SortOrder = SortOrder.desc


# ---------- db helpers ----------

def _extract_ids(rows: list[dict] | None) -> set[str]:
    return {r["candidate_id"] for r in (rows or []) if r.get("candidate_id")}


def _load_standard_skill_names() -> dict[int, str]:
    rows = supabase.table("standard_skills").select("skill_id,name").execute().data or []
    return {int(r["skill_id"]): r["name"] for r in rows if r.get("skill_id") and r.get("name")}


def _ids_by_education(major: str | None, year: int | None) -> set[str]:
    """One DB call covering both major and graduation year filters."""
    q = supabase.table("education").select("candidate_id")
    if major:
        q = q.ilike("field_of_study", f"%{major}%")
    if year:
        q = q.gte("end_date", f"{year}-01-01").lte("end_date", f"{year}-12-31")
    return _extract_ids(q.execute().data)


def _ids_with_skill(skill_name: str, standard_skill_names: dict[int, str]) -> set[str]:
    norm = skill_name.strip().lower()
    std_ids = [sid for sid, name in standard_skill_names.items() if norm in name.lower()]

    ids = _extract_ids(
        supabase.table("skills").select("candidate_id")
        .ilike("custom_skill_name", f"%{skill_name}%").execute().data
    )
    if std_ids:
        ids |= _extract_ids(
            supabase.table("skills").select("candidate_id")
            .in_("skill_id", std_ids).execute().data
        )
    return ids


def _emails_for(candidate_ids: list[str]) -> dict[str, str]:
    if not candidate_ids:
        return {}
    wanted, found = set(candidate_ids), {}
    try:
        for page in range(1, 21):
            users = supabase.auth.admin.list_users(page=page, per_page=200) or []
            if not users:
                break
            for u in users:
                if (uid := getattr(u, "id", None)) in wanted:
                    found[uid] = getattr(u, "email", None) or ""
                    wanted.discard(uid)
            if not wanted or len(users) < 200:
                break
    except Exception as exc:
        logger.warning("Could not fetch emails: %s", exc)
    return found


def _bulk_fetch(table: str, candidate_ids: list[str]) -> dict[str, list[dict]]:
    rows = supabase.table(table).select("*").in_("candidate_id", candidate_ids).execute().data or []
    grouped: dict[str, list[dict]] = {cid: [] for cid in candidate_ids}
    for row in rows:
        if (cid := row.get("candidate_id")) in grouped:
            grouped[cid].append(row)
    return grouped


# ---------- endpoint ----------

@app.post("/ranking/search", tags=["ranking"])
def search_candidates(
    body: SearchRequest,
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
):
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id")

    filters = body.model_dump(exclude={"sort_by", "sort_order"}, exclude_none=True)

    standard_skill_names = _load_standard_skill_names()

    # --- DB-level filtering ---
    candidate_ids = {
        r["id"] for r in
        supabase.table("profiles").select("id").eq("role", "candidate")
        .ilike("location", f"%{body.location}%").execute().data or []
        if r.get("id")
    }

    if body.major or body.graduation_year:
        candidate_ids &= _ids_by_education(body.major, body.graduation_year)

    for skill in body.tech_skills:
        candidate_ids &= _ids_with_skill(skill, standard_skill_names)

    if not candidate_ids:
        return {"results": [], "count": 0}

    # --- Load full data for shortlisted candidates only ---
    profiles = supabase.table("profiles").select("*").in_("id", list(candidate_ids)).execute().data or []
    ids       = [p["id"] for p in profiles]

    by_cand = {
        table: _bulk_fetch(table, ids)
        for table in ("experiences", "education", "skills", "certificates")
    }

    # --- Python-level filtering + scoring ---
    results: list[dict] = []
    for profile in profiles:
        cid          = profile["id"]
        experiences  = by_cand["experiences"].get(cid, [])
        education    = by_cand["education"].get(cid, [])
        certificates = by_cand["certificates"].get(cid, [])
        skill_map    = build_skill_lookup(by_cand["skills"].get(cid, []), standard_skill_names)

        if not passes_hard_filters(profile, experiences, education, skill_map, filters):
            continue

        results.append({
            "profile":             profile,
            "experiences":         experiences,
            "education":           education,
            "certificates":        certificates,
            "skill_map":           skill_map,
            "avg_soft_skill_score": score_candidate(skill_map, filters),
        })

    # --- Sort (all matches returned, no limit) ---
    sort_key = (
        (lambda c: _years_of_experience(c["experiences"]))
        if body.sort_by == SortBy.years_experience
        else (lambda c: c["avg_soft_skill_score"])
    )
    results.sort(key=sort_key, reverse=body.sort_order == SortOrder.desc)

    emails = _emails_for([r["profile"]["id"] for r in results])

    cards = [
        build_candidate_card(
            r["profile"], r["experiences"], r["education"],
            r["skill_map"], r["certificates"], r["avg_soft_skill_score"],
            filters=filters, email=emails.get(r["profile"]["id"]),
        )
        for r in results
    ]

    logger.info("employer=%s search -> %d results", x_user_id, len(cards))
    return {"results": cards, "count": len(cards)}
