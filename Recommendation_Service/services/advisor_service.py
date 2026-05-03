import hashlib
import json
import logging
import time
from openai import AsyncOpenAI

from config import NEBIUS_API_KEY, NEBIUS_BASE_URL, LLM_MODEL, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

logger = logging.getLogger(__name__)

_llm_client = AsyncOpenAI(base_url=NEBIUS_BASE_URL, api_key=NEBIUS_API_KEY)

_analysis_cache: dict[str, dict] = {}
_ANALYSIS_CACHE_TTL = 3600  # 1 hour
_CACHE_VERSION = "v2"  # bump this to invalidate all cached results after prompt changes


def _format_profile(bundle: dict) -> str:
    lines = []

    profile = bundle.get("profile", {})
    if profile.get("full_name"):
        lines.append(f"Name: {profile['full_name']}")
    if profile.get("bio"):
        lines.append(f"Bio: {profile['bio']}")
    if profile.get("location"):
        lines.append(f"Location: {profile['location']}")
    if profile.get("languages"):
        lines.append(f"Languages: {', '.join(profile['languages'])}")

    experiences = bundle.get("experiences", [])
    if experiences:
        lines.append("\nWork Experience:")
        for exp in experiences:
            start = exp.get("start_date", "")
            end = exp.get("end_date", "Present")
            lines.append(f"  - {exp.get('job_title', 'N/A')} at {exp.get('company', 'N/A')} ({start} - {end})")
            if exp.get("description"):
                lines.append(f"    {exp['description']}")

    education = bundle.get("education", [])
    if education:
        lines.append("\nEducation:")
        for edu in education:
            lines.append(
                f"  - {edu.get('degree', '')} in {edu.get('field_of_study', '')} "
                f"at {edu.get('institution', 'N/A')}"
            )

    certificates = bundle.get("certificates", [])
    if certificates:
        cert_lines = []
        for cert in certificates:
            cert_name = cert.get('certificate_name') or None
            if not cert_name:
                continue
            issuer = cert.get('issuer') or cert.get('issuer_id') or None
            if issuer and issuer != 'custom':
                cert_lines.append(f"  - {cert_name} by {issuer}")
            else:
                cert_lines.append(f"  - {cert_name}")
        if cert_lines:
            lines.append("\nCertificates (already held — do NOT recommend these):")
            lines.extend(cert_lines)

    skills = bundle.get("skills", [])
    if skills:
        skill_names = [s.get("custom_skill_name") or s.get("skill_name") or s.get("name") or "" for s in skills]
        skill_names = [s for s in skill_names if s]
        if skill_names:
            lines.append(f"\nSkills: {', '.join(skill_names)}")

    return "\n".join(lines) if lines else "No profile data available."


_SYSTEM_PROMPT = """You are an expert career advisor and CV consultant. You will receive a candidate's profile and a job description. Your task is to produce a structured JSON analysis.

CRITICAL OUTPUT RULES
---------------------
- Respond ONLY with a valid JSON object. No markdown, no explanation, no code fences, no extra text — raw JSON only.
- All string values must be plain text. No bullet points, no newlines, no HTML, no markdown inside values.
- "name", "skill", "job_title", "company" fields: keep short (1–5 words max).
- "reason", "description" fields: exactly 1 sentence, max 20 words. Direct and specific.
- "duration" field: format strictly as "YYYY - YYYY • X years" or "YYYY - Present • X years".

EXACT JSON SCHEMA TO RETURN
----------------------------
{
  "job_title": "string — job title exactly as written in the job description",
  "relevant_skills": [
    {
      "name": "string — exact skill name from the candidate profile",
      "description": "string — one sentence: which job requirement this skill satisfies"
    }
  ],
  "matching_experiences": [
    {
      "job_title": "string — candidate's exact job title",
      "company": "string — exact company name",
      "duration": "string — e.g. 2020 - Present • 4 years",
      "description": "string — one sentence: what the candidate did that maps to a specific job requirement"
    }
  ],
  "recommended_certifications": [
    {
      "name": "string — full official certification name",
      "description": "string — one sentence: which job requirement gap this cert closes"
    }
  ],
  "areas_for_development": [
    {
      "skill": "string — exact technology or tool name from the job description",
      "description": "string — one sentence: why this gap matters for this role"
    }
  ]
}

CONTENT RULES PER SECTION
--------------------------
relevant_skills: 3–5 items. Only skills the candidate actually has. Never invent skills.
matching_experiences: 1–3 items. Only genuinely relevant roles. Skip unrelated or too-junior positions.
recommended_certifications: 0–3 items. Real industry certifications that this specific candidate does NOT already hold and that directly address a gap identified in the job description. If the candidate already holds all relevant certifications, return an empty array []. Cross-check every recommendation against the EXISTING CERTIFICATIONS list in the user message — any match is forbidden.
areas_for_development: 0–4 items. Only technologies explicitly in the job description that are absent from the candidate's profile. No generic soft skills. Return [] if none.
"""


async def analyze_cv(user_id: str, bundle: dict, job_description: str) -> dict:
    cache_key = f"{_CACHE_VERSION}:{user_id}:{hashlib.sha256(job_description.encode()).hexdigest()[:16]}"
    entry = _analysis_cache.get(cache_key)
    if entry and time.time() - entry["ts"] < _ANALYSIS_CACHE_TTL:
        logger.info("Cache hit for analyze_cv user=%s", user_id)
        return entry["data"]

    profile_text = _format_profile(bundle)

    existing_cert_names = [
        cert.get("certificate_name")
        for cert in bundle.get("certificates", [])
        if cert.get("certificate_name")
    ]
    existing_certs_block = (
        "\n".join(f"  - {name}" for name in existing_cert_names)
        if existing_cert_names
        else "  (none)"
    )

    user_message = f"""Job Description:
{job_description}

Candidate Profile:
{profile_text}

EXISTING CERTIFICATIONS — the candidate already holds every item below. You MUST NOT include any of these in recommended_certifications under any circumstances:
{existing_certs_block}

Analyze the candidate's profile against the job description and return your JSON recommendations. For recommended_certifications, only suggest certifications not listed above."""

    try:
        response = await _llm_client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.3,
            max_tokens=8000,
            extra_body={"enable_thinking": False},
        )

        msg = response.choices[0].message
        raw = msg.content or getattr(msg, "reasoning_content", None) or "{}"
        logger.info("LLM raw response (first 200 chars): %s", raw[:200])
        # Strip markdown code fences if the model wraps output
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        result = json.loads(raw)

    except json.JSONDecodeError as exc:
        logger.error("LLM returned non-JSON response: %s", exc)
        raise ValueError("AI service returned an unexpected response format") from exc
    except Exception as exc:
        logger.error("LLM call failed: %s", exc)
        raise

    _analysis_cache[cache_key] = {"data": result, "ts": time.time()}

    # Save advisor report to Supabase (non-blocking)
    if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
        try:
            from supabase import create_client  # type: ignore
            sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
            sb.table("advisor_reports").insert({
                "user_id": user_id,
                "job_description": job_description,
                "feedback": result,
            }).execute()
        except Exception as exc:
            logger.warning("Failed to save advisor report for user %s: %s", user_id, exc)

    return result
