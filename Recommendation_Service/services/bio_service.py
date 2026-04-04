import logging
from openai import AsyncOpenAI

from config import NEBIUS_API_KEY, NEBIUS_BASE_URL, LLM_MODEL

logger = logging.getLogger(__name__)

_llm_client = AsyncOpenAI(base_url=NEBIUS_BASE_URL, api_key=NEBIUS_API_KEY)


async def generate_bio(bundle: dict, keywords: list[str]) -> str:
    """
    Generate a 2-3 sentence professional bio from the user's profile and keywords.
    Never raises — returns empty string on failure.
    """
    profile = bundle.get("profile", {})
    name = profile.get("full_name", "The candidate")

    experiences = bundle.get("experiences", [])
    current_role = ""
    if experiences:
        exp = experiences[0]
        current_role = f"{exp.get('job_title', '')} at {exp.get('company', '')}".strip(" at")

    skills = bundle.get("skills", [])
    skill_names = [s.get("custom_skill_name") or s.get("skill_name") or s.get("name") or "" for s in skills]
    skill_names = [s for s in skill_names if s]

    keywords_str = ", ".join(keywords) if keywords else ""
    skills_str = ", ".join(skill_names[:8]) if skill_names else ""

    prompt = f"""Write a professional CV bio for the following candidate. Return ONLY the bio text — no labels, no formatting, no quotes, no explanation.

Candidate details:
- Name: {name}
- Current/Most Recent Role: {current_role or "Not specified"}
- Skills: {skills_str or "Not specified"}
- Keywords to emphasise: {keywords_str or "None"}

Requirements:
- 2 to 3 sentences maximum
- Written in third person
- Professional tone, no buzzwords or clichés
- Highlight the keywords naturally if provided
- Plain text only"""

    try:
        response = await _llm_client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=150,
        )
        bio = (response.choices[0].message.content or "").strip()
        # Strip any accidental quotes the model might wrap around the text
        if bio.startswith('"') and bio.endswith('"'):
            bio = bio[1:-1].strip()
        return bio
    except Exception as exc:
        logger.warning("Bio generation failed: %s", exc)
        return profile.get("bio", "")
