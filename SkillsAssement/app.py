
import os
import json
import re
import io
import csv
from datetime import datetime
from typing import Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# ── App Setup ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="O*NET Soft Skills Assessment API",
    description="Matches Supabase user profiles to O*NET occupations and assesses soft skills",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Supabase Client (read-only) ─────────────────────────────────────────────
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# ── Nebius LLM Client ────────────────────────────────────────────────────────
NEBIUS_API_KEY = os.environ.get("NEBIUS_API_KEY")
if not NEBIUS_API_KEY:
    raise ValueError("NEBIUS_API_KEY must be set in .env")


def get_llm_client() -> OpenAI:
    return OpenAI(
        base_url="https://api.tokenfactory.nebius.com/v1/",
        api_key=NEBIUS_API_KEY,
    )


# ── Constants ────────────────────────────────────────────────────────────────
SOFT_SKILL_IDS = {
    "2.B.1.b": "Coordination",
    "2.B.1.e": "Instructing",
    "2.B.1.d": "Negotiation",
    "2.B.1.c": "Persuasion",
    "2.B.1.f": "Service Orientation",
    "2.B.1.a": "Social Perceptiveness",
    "2.A.2.b": "Active Learning",
    "2.A.1.b": "Active Listening",
    "2.D.1.a": "Complex Problem Solving",
    "2.A.2.a": "Critical Thinking",
    "2.C.1.a": "Judgment and Decision Making",
    "2.A.2.c": "Learning Strategies",
    "2.A.2.d": "Monitoring",
    "2.E.2.a": "Time Management",
}

SOCIAL_SKILLS = [
    "Coordination", "Instructing", "Negotiation",
    "Persuasion", "Service Orientation", "Social Perceptiveness",
]
THINKING_SKILLS = [
    "Active Learning", "Active Listening", "Complex Problem Solving",
    "Critical Thinking", "Judgment and Decision Making",
    "Learning Strategies", "Monitoring", "Time Management",
]

TARGET_ELEMENT_IDS = list(SOFT_SKILL_IDS.keys())
ALL_SKILL_NAMES = list(SOFT_SKILL_IDS.values())


# ── Load O*NET Excel Data ───────────────────────────────────────────────────
def load_skills_data() -> pd.DataFrame:
    """Load and filter Skills.xlsx for the 14 target soft skills."""
    df = pd.read_excel("Skills.xlsx")
    return df[df["Element ID"].isin(TARGET_ELEMENT_IDS)]


DF = load_skills_data()


def get_occupations() -> dict:
    """Return dict of {title: code} for all occupations."""
    occ = DF[["O*NET-SOC Code", "Title"]].drop_duplicates().sort_values("Title")
    return dict(zip(occ["Title"], occ["O*NET-SOC Code"]))


OCC_MAP = get_occupations()
OCC_TITLES = list(OCC_MAP.keys())


