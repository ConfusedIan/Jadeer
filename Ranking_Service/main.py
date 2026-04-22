import logging
import re
from enum import Enum
from typing import List, Optional

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from supabase import create_client, Client

from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
from ranking import (
    _norm,
    build_skill_lookup,
    passes_hard_filters,
    score_candidate,
    build_candidate_card,
    _years_of_experience,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ranking")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY env vars")

db: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
app = FastAPI(title="Ranking Service", version="0.1.0")

_CHUNK = 200  # max IDs per Supabase in_() call


# ---------- app ----------

@app.exception_handler(Exception)
async def _handle_error(_request: Request, exc: Exception):
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(status_code=500, content={"error": "Internal server error"})


@app.get("/ranking/health")
def health():
    return {"status": "ok", "service": "ranking"}


# ---------- models ----------

class SortBy(str, Enum):
    score = "score"
    years_experience = "years_experience"


class SortOrder(str, Enum):
    desc = "desc"
    asc = "asc"


class SkillFilter(BaseModel):
    name: str
    min_score: float = Field(default=0, ge=0, le=100)


class SearchRequest(BaseModel):
    major: Optional[str] = None
    location: Optional[str] = None
    min_years_experience: Optional[float] = Field(default=None, ge=0)
    soft_skills: List[SkillFilter] = Field(default_factory=list)
    tech_skills: List[str] = Field(default_factory=list)
    graduation_year: Optional[int] = None
    sort_by: SortBy = SortBy.score
    sort_order: SortOrder = SortOrder.desc


# ---------- db helpers ----------

def _extract_ids(rows) -> set[str]:
    return {r["candidate_id"] for r in (rows or []) if r.get("candidate_id")}


def _load_skill_names() -> dict[int, str]:
    rows = db.table("standard_skills").select("skill_id,name").execute().data or []
    return {
        int(r["skill_id"]): r["name"]
        for r in rows
        if r.get("skill_id") and r.get("name")
    }


def _ids_by_location(location: str) -> set[str]:
    rows = (
        db.table("profiles")
        .select("id")
        .eq("role", "candidate")
        .ilike("location", f"%{location}%")
        .execute()
        .data
        or []
    )
    return {r["id"] for r in rows if r.get("id")}


def _all_candidate_ids() -> set[str]:
    rows = db.table("profiles").select("id").eq("role", "candidate").execute().data or []
    return {r["id"] for r in rows if r.get("id")}


def _ids_by_major(major: str) -> set[str]:
    return _extract_ids(
        db.table("education")
        .select("candidate_id")
        .ilike("field_of_study", f"%{major}%")
        .execute()
        .data
    )


def _ids_by_grad_year(year: int) -> set[str]:
    return _extract_ids(
        db.table("education")
        .select("candidate_id")
        .gte("end_date", f"{year}-01-01")
        .lte("end_date", f"{year}-12-31")
        .execute()
        .data
    )


def _skill_text_matches(candidate_name: str, wanted_name: str) -> bool:
    wanted = _norm(wanted_name)
    candidate = _norm(candidate_name)

    if not wanted or not candidate:
        return False

    if candidate == wanted:
        return True

    pattern = re.compile(r"(?<![a-z0-9])" + re.escape(wanted) + r"(?![a-z0-9])")
    return bool(pattern.search(candidate))


def _ids_by_skill(name: str, skill_names: dict[int, str]) -> set[str]:
    wanted = _norm(name)
    if not wanted:
        return set()

    # Check standard skill names using the same matching style used later in Python
    std_ids = [
        sid for sid, skill_name in skill_names.items()
        if _skill_text_matches(skill_name, wanted)
    ]

    # Load skill rows and match custom / resolved names consistently
    rows = db.table("skills").select("candidate_id,custom_skill_name,skill_id").execute().data or []

    matched_ids: set[str] = set()
    for row in rows:
        cid = row.get("candidate_id")
        if not cid:
            continue

        custom_name = row.get("custom_skill_name") or ""
        skill_id = row.get("skill_id")

        if custom_name and _skill_text_matches(custom_name, wanted):
            matched_ids.add(cid)
            continue

        if skill_id:
            try:
                resolved_name = skill_names.get(int(skill_id), "")
            except (TypeError, ValueError):
                resolved_name = ""

            if resolved_name and _skill_text_matches(resolved_name, wanted):
                matched_ids.add(cid)

    # Keep direct skill_id filtering too for standard skills
    if std_ids:
        matched_ids |= _extract_ids(
            db.table("skills").select("candidate_id").in_("skill_id", std_ids).execute().data
        )

    return matched_ids


