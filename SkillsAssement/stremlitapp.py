import os
import json
import re
import csv
import io
import pandas as pd
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="O*NET Soft Skills Assessment",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

:root {
    --primary: #6C5CE7;
    --primary-dark: #5A4BD1;
    --secondary: #00CEC9;
    --accent: #FD79A8;
    --bg-dark: #0F0E17;
    --bg-card: #1A1A2E;
    --text-primary: #FFFFFE;
    --text-secondary: #FFFFFE;
    --success: #00B894;
    --danger: #FF6B6B;
    --warning: #FDCB6E;
}

.stApp {
    background: linear-gradient(135deg, var(--bg-dark) 0%, #16213E 50%, #0F3460 100%);
    font-family: 'Inter', sans-serif;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1A1A2E 0%, #16213E 100%);
    border-right: 1px solid rgba(108, 92, 231, 0.2);
}
section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3 {
    color: var(--text-primary);
}

/* Force ALL text to white — override Streamlit default grays */
/* BUT exclude selectbox/select internals so selected values stay visible */
.stApp, .stApp p, .stApp span, .stApp label,
.stApp .stMarkdown, .stApp .stMarkdown p, .stApp .stMarkdown li,
.stApp .stCaption, .stApp small,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] small,
section[data-testid="stSidebar"] .stCaption,
[data-testid="stWidgetLabel"] label,
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] div,
.stSelectbox label, .stMultiSelect label, .stRadio label,
.stTextArea label, .stTextInput label,
.stSelectbox [data-testid="stWidgetLabel"],
.stRadio [data-testid="stWidgetLabel"],
[class*="caption"], [class*="helper"] {
    color: #FFFFFE !important;
}

/* General div white rule — exclude selectbox internals */
.stApp div:not([data-baseweb="select"] *):not([data-baseweb="popover"] *):not([data-baseweb="menu"] *),
section[data-testid="stSidebar"] div:not([data-baseweb="select"] *):not([data-baseweb="popover"] *):not([data-baseweb="menu"] *) {
    color: #FFFFFE !important;
}

/* ── SELECTBOX: force selected value text to BLACK ─────────────────────── */
.stApp .stSelectbox [data-baseweb="select"] div,
.stApp .stSelectbox [data-baseweb="select"] span,
.stApp .stMultiSelect [data-baseweb="select"] div,
.stApp .stMultiSelect [data-baseweb="select"] span,
section[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] div,
section[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] span,
section[data-testid="stSidebar"] .stMultiSelect [data-baseweb="select"] div,
section[data-testid="stSidebar"] .stMultiSelect [data-baseweb="select"] span {
    color: #1a1a2e !important;
}

/* Keep placeholder text gray */
.stSelectbox input::placeholder,
.stMultiSelect input::placeholder,
.stTextArea textarea::placeholder,
.stTextInput input::placeholder,
[data-baseweb="select"] input::placeholder {
    color: #8b8fa3 !important;
}

/* Dropdown menu list items — black text on white background */
[data-baseweb="popover"] li,
[data-baseweb="popover"] li span,
[data-baseweb="popover"] li div,
[data-baseweb="menu"] li,
[data-baseweb="menu"] li span,
[data-baseweb="menu"] li div,
ul[role="listbox"] li,
ul[role="listbox"] li span,
ul[role="listbox"] li div {
    color: #000000 !important;
}

/* Radio button option labels — keep white */
.stRadio [data-baseweb="radio"] label,
.stRadio [data-baseweb="radio"] label span,
.stRadio [data-baseweb="radio"] label div {
    color: #FFFFFE !important;
}