def get_skill_data(occ_code: str, selected_skills: list[str]) -> list[dict]:
    """Get importance/level data for selected skills and occupation from O*NET."""
    skill_ids = [k for k, v in SOFT_SKILL_IDS.items() if v in selected_skills]
    filtered = DF[(DF["O*NET-SOC Code"] == occ_code) & (DF["Element ID"].isin(skill_ids))]

    results = []
    for skill_name in selected_skills:
        skill_rows = filtered[filtered["Element Name"] == skill_name]
        imp_row = skill_rows[skill_rows["Scale Name"] == "Importance"]
        lvl_row = skill_rows[skill_rows["Scale Name"] == "Level"]

        if imp_row.empty and lvl_row.empty:
            continue

        raw_imp = float(imp_row["Data Value"].values[0]) if not imp_row.empty else 0
        raw_lvl = float(lvl_row["Data Value"].values[0]) if not lvl_row.empty else 0

        not_relevant = False
        if not lvl_row.empty:
            nr_val = lvl_row["Not Relevant"].values[0]
            if isinstance(nr_val, str) and nr_val.strip().upper() == "Y":
                not_relevant = True

        suppress = False
        for row_set in [imp_row, lvl_row]:
            if not row_set.empty:
                rs_val = row_set["Recommend Suppress"].values[0]
                if isinstance(rs_val, str) and rs_val.strip().upper() in ("Y", "YES", "1"):
                    suppress = True

        std_imp = round(((raw_imp - 1) / 4) * 100, 1) if raw_imp > 0 else 0
        std_lvl = round((raw_lvl / 7) * 100, 1) if raw_lvl > 0 else 0

        category = "Social Skills" if skill_name in SOCIAL_SKILLS else "Thinking Skills"
        if std_imp >= 50:
            priority = "HIGH"
        elif std_imp >= 25:
            priority = "MEDIUM"
        else:
            priority = "LOW"

        results.append({
            "skill": skill_name,
            "category": category,
            "raw_importance": round(raw_imp, 2),
            "raw_level": round(raw_lvl, 2),
            "standardized_importance": std_imp,
            "standardized_level": std_lvl,
            "priority": priority,
            "not_relevant": not_relevant,
            "suppress": suppress,
        })

    return results


def calc_pass_threshold(skill_data: list[dict]) -> tuple[int, str]:
    """Determine pass threshold based on skill importance."""
    relevant = [s for s in skill_data if not s["not_relevant"]]
    if not relevant:
        return 3, "Default threshold (no relevant skill data)"

    avg_imp = sum(s["standardized_importance"] for s in relevant) / len(relevant)
    if avg_imp >= 50:
        return 4, f"High threshold (4/5) — standardized importance is high ({avg_imp:.0f})"
    elif avg_imp >= 25:
        return 3, f"Standard threshold (3/5) — standardized importance is moderate ({avg_imp:.0f})"
    else:
        return 2, f"Low threshold (2/5) — standardized importance is low ({avg_imp:.0f})"


def save_assessment_result(
    user_client: Client,
    user_id: str,
    result_data: dict,
) -> Optional[dict]:
    """Save assessment result to the assessment_results table in Supabase."""
    try:
        row = {
            "user_id": user_id,
            "occupation_title": result_data.get("occupation_title", ""),
            "occupation_code": result_data.get("occupation_code", ""),
            "skill_name": result_data.get("skill_name", ""),
            "skill_category": result_data.get("skill_category", ""),
            "skill_priority": result_data.get("skill_priority", ""),
            "score": result_data.get("score", 0),
            "total_questions": result_data.get("total_questions", 0),
            "percentage": result_data.get("percentage", 0),
            "passed": result_data.get("passed", False),
            "pass_threshold": result_data.get("pass_threshold", 3),
            "threshold_reason": result_data.get("threshold_reason", ""),
            "question_results": json.dumps(result_data.get("question_results", [])),
        }
        insert_result = user_client.table("assessment_results").insert(row).execute()
        return insert_result.data[0] if insert_result.data else None
    except Exception as e:
        print(f"[WARNING] Failed to save assessment result: {e}")
        return None


def _try_auth(authorization: Optional[str]):
    """Try to authenticate user from an optional Bearer token. Returns (user_client, user) or (None, None)."""
    if not authorization or not authorization.startswith("Bearer "):
        return None, None
    try:
        token = authorization.split(" ", 1)[1]
        user_client, user = get_supabase_user(token)
        return user_client, user
    except Exception:
        return None, None


# ── Supabase User Data Fetching ──────────────────────────────────────────────
def get_supabase_user(access_token: str) -> tuple[Client, dict]:
    """Authenticate and return user client + user info. Read-only."""
    try:
        user_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        user_client.auth.set_session(access_token, access_token)
        user = user_client.auth.get_user(access_token)
        if not user or not user.user:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return user_client, user.user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")


