from __future__ import annotations
from datetime import date
from typing import Any


def _norm(value: Any) -> str:
    return "" if value is None else str(value).strip().lower()


def _years_of_experience(experiences: list[dict]) -> float:
    total_days = 0
    today = date.today()
    for exp in experiences or []:
        start = exp.get("start_date")
        end = exp.get("end_date") or today.isoformat()
        try:
            s = date.fromisoformat(str(start)[:10])
            e = date.fromisoformat(str(end)[:10])
            if e > s:
                total_days += (e - s).days
        except (ValueError, TypeError):
            continue
    return round(total_days / 365.25, 1)


def _graduation_year(education: list[dict]) -> int | None:
    years = []
    for edu in education or []:
        end = edu.get("end_date")
        if not end:
            continue
        try:
            years.append(date.fromisoformat(str(end)[:10]).year)
        except (ValueError, TypeError):
            continue
    return max(years) if years else None


def _major(education: list[dict]) -> str:
    latest_year, latest_major = -1, ""
    for edu in education or []:
        field = edu.get("field_of_study") or ""
        end = edu.get("end_date")
        try:
            year = date.fromisoformat(str(end)[:10]).year if end else 0
        except (ValueError, TypeError):
            year = 0
        if field and year >= latest_year:
            latest_year, latest_major = year, field
    return latest_major


def _strip(rows: list[dict]) -> list[dict]:
    return [{k: v for k, v in row.items() if k != "candidate_id"} for row in rows]


def build_skill_lookup(skills: list[dict], standard_skill_names: dict[int, str]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for s in skills or []:
        sid = s.get("skill_id")
        name = (standard_skill_names.get(int(sid)) if sid else None) or s.get("custom_skill_name", "")
        if not name:
            continue
        s["_resolved_name"] = name
        out[_norm(name)] = s
    return out


def passes_hard_filters(
    candidate: dict,
    experiences: list[dict],
    education: list[dict],
    skill_map: dict[str, dict],
    filters: dict,
) -> bool:
    if (major := _norm(filters.get("major"))) and major not in _norm(_major(education)):
        return False

    if (grad := filters.get("graduation_year")) is not None and _graduation_year(education) != int(grad):
        return False

    if (loc := _norm(filters.get("location"))) and loc not in _norm(candidate.get("location")):
        return False

    if (min_exp := filters.get("min_years_experience")) is not None:
        if _years_of_experience(experiences) < float(min_exp):
            return False

    for sf in (filters.get("soft_skills") or []):
        row = skill_map.get(_norm(sf["name"]))
        if not row or row.get("score") is None or float(row["score"]) < float(sf.get("min_score", 0)):
            return False

    for skill_name in (filters.get("tech_skills") or []):
        if not skill_map.get(_norm(skill_name)):
            return False

    return True


def score_candidate(skill_map: dict[str, dict], filters: dict) -> float:
    """Average of the requested soft skill scores as stored — no recalculation."""
    soft_skills = filters.get("soft_skills") or []

    if soft_skills:
        scores = [
            float(skill_map[key]["score"])
            for sf in soft_skills
            if (key := _norm(sf["name"])) in skill_map and skill_map[key].get("score") is not None
        ]
    else:
        scores = [float(s["score"]) for s in skill_map.values() if s.get("score") is not None]

    return round(sum(scores) / len(scores), 1) if scores else 0.0


def build_candidate_card(
    candidate: dict,
    experiences: list[dict],
    education: list[dict],
    skill_map: dict[str, dict],
    certificates: list[dict],
    score: float,
    filters: dict,
    email: str | None = None,
) -> dict:
    # Split skills into what the employer filtered on vs everything else
    requested_names = (
        {_norm(sf["name"]) for sf in (filters.get("soft_skills") or [])} |
        {_norm(n)          for n  in (filters.get("tech_skills")  or [])}
    )

    requested_skills = []
    other_skills = []
    for key, s in skill_map.items():
        entry = {
            "name":        s.get("_resolved_name"),
            "score":       s.get("score"),
            "category":    s.get("category"),
            "is_verified": bool(s.get("is_verified", False)),
        }
        (requested_skills if key in requested_names else other_skills).append(entry)

    return {
        # Computed fields
        "avg_soft_skill_score": score,
        "years_of_experience":  _years_of_experience(experiences),
        "major":                _major(education),
        "graduation_year":      _graduation_year(education),
        "email":                email,

        # Skills split into filtered vs others
        "requested_skills": requested_skills,
        "other_skills":     other_skills,

        # Everything else — raw from DB, all columns included
        "profile":       candidate,
        "experiences":   _strip(experiences),
        "education":     _strip(education),
        "certificates":  _strip(certificates),
    }