.hero-header {
    text-align: center;
    padding: 2rem 1rem 1rem;
}
.hero-header h1 {
    font-size: 2.4rem;
    font-weight: 800;
    background: linear-gradient(135deg, #6C5CE7, #00CEC9, #FD79A8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.3rem;
}
.hero-header p {
    color: var(--text-secondary);
    font-size: 1.05rem;
    font-weight: 300;
}

.skill-card {
    background: linear-gradient(135deg, rgba(26,26,46,0.9), rgba(34,34,58,0.9));
    border: 1px solid rgba(108,92,231,0.2);
    border-radius: 16px;
    padding: 1.3rem;
    margin-bottom: 0.8rem;
    backdrop-filter: blur(10px);
    transition: transform 0.2s, box-shadow 0.2s;
}
.skill-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(108,92,231,0.15);
}
.skill-card h3 { color: #6C5CE7; font-size: 1.05rem; margin-bottom: 0.2rem; }
.skill-card .definition { color: var(--text-secondary); font-size: 0.85rem; font-style: italic; }

.result-card {
    background: linear-gradient(135deg, rgba(26,26,46,0.95), rgba(22,33,62,0.95));
    border: 1px solid rgba(0,206,201,0.3);
    border-radius: 16px;
    padding: 1.8rem;
    margin: 1rem 0;
}

.metric-box {
    background: linear-gradient(135deg, rgba(108,92,231,0.15), rgba(0,206,201,0.1));
    border: 1px solid rgba(108,92,231,0.25);
    border-radius: 14px;
    padding: 1.2rem;
    text-align: center;
}
.metric-box .value { font-size: 2rem; font-weight: 700; color: var(--primary); }
.metric-box .label { font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.2rem; }

.question-card {
    background: linear-gradient(135deg, rgba(26,26,46,0.95), rgba(34,34,58,0.95));
    border: 1px solid rgba(108,92,231,0.25);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1.2rem;
}
.question-card h4 { color: #6C5CE7; margin-bottom: 0.5rem; }

.score-badge {
    display: inline-block;
    padding: 0.25rem 0.9rem;
    border-radius: 20px;
    font-weight: 600;
    font-size: 0.85rem;
}
.score-high { background: rgba(0,184,148,0.2); color: #00B894; border: 1px solid rgba(0,184,148,0.3); }
.score-low  { background: rgba(255,107,107,0.2); color: #FF6B6B; border: 1px solid rgba(255,107,107,0.3); }

.stButton > button {
    background: linear-gradient(135deg, #6C5CE7, #5A4BD1) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.6rem 2rem !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    transition: all 0.3s !important;
    box-shadow: 0 4px 15px rgba(108,92,231,0.3) !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(108,92,231,0.4) !important;
}

.gradient-divider {
    height: 2px;
    background: linear-gradient(90deg, transparent, #6C5CE7, #00CEC9, transparent);
    border: none;
    margin: 1.5rem 0;
}

.pass-badge {
    display: inline-block; padding: 0.4rem 1.5rem; border-radius: 24px;
    font-weight: 700; font-size: 1.1rem;
}
.pass-yes { background: rgba(0,184,148,0.2); color: #00B894; border: 2px solid #00B894; }
.pass-no  { background: rgba(255,107,107,0.2); color: #FF6B6B; border: 2px solid #FF6B6B; }
</style>
""", unsafe_allow_html=True)


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
    "2.B.5.a": "Time Management",
}

SOCIAL_SKILLS = ["Coordination", "Instructing", "Negotiation", "Persuasion",
                 "Service Orientation", "Social Perceptiveness"]
THINKING_SKILLS = ["Active Learning", "Active Listening", "Complex Problem Solving",
                   "Critical Thinking", "Judgment and Decision Making",
                   "Learning Strategies", "Monitoring", "Time Management"]

TARGET_ELEMENT_IDS = list(SOFT_SKILL_IDS.keys())


# ── Load Excel ───────────────────────────────────────────────────────────────
@st.cache_data
def load_skills_data():
    """Load and filter Skills.xlsx for the 14 target soft skills."""
    df = pd.read_excel("Skills.xlsx")
    df = df[df["Element ID"].isin(TARGET_ELEMENT_IDS)]
    return df


@st.cache_data
def get_occupations(df):
    """Return sorted list of unique occupation titles with their codes."""
    occ = df[["O*NET-SOC Code", "Title"]].drop_duplicates()
    occ = occ.sort_values("Title")
    return occ


def get_skill_data(df, occ_code, selected_skills):
    """Get importance/level data for selected skills and occupation."""
    skill_ids = [k for k, v in SOFT_SKILL_IDS.items() if v in selected_skills]
    filtered = df[(df["O*NET-SOC Code"] == occ_code) & (df["Element ID"].isin(skill_ids))]

    results = []
    for skill_name in selected_skills:
        skill_rows = filtered[filtered["Element Name"] == skill_name]

        imp_row = skill_rows[skill_rows["Scale Name"] == "Importance"]
        lvl_row = skill_rows[skill_rows["Scale Name"] == "Level"]

        if imp_row.empty and lvl_row.empty:
            continue

        raw_imp = float(imp_row["Data Value"].values[0]) if not imp_row.empty else 0
        raw_lvl = float(lvl_row["Data Value"].values[0]) if not lvl_row.empty else 0

        # Check NOT RELEVANT
        not_relevant = False
        if not lvl_row.empty:
            nr_val = lvl_row["Not Relevant"].values[0]
            if isinstance(nr_val, str) and nr_val.strip().upper() == "Y":
                not_relevant = True

        # Check Recommend Suppress
        suppress = False
        for row_set in [imp_row, lvl_row]:
            if not row_set.empty:
                rs_val = row_set["Recommend Suppress"].values[0]
                if isinstance(rs_val, str) and rs_val.strip().upper() in ("Y", "YES", "1"):
                    suppress = True

        std_imp = round(((raw_imp - 1) / 4) * 100, 1) if raw_imp > 0 else 0
        std_lvl = round((raw_lvl / 7) * 100, 1) if raw_lvl > 0 else 0

        category = "Social Skills" if skill_name in SOCIAL_SKILLS else "Thinking Skills"

        results.append({
            "skill": skill_name,
            "category": category,
            "raw_imp": round(raw_imp, 2),
            "raw_lvl": round(raw_lvl, 2),
            "std_imp": std_imp,
            "std_lvl": std_lvl,
            "not_relevant": not_relevant,
            "suppress": suppress,
        })

    return results


def calc_pass_threshold(skill_data):
    """Determine pass threshold based on skill importance. Max threshold is 4/5."""
    relevant = [s for s in skill_data if not s["not_relevant"]]
    if not relevant:
        return 3, "Default threshold (no relevant skill data)"

    avg_imp = sum(s["std_imp"] for s in relevant) / len(relevant)
    if avg_imp >= 50:
        return 4, f"High threshold (4/5) — standardized importance is high ({avg_imp:.0f})"
    elif avg_imp >= 25:
        return 3, f"Standard threshold (3/5) — standardized importance is moderate ({avg_imp:.0f})"
    else:
        return 2, f"Low threshold (2/5) — standardized importance is low ({avg_imp:.0f})"


def match_occupation_from_summary(summary: str, occupation_list: list[str]) -> str:
    """Use LLM to match a user's self-description to the closest O*NET occupation."""
    client = OpenAI(
        base_url="https://api.tokenfactory.nebius.com/v1/",
        api_key=os.environ.get("NEBIUS_API_KEY"),
    )

    # Send a subset of occupations to keep the prompt manageable
    occ_text = "\n".join(f"- {o}" for o in occupation_list)

    response = client.chat.completions.create(
        model="Qwen/Qwen2.5-Coder-7B-fast",
        messages=[
            {"role": "system", "content": f"""You are an O*NET occupation classifier. Given a user's self-description, determine the SINGLE most matching occupation from the provided list.

RESPOND WITH ONLY the exact occupation title from the list, nothing else. No explanation, no quotes, just the title exactly as it appears in the list.

Available occupations:
{occ_text}"""},
            {"role": "user", "content": f"Match this person to an occupation:\n\n{summary}"},
        ],
    )

    matched = response.choices[0].message.content.strip().strip('"').strip("'")

    # Find closest match from the list
    matched_lower = matched.lower()
    for occ in occupation_list:
        if occ.lower() == matched_lower:
            return occ

    # Partial match fallback
    for occ in occupation_list:
        if matched_lower in occ.lower() or occ.lower() in matched_lower:
            return occ

    # Return the AI's best guess even if not exact
    return matched


# ── AI Question Generation ──────────────────────────────────────────────────
def generate_assessment(occupation_title: str, skill_data: list[dict]) -> list[dict]:
    """Generate 5 scenario-based MCQ questions using the Nebius API."""
    client = OpenAI(
        base_url="https://api.tokenfactory.nebius.com/v1/",
        api_key=os.environ.get("NEBIUS_API_KEY"),
    )

    # Build skill context for the prompt
    relevant_skills = [s for s in skill_data if not s["not_relevant"]]
    if not relevant_skills:
        return []

    skills_info = "\n".join([
        f"- {s['skill']} (Category: {s['category']}) — "
        f"Importance: {s['std_imp']}/100 ({'HIGH' if s['std_imp'] >= 50 else 'MEDIUM' if s['std_imp'] >= 25 else 'LOW'}), "
        f"Level: {s['std_lvl']}/100 ({'Complex scenarios' if s['std_lvl'] >= 60 else 'Intermediate scenarios' if s['std_lvl'] >= 30 else 'Basic scenarios'})"
        f"{' ⚠️ LOW CONFIDENCE RATING' if s['suppress'] else ''}"
        for s in relevant_skills
    ])

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
3. {"ALL 5 questions MUST target the single skill provided above. Do NOT invent or use any other skills." if len(relevant_skills) == 1 else "Cover at least 2 different skills from the list above. Do NOT invent skills outside the provided list."}
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

            # ── Strip markdown fences (```json ... ``` or ``` ... ```) ──
            raw = re.sub(r'^```(?:json|JSON)?\s*\n?', '', raw)
            raw = re.sub(r'\n?```\s*$', '', raw)
            raw = raw.strip()

            # ── Sanitize invalid control characters inside JSON string values ──
            def _sanitize_json(s):
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

            raw = _sanitize_json(raw)

            # ── Try to parse JSON, with multiple fallback strategies ──
            result = None

            # Strategy 1: direct parse
            try:
                result = json.loads(raw)
            except json.JSONDecodeError:
                pass

            # Strategy 2: extract the outermost [...] and parse that
            if result is None:
                arr_match = re.search(r'\[.*\]', raw, re.DOTALL)
                if arr_match:
                    try:
                        result = json.loads(arr_match.group(0))
                    except json.JSONDecodeError:
                        pass

            # Strategy 3: raw_decode – grab the first valid JSON value
            if result is None:
                try:
                    decoder = json.JSONDecoder()
                    result, _ = decoder.raw_decode(raw)
                except json.JSONDecodeError:
                    raise ValueError("Could not parse AI response as JSON.")

            # ── Normalise result into a list of question dicts ──
            if isinstance(result, dict):
                for key in ("questions", "data", "assessment", "quiz", "items"):
                    if key in result and isinstance(result[key], list):
                        result = result[key]
                        break
                if isinstance(result, dict):
                    result = [result]

            if not isinstance(result, list):
                raise ValueError("AI response was not a JSON array.")

            # ── Validate each question object ──
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
    raise ValueError(
        f"Failed after {MAX_RETRIES} attempts. Last error: {last_error}"
    )


# ── CSV export ───────────────────────────────────────────────────────────────
def generate_csv(skill_data, score, total, passed, threshold_reason, occupation):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["O*NET Soft Skills Assessment Results"])
    writer.writerow(["Occupation", occupation])
    writer.writerow(["Score", f"{score}/{total}"])
    writer.writerow(["Result", "PASS" if passed else "FAIL"])
    writer.writerow(["Threshold Logic", threshold_reason])
    writer.writerow([])
    writer.writerow(["Skill", "Category", "Raw Importance", "Raw Level",
                      "Std Importance", "Std Level", "Not Relevant", "Suppress"])
    for s in skill_data:
        writer.writerow([
            s["skill"], s["category"], s["raw_imp"], s["raw_lvl"],
            s["std_imp"], s["std_lvl"],
            "Yes" if s["not_relevant"] else "No",
            "Yes" if s["suppress"] else "No",
        ])
    return output.getvalue()


# ── Session State ────────────────────────────────────────────────────────────
if "stage" not in st.session_state:
    st.session_state.stage = "input"
if "skill_data" not in st.session_state:
    st.session_state.skill_data = []
if "questions" not in st.session_state:
    st.session_state.questions = []
if "occ_code" not in st.session_state:
    st.session_state.occ_code = ""
if "occ_title" not in st.session_state:
    st.session_state.occ_title = ""
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}


# ── Load Data ────────────────────────────────────────────────────────────────
df = load_skills_data()
occupations = get_occupations(df)
occ_titles = occupations["Title"].tolist()
occ_map = dict(zip(occupations["Title"], occupations["O*NET-SOC Code"]))

# Get available skills per occupation (will update dynamically)
all_skill_names = list(SOFT_SKILL_IDS.values())


# ── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎯 Assessment Setup")
    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

    # Step 1: Choose how to identify occupation
    input_mode = st.radio(
        "🏢 How would you like to identify your occupation?",
        options=["Select from list", "Write a summary about myself"],
        index=0,
        help="Choose to pick an occupation directly or describe yourself and let AI match you.",
    )

    selected_occ = None
    occ_code = None

    if input_mode == "Select from list":
        selected_occ = st.selectbox(
            "🔍 Search Occupation",
            options=[""] + occ_titles,
            index=0,
            help="Search and select your target O*NET occupation",
            placeholder="Type to search occupations...",
        )
        if selected_occ:
            occ_code = occ_map[selected_occ]
            st.caption(f"📋 Code: `{occ_code}`")

    else:  # Write a summary
        user_summary = st.text_area(
            "📝 Describe yourself",
            placeholder="e.g. I work in data analysis, building dashboards and reports. I manage a small team and often present insights to executives...",
            height=120,
            help="Describe your role, daily tasks, and responsibilities. The AI will match you to the closest O*NET occupation.",
        )

        if user_summary and len(user_summary.strip()) > 10:
            if st.button("🤖 Find My Occupation", use_container_width=True):
                with st.spinner("🔍 AI is matching your profile to O*NET occupations..."):
                    try:
                        matched_title = match_occupation_from_summary(user_summary, occ_titles)
                        st.session_state._matched_occ = matched_title
                    except Exception as e:
                        st.error(f"❌ Matching failed: {e}")

        # Show matched result
        if hasattr(st.session_state, "_matched_occ") and st.session_state._matched_occ:
            matched = st.session_state._matched_occ
            st.success(f"✅ Best match: **{matched}**")
            if matched in occ_map:
                selected_occ = matched
                occ_code = occ_map[matched]
                st.caption(f"📋 Code: `{occ_code}`")
            else:
                st.warning(f"⚠️ '{matched}' not found in the list. Please select manually.")
                selected_occ = st.selectbox(
                    "🔍 Select the correct occupation",
                    options=[""] + occ_titles,
                    index=0,
                    placeholder="Type to search...",
                    key="fallback_occ",
                )
                if selected_occ:
                    occ_code = occ_map[selected_occ]

    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

    # Step 2: Select ONE skill
    st.markdown("### 🎯 Select Skill to Assess")

    selected_skill = st.selectbox(
        "Choose one of the 14 O*NET Soft Skills",
        options=[""] + all_skill_names,
        index=0,
        help="Select a single skill to assess. The app will generate 5 questions for this skill.",
        placeholder="Pick a skill...",
    )

    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

    if st.button("🔄 Reset", use_container_width=True):
        st.session_state.stage = "input"
        st.session_state.skill_data = []
        st.session_state.questions = []
        st.session_state.user_answers = {}
        if hasattr(st.session_state, "_matched_occ"):
            del st.session_state._matched_occ
        st.rerun()

    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

    if selected_occ and selected_skill:
        if st.button("🚀 Generate Assessment", use_container_width=True):
            st.session_state.occ_code = occ_code
            st.session_state.occ_title = selected_occ
            st.session_state.stage = "loading"
            st.session_state._selected_skills = [selected_skill]
            st.rerun()
    elif not selected_occ:
        st.info("⬆️ Select or match an occupation to begin.")
    elif not selected_skill:
        st.info("⬆️ Select a skill to assess.")

    st.markdown("---")
    st.markdown(
        "<p style='color:#FFFFFE;font-size:0.78rem;text-align:center;'>"
        "Powered by O*NET Standards<br>Data from Skills.xlsx · AI via Nebius</p>",
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN CONTENT
# ══════════════════════════════════════════════════════════════════════════════

# ── INPUT STAGE ──────────────────────────────────────────────────────────────
if st.session_state.stage == "input":
    st.markdown("""
    <div class="hero-header">
        <h1>🎯 O*NET Soft Skills Assessment</h1>
        <p>Data-driven assessment powered by official O*NET occupation data</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

    st.markdown("### How It Works")
    cols = st.columns(4)
    steps = [
        ("1️⃣", "Choose Occupation", "Select from list or describe yourself for AI matching"),
        ("2️⃣", "Pick a Skill", "Select one of the 14 soft skills to assess"),
        ("3️⃣", "Take the Quiz", "Answer 5 scenario-based questions tailored to your role"),
        ("4️⃣", "Get Results", "See your score, pass/fail, skill breakdown & export CSV"),
    ]
    for col, (icon, title, desc) in zip(cols, steps):
        with col:
            st.markdown(f"""
            <div class="skill-card" style="text-align:center;">
                <div style="font-size:2rem;">{icon}</div>
                <h3>{title}</h3>
                <div class="definition">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

    # Show the 14 skills
    st.markdown("### 📚 The 14 O*NET Soft Skills")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 🤝 Social Skills")
        for s in SOCIAL_SKILLS:
            st.markdown(f"- **{s}**")
    with c2:
        st.markdown("#### 🧠 Thinking Skills")
        for s in THINKING_SKILLS:
            st.markdown(f"- **{s}**")

    st.markdown("""
    <div style="text-align:center; color:#FFFFFE; padding:2rem 1rem;">
        <p>👈 Use the sidebar to select an occupation and skills, then click <b>Generate Assessment</b></p>
    </div>
    """, unsafe_allow_html=True)


# ── LOADING STAGE ────────────────────────────────────────────────────────────
elif st.session_state.stage == "loading":
    occ_code = st.session_state.occ_code
    occ_title = st.session_state.occ_title
    selected_skills = st.session_state._selected_skills

    st.markdown(f"""
    <div class="hero-header">
        <h1>⏳ Generating Assessment</h1>
        <p>Occupation: <b>{occ_title}</b> ({occ_code})</p>
    </div>
    """, unsafe_allow_html=True)

    # Step 1: Read skill data from Excel
    with st.spinner("📊 Reading O*NET data from Skills.xlsx..."):
        skill_data = get_skill_data(df, occ_code, selected_skills)

    # Filter out NOT RELEVANT skills
    relevant = [s for s in skill_data if not s["not_relevant"]]
    not_relevant = [s for s in skill_data if s["not_relevant"]]

    if not_relevant:
        st.warning(f"⚠️ Skipping {len(not_relevant)} skill(s) marked as NOT RELEVANT: "
                   + ", ".join(s["skill"] for s in not_relevant))

    if not relevant:
        st.error("❌ No relevant skills found for this occupation. Please choose different skills or occupation.")
        st.session_state.stage = "input"
        st.stop()

    # Show skill data summary
    st.markdown("### 📋 Skill Data from O*NET")
    header = "| Skill | Category | Raw Imp | Raw Lvl | Std Imp | Std Lvl | Priority | Difficulty |"
    sep = "|-------|----------|---------|---------|---------|---------|----------|------------|"
    rows = [header, sep]
    for s in relevant:
        priority = "🔴 HIGH" if s["std_imp"] >= 50 else ("🟡 MED" if s["std_imp"] >= 25 else "🟢 LOW")
        difficulty = "Complex" if s["std_lvl"] >= 60 else ("Intermediate" if s["std_lvl"] >= 30 else "Basic")
        suppress_flag = " ⚠️" if s["suppress"] else ""
        rows.append(f"| {s['skill']}{suppress_flag} | {s['category']} | {s['raw_imp']} | {s['raw_lvl']} | "
                    f"{s['std_imp']} | {s['std_lvl']} | {priority} | {difficulty} |")
    st.markdown("\n".join(rows))

    # Step 2: Generate questions via AI
    with st.spinner("🤖 AI is generating scenario-based questions..."):
        try:
            questions = generate_assessment(occ_title, relevant)
        except Exception as e:
            st.error(f"❌ Failed to generate questions: {e}")
            st.session_state.stage = "input"
            st.stop()

    st.session_state.skill_data = skill_data
    st.session_state.questions = questions
    st.session_state.user_answers = {}
    st.session_state.stage = "quiz"
    st.rerun()


# ── QUIZ STAGE ───────────────────────────────────────────────────────────────
elif st.session_state.stage == "quiz":
    occ_title = st.session_state.occ_title
    occ_code = st.session_state.occ_code
    questions = st.session_state.questions
    skill_data = st.session_state.skill_data

    st.markdown(f"""
    <div class="hero-header">
        <h1>📝 Assessment Quiz</h1>
        <p>{occ_title} ({occ_code}) · {len(questions)} Questions</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

    with st.form("quiz_form"):
        answers = {}
        for i, q in enumerate(questions):
            target = q.get("target_skill", "Unknown")

            st.markdown(f"""
            <div class="question-card">
                <h4>Question {i + 1} of {len(questions)}</h4>
                <div style="color:#FFFFFE; font-size:0.8rem; margin-bottom:0.5rem;">
                    🎯 Skill: {target}
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"**{q['question']}**")

            options_list = [f"{k}. {v}" for k, v in q["options"].items()]
            choice = st.radio(
                f"Your answer for Q{i + 1}",
                options=options_list,
                index=None,
                key=f"q_{i}",
                label_visibility="collapsed",
            )
            answers[i] = choice

            st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

        submitted = st.form_submit_button("📊 Submit & See Results", use_container_width=True)

    if submitted:
        # Check all answered
        unanswered = [i + 1 for i, a in answers.items() if a is None]
        if unanswered:
            st.error(f"⚠️ Please answer all questions. Missing: Q{', Q'.join(map(str, unanswered))}")
            st.stop()

        # Extract letter answers
        user_answers = {}
        for i, choice in answers.items():
            letter = choice.split(".")[0].strip() if choice else ""
            user_answers[i] = letter

        st.session_state.user_answers = user_answers
        st.session_state.stage = "results"
        st.rerun()


# ── RESULTS STAGE ────────────────────────────────────────────────────────────
elif st.session_state.stage == "results":
    occ_title = st.session_state.occ_title
    occ_code = st.session_state.occ_code
    questions = st.session_state.questions
    skill_data = st.session_state.skill_data
    user_answers = st.session_state.user_answers

    # Calculate score
    score = 0
    for i, q in enumerate(questions):
        if user_answers.get(i) == q["correct"]:
            score += 1
    total = len(questions)

    # Pass/Fail
    pass_threshold, threshold_reason = calc_pass_threshold(skill_data)
    passed = score >= pass_threshold

    st.markdown(f"""
    <div class="hero-header">
        <h1>📊 Assessment Results</h1>
        <p>{occ_title} ({occ_code})</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

    # Summary metrics
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(f"""
        <div class="metric-box">
            <div class="value">{score}/{total}</div>
            <div class="label">Score</div>
        </div>""", unsafe_allow_html=True)
    with m2:
        pct = round((score / total) * 100) if total > 0 else 0
        st.markdown(f"""
        <div class="metric-box">
            <div class="value">{pct}%</div>
            <div class="label">Accuracy</div>
        </div>""", unsafe_allow_html=True)
    with m3:
        badge_cls = "pass-yes" if passed else "pass-no"
        badge_text = "✅ PASS" if passed else "❌ FAIL"
        st.markdown(f"""
        <div class="metric-box">
            <div class="pass-badge {badge_cls}">{badge_text}</div>
            <div class="label" style="margin-top:0.5rem;">Threshold: {pass_threshold}/{total}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

    # ── Section 1: Skill Data Summary ────────────────────────────────────────
    st.markdown("### 📋 1. Occupation & Skills Summary")
    st.markdown(f"""
    <div class="result-card">
        <p><b>Occupation:</b> {occ_title} (<code>{occ_code}</code>)</p>
    </div>
    """, unsafe_allow_html=True)

    relevant = [s for s in skill_data if not s["not_relevant"]]
    header = "| Skill | Category | Raw Imp | Raw Lvl | Std Imp | Std Lvl |"
    sep = "|-------|----------|---------|---------|---------|---------|"
    rows = [header, sep]
    for s in relevant:
        flag = " ⚠️" if s["suppress"] else ""
        rows.append(f"| {s['skill']}{flag} | {s['category']} | {s['raw_imp']} | {s['raw_lvl']} | "
                    f"{s['std_imp']} | {s['std_lvl']} |")
    st.markdown("\n".join(rows))

    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

    # ── Section 2: Answer Key ────────────────────────────────────────────────
    st.markdown("### 📝 2. Answer Key & Explanations")

    for i, q in enumerate(questions):
        user_ans = user_answers.get(i, "?")
        correct_ans = q["correct"]
        is_correct = user_ans == correct_ans
        target_skill = q.get("target_skill", "Unknown")

        icon = "✅" if is_correct else "❌"
        badge_cls = "score-high" if is_correct else "score-low"

        st.markdown(f"""
        <div class="question-card">
            <h4>{icon} Q{i + 1}: {q['question'][:80]}...</h4>
            <div style="display:flex; gap:1.5rem; flex-wrap:wrap; margin:0.5rem 0;">
                <div><span style="color:#FFFFFE;">Your Answer:</span> <b>{user_ans}</b></div>
                <div><span style="color:#FFFFFE;">Correct:</span> <span class="score-badge {badge_cls}">{correct_ans}</span></div>
                <div><span style="color:#FFFFFE;">Skill:</span> {target_skill}</div>
            </div>
            <div style="color:#FFFFFE; font-size:0.9rem; margin-top:0.5rem;">
                💡 {q.get('explanation', 'N/A')}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

    # ── Section 3: Scoring Logic ─────────────────────────────────────────────
    st.markdown("### ⚖️ 3. Scoring Logic")
    st.markdown(f"""
    <div class="result-card">
        <p><b>Pass Threshold:</b> {pass_threshold}/{total}</p>
        <p><b>Reasoning:</b> {threshold_reason}</p>
        <p><b>Your Score:</b> {score}/{total} → <span class="pass-badge {'pass-yes' if passed else 'pass-no'}">{'PASS' if passed else 'FAIL'}</span></p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

    # ── Export & Restart ─────────────────────────────────────────────────────
    st.markdown("### 💾 Export & Actions")
    csv_data = generate_csv(skill_data, score, total, passed, threshold_reason, f"{occ_title} ({occ_code})")

    col_dl, col_new = st.columns(2)
    with col_dl:
        st.download_button(
            label="📥 Download CSV Report",
            data=csv_data,
            file_name=f"onet_assessment_{occ_code}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with col_new:
        if st.button("🔄 New Assessment", use_container_width=True):
            st.session_state.stage = "input"
            st.session_state.skill_data = []
            st.session_state.questions = []
            st.session_state.user_answers = {}
            st.rerun()