def fetch_user_data(user_client: Client, user_id: str) -> dict:
    """Pull candidate profile, skills, certificates, and latest CV from Supabase."""
    data = {"user_id": user_id}

    # 1. Candidate profile
    try:
        result = user_client.table("candidate_profiles").select("*").eq("user_id", user_id).execute()
        data["profile"] = result.data[0] if result.data else {}
    except Exception:
        data["profile"] = {}

    # 2. Skills
    try:
        result = user_client.table("skills").select("*").eq("user_id", user_id).execute()
        data["skills"] = result.data or []
    except Exception:
        data["skills"] = []

    # 3. Certificates
    try:
        result = user_client.table("certificates").select("*").eq("user_id", user_id).execute()
        data["certificates"] = result.data or []
    except Exception:
        data["certificates"] = []

    # 4. Latest CV (resume_data JSON)
    try:
        result = (
            user_client.table("cvs")
            .select("resume_data, score_data, filename, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        data["latest_cv"] = result.data[0] if result.data else {}
    except Exception:
        data["latest_cv"] = {}

    return data


def build_occupation_prompt(user_data: dict) -> str:
    """Build a structured text summary from Supabase user data for LLM occupation matching."""
    parts = []

    profile = user_data.get("profile", {})
    if profile.get("professional_headline"):
        parts.append(f"Job Title/Headline: {profile['professional_headline']}")
    if profile.get("major_specialization"):
        parts.append(f"Major/Specialization: {profile['major_specialization']}")
    if profile.get("years_of_experience"):
        parts.append(f"Years of Experience: {profile['years_of_experience']}")
    if profile.get("bio"):
        parts.append(f"About Me: {profile['bio']}")
    if profile.get("preferred_job_type"):
        parts.append(f"Preferred Job Type: {profile['preferred_job_type']}")

    # Skills from skills table
    skills = user_data.get("skills", [])
    if skills:
        skill_names = [s.get("skill_name", "") for s in skills if s.get("skill_name")]
        if skill_names:
            parts.append(f"Skills: {', '.join(skill_names)}")

    # Certificates
    certs = user_data.get("certificates", [])
    if certs:
        cert_names = [c.get("certificate_name", "") for c in certs if c.get("certificate_name")]
        if cert_names:
            parts.append(f"Certificates: {', '.join(cert_names)}")

    # CV data
    cv = user_data.get("latest_cv", {})
    resume_data = cv.get("resume_data", {})
    if isinstance(resume_data, dict):
        # Experience
        experience = resume_data.get("experience", [])
        if isinstance(experience, list) and experience:
            latest = experience[0] if experience else {}
            if isinstance(latest, dict):
                title = latest.get("title", "")
                company = latest.get("company", "")
                responsibilities = latest.get("responsibilities", "")
                if title:
                    parts.append(f"Most Recent Job Title: {title}")
                if company:
                    parts.append(f"Company: {company}")
                if responsibilities:
                    if isinstance(responsibilities, list):
                        responsibilities = "; ".join(responsibilities)
                    parts.append(f"Key Responsibilities: {responsibilities}")

        # Education
        education = resume_data.get("education", [])
        if isinstance(education, list) and education:
            latest_edu = education[0] if education else {}
            if isinstance(latest_edu, dict):
                degree = latest_edu.get("degree", "")
                field = latest_edu.get("field", "")
                institution = latest_edu.get("institution", "")
                if degree or field:
                    parts.append(f"Education: {degree} in {field}" + (f" from {institution}" if institution else ""))

        # Summary from CV
        summary = resume_data.get("summary", "")
        if summary and isinstance(summary, str):
            parts.append(f"Professional Summary: {summary}")

    if not parts:
        return "No user data available."

    return "\n".join(parts)


def match_occupation_from_summary(summary: str) -> str:
    """Use LLM to match a user's structured data to the closest O*NET occupation."""
    client = get_llm_client()
    occ_text = "\n".join(f"- {o}" for o in OCC_TITLES)

    response = client.chat.completions.create(
        model="Qwen/Qwen2.5-Coder-7B-fast",
        messages=[
            {
                "role": "system",
                "content": f"""You are an O*NET occupation classifier. Given a user's profile data, determine the SINGLE most matching occupation from the provided list.

RESPOND WITH ONLY the exact occupation title from the list, nothing else. No explanation, no quotes, just the title exactly as it appears in the list.

Available occupations:
{occ_text}""",
            },
            {"role": "user", "content": f"Match this person to an occupation:\n\n{summary}"},
        ],
    )

    matched = response.choices[0].message.content.strip().strip('"').strip("'")

    # Exact match
    matched_lower = matched.lower()
    for occ in OCC_TITLES:
        if occ.lower() == matched_lower:
            return occ

    # Partial match fallback
    for occ in OCC_TITLES:
        if matched_lower in occ.lower() or occ.lower() in matched_lower:
            return occ

    return matched


# ── AI Question Generation ──────────────────────────────────────────────────
def _sanitize_json(s: str) -> str:
    """Sanitize invalid control characters inside JSON string values."""
    out = []
    in_string = False
    escape = False
    for ch in s:
        if escape:
            out.append(ch)
            escape = False
            continue
        if ch == '\\' and in_string:
            out.append(ch)
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            out.append(ch)
            continue
        if in_string and ord(ch) < 0x20:
            if ch == '\n':
                out.append('\\n')
            elif ch == '\r':
                out.append('\\r')
            elif ch == '\t':
                out.append('\\t')
            else:
                out.append(' ')
            continue
        out.append(ch)
    return ''.join(out)


def generate_assessment(occupation_title: str, skill_data: list[dict]) -> list[dict]:
    """Generate 5 scenario-based MCQ questions using the Nebius API (with retry)."""
    client = get_llm_client()

    relevant_skills = [s for s in skill_data if not s["not_relevant"]]
    if not relevant_skills:
        return []

    skills_info = "\n".join([
        f"- {s['skill']} (Category: {s['category']}) — "
        f"Importance: {s['standardized_importance']}/100 ({s['priority']}), "
        f"Level: {s['standardized_level']}/100 "
        f"({'Complex scenarios' if s['standardized_level'] >= 60 else 'Intermediate scenarios' if s['standardized_level'] >= 30 else 'Basic scenarios'})"
        f"{' ⚠️ LOW CONFIDENCE RATING' if s['suppress'] else ''}"
        for s in relevant_skills
    ])

    skill_rule = (
        "ALL 5 questions MUST target the single skill provided above. Do NOT invent or use any other skills."
        if len(relevant_skills) == 1
        else "Cover at least 2 different skills from the list above. Do NOT invent skills outside the provided list."
    )

    system_prompt = f"""You are an expert O*NET-based assessment designer.

Create exactly 5 SCENARIO-BASED multiple-choice questions for the occupation: "{occupation_title}"

SKILLS DATA (from official O*NET database):
{skills_info}

DIFFICULTY RULES (follow strictly):
- Skills with Standardized Importance ≥ 50: HIGH priority — allocate more questions to these.
- Skills with Standardized Importance 25–49: MEDIUM priority.
- Skills with Standardized Importance < 25: LOW priority — fewer/easier questions.

- Skills with Standardized Level ≥ 60: Generate COMPLEX, context-rich scenarios requiring higher-level reasoning.
- Skills with Standardized Level 30–59: Generate INTERMEDIATE scenarios with some nuance.
- Skills with Standardized Level < 30: Generate BASIC, straightforward scenarios.

RULES:
1. Exactly 5 questions total.
2. Prioritize skills with higher Standardized Importance.
3. {skill_rule}
4. Each question MUST be a realistic workplace scenario specific to "{occupation_title}".
5. Each question has exactly 4 options labeled A, B, C, D.
6. Exactly one option is correct.
7. Include which skill the question targets.
8. Include a brief explanation of why the correct answer is best.

CRITICAL: Your response must be ONLY a valid JSON array. Do not include any text before or after the JSON. Do not use markdown code fences. Start your response with [ and end with ].
Each element must have this exact schema:
{{
  "question": "...",
  "target_skill": "...",
  "options": {{
    "A": "...",
    "B": "...",
    "C": "...",
    "D": "..."
  }},
  "correct": "A",
  "explanation": "..."
}}"""

    MAX_RETRIES = 3
    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model="Qwen/Qwen2.5-Coder-7B-fast",
                temperature=0.7,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Generate the 5-question assessment for {occupation_title}. Respond with ONLY a JSON array, no other text."},
                ],
            )

            raw = response.choices[0].message.content.strip()

            # Strip markdown fences
            raw = re.sub(r'^```(?:json|JSON)?\s*\n?', '', raw)
            raw = re.sub(r'\n?```\s*$', '', raw)
            raw = raw.strip()

            # Sanitize control characters
            raw = _sanitize_json(raw)

            # Try to parse JSON with multiple strategies
            result = None

            # Strategy 1: direct parse
            try:
                result = json.loads(raw)
            except json.JSONDecodeError:
                pass

            # Strategy 2: extract outermost [...]
            if result is None:
                arr_match = re.search(r'\[.*\]', raw, re.DOTALL)
                if arr_match:
                    try:
                        result = json.loads(arr_match.group(0))
                    except json.JSONDecodeError:
                        pass

            # Strategy 3: raw_decode
            if result is None:
                try:
                    decoder = json.JSONDecoder()
                    result, _ = decoder.raw_decode(raw)
                except json.JSONDecodeError:
                    raise ValueError("Could not parse AI response as JSON.")

            # Normalise into a list
            if isinstance(result, dict):
                for key in ("questions", "data", "assessment", "quiz", "items"):
                    if key in result and isinstance(result[key], list):
                        result = result[key]
                        break
                if isinstance(result, dict):
                    result = [result]

            if not isinstance(result, list):
                raise ValueError("AI response was not a JSON array.")

            # Validate each question
            required_keys = {"question", "options", "correct"}
            validated = []
            for item in result:
                if isinstance(item, dict) and required_keys.issubset(item.keys()):
                    if isinstance(item.get("options"), dict):
                        validated.append(item)

            if not validated:
                raise ValueError("AI returned no valid questions.")

            return validated

        except Exception as e:
            last_error = e
            continue

    # All retries exhausted
    raise ValueError(f"Failed after {MAX_RETRIES} attempts. Last error: {last_error}")


