from __future__ import annotations

import re
from datetime import date
from typing import Any


def _norm(value: Any) -> str:
    if value is None:
        return ""
    s = str(value).strip().lower()
    s = re.sub(r"[-_]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _parse_date(value: Any) -> date | None:
    try:
        return date.fromisoformat(str(value)[:10])
    except (ValueError, TypeError, AttributeError):
        return None


def _years_of_experience(experiences: list[dict]) -> float:
    today = date.today()
    total_days = 0

    for exp in experiences or []:
        start = _parse_date(exp.get("start_date"))
        end = _parse_date(exp.get("end_date")) or today
        if start and end > start:
            total_days += (end - start).days

    return round(total_days / 365.25, 1)


def _graduation_year(education: list[dict]) -> int | None:
    years = [
        d.year
        for edu in (education or [])
        if (d := _parse_date(edu.get("end_date")))
    ]
    return max(years) if years else None


def _major(education: list[dict]) -> str:
    best_year, best_field = -1, ""

    for edu in education or []:
        field = (edu.get("field_of_study") or "").strip()
        end_date = _parse_date(edu.get("end_date"))
        year = end_date.year if end_date else 0

        if field and year >= best_year:
            best_year, best_field = year, field

    return best_field


def _skill_name(skill: dict, standard_skill_names: dict[int, str]) -> str:
    skill_id = skill.get("skill_id")
    return (
        (standard_skill_names.get(int(skill_id)) if skill_id else None)
        or (skill.get("custom_skill_name") or "")
    ).strip()


def _is_better_skill(new: dict, existing: dict) -> bool:
    new_verified = bool(new.get("is_verified"))
    old_verified = bool(existing.get("is_verified"))

    if new_verified != old_verified:
        return new_verified

    new_score = float(new.get("score") or 0)
    old_score = float(existing.get("score") or 0)

    if new_score != old_score:
        return new_score > old_score

    try:
        return int(new.get("id") or 0) > int(existing.get("id") or 0)
    except (ValueError, TypeError):
        return False


def build_skill_lookup(
    skills: list[dict],
    standard_skill_names: dict[int, str],
) -> dict[str, dict]:
    lookup: dict[str, dict] = {}

    for skill in skills or []:
        name = _skill_name(skill, standard_skill_names)
        if not name:
            continue

        key = _norm(name)
        enriched = {**skill, "_resolved_name": name}

        if key not in lookup or _is_better_skill(enriched, lookup[key]):
            lookup[key] = enriched

    return lookup


def _find_skill(skill_map: dict[str, dict], name: str) -> dict | None:
    key = _norm(name)

    if key in skill_map:
        return skill_map[key]

    pattern = re.compile(r"(?<![a-z0-9])" + re.escape(key) + r"(?![a-z0-9])")
    for stored_name, row in skill_map.items():
        if pattern.search(stored_name):
            return row

    return None


def passes_hard_filters(
    candidate: dict,
    experiences: list[dict],
    education: list[dict],
    skill_map: dict[str, dict],
    filters: dict,
) -> bool:
    major = _norm(filters.get("major"))
    if major and major not in _norm(_major(education)):
        return False

    graduation_year = filters.get("graduation_year")
    if graduation_year is not None and _graduation_year(education) != int(graduation_year):
        return False

    location = _norm(filters.get("location"))
    if location and location not in _norm(candidate.get("location")):
        return False

    min_exp = filters.get("min_years_experience")
    if min_exp is not None and _years_of_experience(experiences) < float(min_exp):
        return False

    for skill_filter in filters.get("soft_skills") or []:
        row = _find_skill(skill_map, skill_filter["name"])
        if row is None:
            return False

        score = row.get("score")
        if score is None or float(score) < float(skill_filter.get("min_score") or 0):
            return False

    for name in filters.get("tech_skills") or []:
        if _find_skill(skill_map, name) is None:
            return False

    return True


def score_candidate(skill_map: dict[str, dict], filters: dict) -> float:
    soft_skills = filters.get("soft_skills") or []

    if soft_skills:
        scores = [
            float(row["score"])
            for skill_filter in soft_skills
            if (row := _find_skill(skill_map, skill_filter["name"])) and row.get("score") is not None
        ]
    else:
        scores = [
            float(skill["score"])
            for skill in skill_map.values()
            if skill.get("score") is not None
        ]

    return round(sum(scores) / len(scores), 1) if scores else 0.0


def _strip(rows: list[dict]) -> list[dict]:
    return [{k: v for k, v in row.items() if k != "candidate_id"} for row in rows]


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
    requested_names = (
        {_norm(skill["name"]) for skill in (filters.get("soft_skills") or [])}
        | {_norm(name) for name in (filters.get("tech_skills") or [])}
    )

    requested_skills = []
    other_skills = []

    for key, skill in skill_map.items():
        entry = {
            "name": skill["_resolved_name"],
            "score": skill.get("score"),
            "category": skill.get("category"),
            "is_verified": bool(skill.get("is_verified", False)),
        }
        (requested_skills if key in requested_names else other_skills).append(entry)

    return {
        "avg_soft_skill_score": score,
        "years_of_experience": _years_of_experience(experiences),
        "major": _major(education),
        "graduation_year": _graduation_year(education),
        "email": email,
        "requested_skills": requested_skills,
        "other_skills": other_skills,
        "profile": candidate,
        "experiences": _strip(experiences),
        "education": _strip(education),
        "certificates": _strip(certificates),
    }