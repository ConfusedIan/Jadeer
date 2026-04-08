"""
Ranking logic for the Jadeer Ranking Service.

The employer provides a set of search filters. Filters that are present act as
HARD filters (a candidate that fails any of them is excluded). Candidates who
pass all filters are then RANKED by how well they match the requested skills.

There are no fixed weights/percentages: the score is derived directly from the
employer's own criteria, against the candidate profiles that exist on the
platform.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Iterable


def _norm(value: Any) -> str:
    """Lowercase + strip for case-insensitive comparison. Safe on None."""
    if value is None:
        return ""
    return str(value).strip().lower()


def _years_of_experience(experiences: list[dict]) -> float:
    """
    Estimate total years of experience by summing the duration of each
    experience entry. Ongoing experiences (no end_date) count up to today.
    """
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
    """Latest end_date year across the candidate's education entries."""
    years: list[int] = []
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
    """Take the field of study from the most recent education entry."""
    latest_year = -1
    latest_major = ""
    for edu in education or []:
        field = edu.get("field_of_study") or ""
        end = edu.get("end_date")
        try:
            year = date.fromisoformat(str(end)[:10]).year if end else 0
        except (ValueError, TypeError):
            year = 0
        if field and year >= latest_year:
            latest_year = year
            latest_major = field
    return latest_major


def resolve_skill_name(skill_row: dict, standard_skill_names: dict[int, str]) -> str:
    """
    Get the display name for a skill row.

    A row in the `skills` table is either:
      - a custom skill (custom_skill_name set, skill_id null), or
      - a standard skill (skill_id set, name lives in `standard_skills`).
    """
    custom = skill_row.get("custom_skill_name")
    if custom:
        return custom
    sid = skill_row.get("skill_id")
    if sid is not None:
        return standard_skill_names.get(int(sid), "")
    return ""


def build_skill_lookup(
    skills: list[dict], standard_skill_names: dict[int, str]
) -> dict[str, dict]:
    """
    Build a {lowercased_name: skill_row} map. The resolved name is also
    injected into each row as `_resolved_name` so downstream code (e.g. the
    candidate card) can render it without re-resolving.
    """
    out: dict[str, dict] = {}
    for s in skills or []:
        name = resolve_skill_name(s, standard_skill_names)
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
    """Return True only if the candidate satisfies every filter the employer set."""

    # Major (matched against the candidate's most recent field_of_study)
    required_major = _norm(filters.get("major"))
    if required_major and required_major not in _norm(_major(education)):
        return False

    # Graduation year (exact match — matches the dropdown in the employer UI)
    required_grad = filters.get("graduation_year")
    if required_grad is not None:
        cand_grad = _graduation_year(education)
        if cand_grad != int(required_grad):
            return False

    # Location (substring match so "Riyadh" matches "Riyadh, Saudi Arabia")
    required_location = _norm(filters.get("location"))
    if required_location:
        cand_location = _norm(candidate.get("location"))
        if required_location not in cand_location:
            return False

    # Minimum years of experience
    min_years = filters.get("min_years_experience")
    if min_years is not None:
        if _years_of_experience(experiences) < float(min_years):
            return False

    # Required skills + minimum skill score
    required_skills: Iterable[str] = filters.get("skills") or []
    min_skill_score = float(filters.get("min_skill_score") or 0)
    for skill_name in required_skills:
        row = skill_map.get(_norm(skill_name))
        if not row:
            return False  # candidate doesn't have this skill at all
        score = row.get("score")
        if score is None or float(score) < min_skill_score:
            return False

    return True


def score_candidate(
    candidate: dict,
    experiences: list[dict],
    education: list[dict],
    skill_map: dict[str, dict],
    filters: dict,
) -> float:
    """
    Score = average assessment score across the requested skills.

    If the employer didn't request any specific skills, the score is the
    candidate's overall average skill score (so the most-assessed candidates
    surface naturally). The score is bounded to [0, 100] and rounded to one
    decimal so it lines up with the UI badges.
    """
    requested = [s for s in (filters.get("skills") or []) if s]

    if requested:
        scores = []
        for name in requested:
            row = skill_map.get(_norm(name))
            if row and row.get("score") is not None:
                scores.append(float(row["score"]))
        if not scores:
            return 0.0
        return round(sum(scores) / len(scores), 1)

    all_scores = [
        float(s["score"]) for s in skill_map.values()
        if s.get("score") is not None
    ]
    if not all_scores:
        return 0.0
    return round(sum(all_scores) / len(all_scores), 1)


def build_candidate_card(
    candidate: dict,
    experiences: list[dict],
    education: list[dict],
    skill_map: dict[str, dict],
    score: float,
    email: str | None = None,
) -> dict:
    """Shape the response so the employer search UI can render it directly."""
    return {
        "candidate_id": candidate.get("id"),
        "full_name": candidate.get("full_name"),
        # The schema has no `headline` column — use bio as the tagline.
        "headline": candidate.get("bio"),
        "location": candidate.get("location"),
        # Email is fetched from auth.users by the caller (after ranking),
        # since the public `profiles` table doesn't store it.
        "email": email,
        "phone": candidate.get("phone"),
        "linkedin_url": candidate.get("linkedin_url"),
        "major": _major(education),
        "graduation_year": _graduation_year(education),
        "years_of_experience": _years_of_experience(experiences),
        "skills": [
            {
                "name": s.get("_resolved_name"),
                "score": s.get("score"),
                "is_verified": bool(s.get("is_verified", False)),
            }
            for s in skill_map.values()
        ],
        "score": score,
    }