# ── Pydantic Models ──────────────────────────────────────────────────────────
class AssessmentRequest(BaseModel):
    occupation_code: str
    skill_name: str


class EvaluateRequest(BaseModel):
    occupation_code: str
    occupation_title: str
    skill_name: str
    questions: list[dict]
    answers: dict[str, str]  # {"0": "A", "1": "C", ...}


class FullAssessmentRequest(BaseModel):
    occupation_code: str
    skill_name: str
    answers: Optional[dict[str, str]] = None  # If provided, evaluates immediately


# ── API Endpoints ────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "service": "O*NET Soft Skills Assessment API",
        "version": "1.0.0",
        "endpoints": [
            "POST /assessment/match-occupation",
            "POST /assessment/generate-assessment",
            "POST /assessment/evaluate",
            "POST /assessment/full-assessment",
            "GET /assessment/skills-list",
            "GET /assessment/occupations",
        ],
    }


@app.get("/assessment/skills-list")
def list_skills():
    """List all 14 O*NET soft skills available for assessment."""
    return {
        "social_skills": SOCIAL_SKILLS,
        "thinking_skills": THINKING_SKILLS,
        "all_skills": ALL_SKILL_NAMES,
    }


@app.get("/assessment/occupations")
def list_occupations():
    """List all available O*NET occupations."""
    return {
        "count": len(OCC_MAP),
        "occupations": [{"title": t, "code": c} for t, c in OCC_MAP.items()],
    }