def _fetch_profiles(candidate_ids: set[str]) -> list[dict]:
    out, ids = [], list(candidate_ids)
    for i in range(0, len(ids), _CHUNK):
        out += db.table("profiles").select("*").in_("id", ids[i:i + _CHUNK]).execute().data or []
    return out


def _bulk_fetch(table: str, ids: list[str]) -> dict[str, list[dict]]:
    rows: list[dict] = []
    for i in range(0, len(ids), _CHUNK):
        rows += (
            db.table(table)
            .select("*")
            .in_("candidate_id", ids[i:i + _CHUNK])
            .execute()
            .data
            or []
        )

    grouped = {cid: [] for cid in ids}
    for row in rows:
        if (cid := row.get("candidate_id")) in grouped:
            grouped[cid].append(row)
    return grouped


def _fetch_emails(ids: list[str]) -> dict[str, str]:
    if not ids:
        return {}

    wanted, found = set(ids), {}
    try:
        for page in range(1, 21):
            resp = db.auth.admin.list_users(page=page, per_page=200)
            users = resp.users if hasattr(resp, "users") else (resp or [])
            if not users:
                break

            for u in users:
                uid = getattr(u, "id", None) or (u.get("id") if isinstance(u, dict) else None)
                email = getattr(u, "email", None) or (u.get("email") if isinstance(u, dict) else None)

                if uid in wanted:
                    found[uid] = email or ""
                    wanted.discard(uid)

            if not wanted or len(users) < 200:
                break

    except Exception as exc:
        logger.warning("Could not fetch emails: %s", exc)

    return found


# ---------- search endpoint ----------

@app.post("/ranking/search")
def search_candidates(
    body: SearchRequest,
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
):
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id")

    filters = body.model_dump(exclude={"sort_by", "sort_order"}, exclude_none=True)
    skill_names = _load_skill_names()

    # 1) Narrow candidate pool at DB level
    ids = _ids_by_location(body.location) if body.location else _all_candidate_ids()

    if body.major:
        ids &= _ids_by_major(body.major)

    if body.graduation_year:
        ids &= _ids_by_grad_year(body.graduation_year)

    for skill in (s for s in body.tech_skills if s.strip()):
        ids &= _ids_by_skill(skill, skill_names)

    if not ids:
        return {"results": [], "count": 0}

    # 2) Load full data for shortlisted candidates
    profiles = _fetch_profiles(ids)
    candidate_ids = [p["id"] for p in profiles]
    by = {
        table: _bulk_fetch(table, candidate_ids)
        for table in ("experiences", "education", "skills", "certificates")
    }

    # 3) Python-level filter + score
    matched: list[dict] = []
    for profile in profiles:
        cid = profile["id"]
        experiences = by["experiences"].get(cid, [])
        education = by["education"].get(cid, [])
        certificates = by["certificates"].get(cid, [])
        skill_map = build_skill_lookup(by["skills"].get(cid, []), skill_names)

        if not passes_hard_filters(profile, experiences, education, skill_map, filters):
            continue

        matched.append(
            {
                "p": profile,
                "exps": experiences,
                "edu": education,
                "certs": certificates,
                "smap": skill_map,
                "score": score_candidate(skill_map, filters, experiences),
            }
        )

    # 4) Sort: secondary by id (stable), then primary metric
    matched.sort(key=lambda x: x["p"].get("id") or "")
    primary = (
        (lambda x: _years_of_experience(x["exps"]))
        if body.sort_by == SortBy.years_experience
        else (lambda x: x["score"])
    )
    matched.sort(key=primary, reverse=body.sort_order == SortOrder.desc)

    # 5) Build response cards
    emails = _fetch_emails([x["p"]["id"] for x in matched])
    cards = [
        build_candidate_card(
            x["p"],
            x["exps"],
            x["edu"],
            x["smap"],
            x["certs"],
            x["score"],
            filters=filters,
            email=emails.get(x["p"]["id"]),
        )
        for x in matched
    ]

    logger.info("employer=%s search -> %d results", x_user_id, len(cards))
    return {"results": cards, "count": len(cards)}