@app.post("/assessment/match-occupation")
def match_occupation(authorization: str = Header(...)):
    """
    Pull user data from Supabase and match to the closest O*NET occupation.
    Returns the matched occupation + all 14 soft skill priorities for that occupation.

    Requires: Bearer <supabase_access_token>
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header must be 'Bearer <token>'")

    token = authorization.split(" ", 1)[1]
    user_client, user = get_supabase_user(token)
    user_data = fetch_user_data(user_client, user.id)

    # Build prompt from user data
    user_summary = build_occupation_prompt(user_data)

    if user_summary == "No user data available.":
        raise HTTPException(
            status_code=400,
            detail="No profile data found. Please complete your Jadeer profile first.",
        )

    # LLM match to O*NET occupation
    matched_title = match_occupation_from_summary(user_summary)
    occ_code = OCC_MAP.get(matched_title)

    if not occ_code:
        raise HTTPException(
            status_code=404,
            detail=f"Could not find a matching O*NET occupation for: '{matched_title}'",
        )

    # Get all 14 soft skills data for this occupation
    all_skill_data = get_skill_data(occ_code, ALL_SKILL_NAMES)

    # Sort by priority (HIGH first)
    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    all_skill_data.sort(key=lambda s: (priority_order.get(s["priority"], 3), -s["standardized_importance"]))

    return {
        "user_id": user.id,
        "user_email": user.email,
        "user_summary_sent_to_llm": user_summary,
        "occupation": {
            "title": matched_title,
            "code": occ_code,
        },
        "skills_overview": [
            {
                "skill_name": s["skill"],
                "category": s["category"],
                "priority": s["priority"],
                "standardized_importance": s["standardized_importance"],
                "standardized_level": s["standardized_level"],
                "raw_importance": s["raw_importance"],
                "raw_level": s["raw_level"],
                "not_relevant": s["not_relevant"],
                "suppress": s["suppress"],
            }
            for s in all_skill_data
        ],
        "available_skills_for_assessment": [
            s["skill"] for s in all_skill_data if not s["not_relevant"]
        ],
    }


@app.post("/assessment/generate-assessment")
def api_generate_assessment(req: AssessmentRequest):
    """
    Generate 5 scenario-based MCQ questions for a given occupation + skill.
    Use the occupation_code from /api/match-occupation response.
    """
    # Validate occupation
    occ_title = None
    for title, code in OCC_MAP.items():
        if code == req.occupation_code:
            occ_title = title
            break

    if not occ_title:
        raise HTTPException(status_code=404, detail=f"Occupation code '{req.occupation_code}' not found")

    if req.skill_name not in ALL_SKILL_NAMES:
        raise HTTPException(
            status_code=400,
            detail=f"Skill '{req.skill_name}' is not one of the 14 O*NET soft skills. Available: {ALL_SKILL_NAMES}",
        )

    # Get skill data for this occupation + skill
    skill_data = get_skill_data(req.occupation_code, [req.skill_name])

    if not skill_data:
        raise HTTPException(
            status_code=404,
            detail=f"No O*NET data found for skill '{req.skill_name}' in occupation '{occ_title}'",
        )

    relevant = [s for s in skill_data if not s["not_relevant"]]
    if not relevant:
        raise HTTPException(
            status_code=400,
            detail=f"Skill '{req.skill_name}' is marked as NOT RELEVANT for '{occ_title}'",
        )

    # Generate questions
    try:
        questions = generate_assessment(occ_title, relevant)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate questions: {str(e)}")

    return {
        "occupation_title": occ_title,
        "occupation_code": req.occupation_code,
        "skill_name": req.skill_name,
        "skill_data": relevant[0],
        "questions": questions,
        "total_questions": len(questions),
    }


@app.post("/assessment/evaluate")
def api_evaluate(req: EvaluateRequest, authorization: Optional[str] = Header(None)):
    """
    Evaluate answers and return assessment_results-compatible output.

    Output covers: user assessment result with score, pass/fail,
    skill priority, threshold reasoning, and per-question breakdown.

    If a valid Bearer token is provided in the Authorization header,
    the result is also saved to the user's assessment_results in Supabase.
    """
    questions = req.questions
    answers = req.answers

    if not questions:
        raise HTTPException(status_code=400, detail="No questions provided")

    # Get skill data
    skill_data = get_skill_data(req.occupation_code, [req.skill_name])
    relevant = [s for s in skill_data if not s["not_relevant"]]

    # Score answers
    score = 0
    total = len(questions)
    question_results = []

    for i, q in enumerate(questions):
        user_answer = answers.get(str(i), "")
        correct_answer = q.get("correct", "")
        is_correct = user_answer.upper().strip() == correct_answer.upper().strip()

        if is_correct:
            score += 1

        question_results.append({
            "question_number": i + 1,
            "question": q.get("question", ""),
            "target_skill": q.get("target_skill", req.skill_name),
            "options": q.get("options", {}),
            "user_answer": user_answer,
            "correct_answer": correct_answer,
            "is_correct": is_correct,
            "explanation": q.get("explanation", ""),
        })

    # Calculate pass/fail
    threshold, threshold_reason = calc_pass_threshold(skill_data)
    passed = score >= threshold
    percentage = round((score / total) * 100) if total > 0 else 0

    # Get skill priority
    skill_priority = relevant[0]["priority"] if relevant else "UNKNOWN"
    skill_importance = relevant[0]["standardized_importance"] if relevant else 0
    skill_level = relevant[0]["standardized_level"] if relevant else 0

    # ── assessment_results compatible output ──────────────────────────────
    result = {
        # Identification
        "occupation_title": req.occupation_title,
        "occupation_code": req.occupation_code,
        "assessed_at": datetime.now().isoformat(),

        # Skill info
        "skill_name": req.skill_name,
        "skill_category": relevant[0]["category"] if relevant else "Unknown",
        "skill_priority": skill_priority,
        "skill_standardized_importance": skill_importance,
        "skill_standardized_level": skill_level,

        # Score
        "score": score,
        "total_questions": total,
        "percentage": percentage,

        # Pass/Fail
        "passed": passed,
        "pass_threshold": threshold,
        "threshold_reason": threshold_reason,

        # Per-question breakdown
        "question_results": question_results,
    }

    # ── Save to Supabase if authenticated ─────────────────────────────────
    user_client, user = _try_auth(authorization)
    if user_client and user:
        saved = save_assessment_result(user_client, user.id, result)
        result["saved_to_supabase"] = saved is not None
        if saved:
            result["supabase_record_id"] = saved.get("id")
    else:
        result["saved_to_supabase"] = False

    return result


# ── Full Assessment Endpoint ─────────────────────────────────────────────────
@app.post("/assessment/full-assessment")
def api_full_assessment(req: FullAssessmentRequest, authorization: Optional[str] = Header(None)):
    """
    Run the full assessment pipeline in one call.

    - If `answers` is NOT provided: generates and returns 5 MCQ questions.
    - If `answers` IS provided: generates questions, evaluates answers,
      and returns the complete assessment result with score and pass/fail.

    Request body:
        occupation_code: str  (e.g. "15-1254.00")
        skill_name: str       (e.g. "Negotiation")
        answers: optional dict (e.g. {"0": "A", "1": "C", "2": "B", "3": "D", "4": "A"})

    If a valid Bearer token is provided in the Authorization header,
    evaluated results are also saved to the user's assessment_results in Supabase.
    """
    # ── Validate occupation ──────────────────────────────────────────────
    occ_title = None
    for title, code in OCC_MAP.items():
        if code == req.occupation_code:
            occ_title = title
            break

    if not occ_title:
        raise HTTPException(status_code=404, detail=f"Occupation code '{req.occupation_code}' not found")

    if req.skill_name not in ALL_SKILL_NAMES:
        raise HTTPException(
            status_code=400,
            detail=f"Skill '{req.skill_name}' is not one of the 14 O*NET soft skills. Available: {ALL_SKILL_NAMES}",
        )

    # ── Get skill data ───────────────────────────────────────────────────
    skill_data = get_skill_data(req.occupation_code, [req.skill_name])

    if not skill_data:
        raise HTTPException(
            status_code=404,
            detail=f"No O*NET data found for skill '{req.skill_name}' in occupation '{occ_title}'",
        )

    relevant = [s for s in skill_data if not s["not_relevant"]]
    if not relevant:
        raise HTTPException(
            status_code=400,
            detail=f"Skill '{req.skill_name}' is marked as NOT RELEVANT for '{occ_title}'",
        )

    # ── Generate questions ───────────────────────────────────────────────
    try:
        questions = generate_assessment(occ_title, relevant)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate questions: {str(e)}")

    # ── Base response (questions only) ───────────────────────────────────
    response = {
        "occupation": {
            "title": occ_title,
            "code": req.occupation_code,
        },
        "skill": {
            "name": req.skill_name,
            "category": relevant[0]["category"],
            "priority": relevant[0]["priority"],
            "standardized_importance": relevant[0]["standardized_importance"],
            "standardized_level": relevant[0]["standardized_level"],
            "raw_importance": relevant[0]["raw_importance"],
            "raw_level": relevant[0]["raw_level"],
        },
        "questions": questions,
        "total_questions": len(questions),
    }

    # ── If no answers provided, return questions for the client to display ─
    if req.answers is None:
        response["status"] = "questions_generated"
        response["message"] = "Answer the questions and re-submit with the 'answers' field to get your result."
        return response

    # ── Evaluate answers ─────────────────────────────────────────────────
    answers = req.answers
    score = 0
    total = len(questions)
    question_results = []

    for i, q in enumerate(questions):
        user_answer = answers.get(str(i), "")
        correct_answer = q.get("correct", "")
        is_correct = user_answer.upper().strip() == correct_answer.upper().strip()

        if is_correct:
            score += 1

        question_results.append({
            "question_number": i + 1,
            "question": q.get("question", ""),
            "target_skill": q.get("target_skill", req.skill_name),
            "options": q.get("options", {}),
            "user_answer": user_answer,
            "correct_answer": correct_answer,
            "is_correct": is_correct,
            "explanation": q.get("explanation", ""),
        })

    # ── Pass/Fail ────────────────────────────────────────────────────────
    threshold, threshold_reason = calc_pass_threshold(skill_data)
    passed = score >= threshold
    percentage = round((score / total) * 100) if total > 0 else 0

    # ── Full result ──────────────────────────────────────────────────────
    response["status"] = "evaluated"
    response["assessed_at"] = datetime.now().isoformat()
    response["result"] = {
        "score": score,
        "total_questions": total,
        "percentage": percentage,
        "passed": passed,
        "pass_threshold": threshold,
        "threshold_reason": threshold_reason,
    }
    response["question_results"] = question_results

    # ── Save to Supabase if authenticated ────────────────────────────────
    user_client, user = _try_auth(authorization)
    if user_client and user:
        save_data = {
            "occupation_title": occ_title,
            "occupation_code": req.occupation_code,
            "skill_name": req.skill_name,
            "skill_category": relevant[0]["category"],
            "skill_priority": relevant[0]["priority"],
            "score": score,
            "total_questions": total,
            "percentage": percentage,
            "passed": passed,
            "pass_threshold": threshold,
            "threshold_reason": threshold_reason,
            "question_results": question_results,
        }
        saved = save_assessment_result(user_client, user.id, save_data)
        response["saved_to_supabase"] = saved is not None
        if saved:
            response["supabase_record_id"] = saved.get("id")
    else:
        response["saved_to_supabase"] = False

    return response


# ── Health Check ─────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {
        "status": "ok",
        "supabase_configured": bool(SUPABASE_URL),
        "nebius_configured": bool(NEBIUS_API_KEY),
        "occupations_loaded": len(OCC_MAP),
        "skills_available": len(ALL_SKILL_NAMES),
    }
