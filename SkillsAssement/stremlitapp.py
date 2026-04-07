import streamlit as st
import time

st.set_page_config(
    page_title="Jadeer",
    page_icon="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><text y='28' font-size='28'>J</text></svg>",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Global CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    -webkit-font-smoothing: antialiased;
}

.stApp { background: #f7f8fa; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #fff;
    border-right: 1px solid #e8eaed;
    min-width: 220px !important;
    max-width: 220px !important;
}
[data-testid="stSidebar"] > div { padding-top: 0 !important; }

/* Hide default radio bullets */
[data-testid="stSidebar"] .stRadio [role="radiogroup"] { gap: 2px; }
[data-testid="stSidebar"] .stRadio label {
    display: flex !important;
    align-items: center;
    gap: 10px;
    padding: 9px 16px;
    border-radius: 6px;
    font-size: 13.5px;
    font-weight: 500;
    color: #4a5568;
    cursor: pointer;
    transition: background 0.15s, color 0.15s;
    width: 100%;
}
[data-testid="stSidebar"] .stRadio label:hover { background: #f0f4ff; color: #2d3748; }
[data-testid="stSidebar"] .stRadio [aria-checked="true"] + label,
[data-testid="stSidebar"] .stRadio label[data-checked="true"] { background: #eef2ff; color: #3b5bdb; font-weight: 600; }
[data-testid="stSidebar"] .stRadio [data-baseweb="radio"] > div:first-child { display: none !important; }

/* ── Main content area ── */
.main .block-container {
    padding: 28px 32px 40px 32px !important;
    max-width: 1100px;
}

/* ── Cards ── */
.jd-card {
    background: #fff;
    border: 1px solid #e8eaed;
    border-radius: 10px;
    padding: 22px 24px;
    margin-bottom: 16px;
}
.jd-card-flat {
    background: #fff;
    border: 1px solid #e8eaed;
    border-radius: 10px;
    overflow: hidden;
    margin-bottom: 16px;
}

/* ── Typography ── */
.jd-page-title {
    font-size: 22px;
    font-weight: 700;
    color: #1a1d23;
    letter-spacing: -0.3px;
    margin-bottom: 2px;
}
.jd-page-sub {
    font-size: 13px;
    color: #8a93a2;
    margin-bottom: 22px;
}
.jd-section-title {
    font-size: 14px;
    font-weight: 700;
    color: #1a1d23;
    letter-spacing: -0.1px;
    margin-bottom: 14px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-size: 11px;
    color: #8a93a2;
}
.jd-label {
    font-size: 12px;
    font-weight: 600;
    color: #8a93a2;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    margin-bottom: 4px;
}
.jd-value {
    font-size: 14px;
    color: #1a1d23;
    font-weight: 500;
}

/* ── Metric tiles ── */
.jd-metrics {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-bottom: 20px;
}
.jd-metric {
    background: #fff;
    border: 1px solid #e8eaed;
    border-radius: 10px;
    padding: 18px 20px;
    text-align: center;
}
.jd-metric-num {
    font-size: 28px;
    font-weight: 700;
    color: #3b5bdb;
    letter-spacing: -1px;
    line-height: 1;
}
.jd-metric-label {
    font-size: 12px;
    color: #8a93a2;
    margin-top: 5px;
    font-weight: 500;
}

/* ── Badges ── */
.jd-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.2px;
}
.jd-badge-blue   { background: #eef2ff; color: #3b5bdb; }
.jd-badge-green  { background: #ebfbee; color: #2f9e44; }
.jd-badge-amber  { background: #fff9db; color: #e67700; }
.jd-badge-red    { background: #fff5f5; color: #e03131; }
.jd-badge-gray   { background: #f3f4f6; color: #6b7280; }

/* ── Priority dots ── */
.dot-high   { color: #3b5bdb; }
.dot-medium { color: #e67700; }
.dot-low    { color: #adb5bd; }

/* ── Progress bar ── */
.jd-bar-wrap { margin-bottom: 11px; }
.jd-bar-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 5px;
    font-size: 13px;
    color: #374151;
    font-weight: 500;
}
.jd-bar-track {
    height: 6px;
    background: #f3f4f6;
    border-radius: 3px;
    overflow: hidden;
}
.jd-bar-fill {
    height: 6px;
    border-radius: 3px;
    background: #3b5bdb;
}

/* ── Divider ── */
.jd-divider { border: none; border-top: 1px solid #f0f1f3; margin: 16px 0; }

/* ── Timeline entries ── */
.jd-entry { display: flex; gap: 14px; margin-bottom: 20px; }
.jd-entry-icon {
    width: 38px; height: 38px; border-radius: 8px;
    background: #f0f4ff;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px; flex-shrink: 0; color: #3b5bdb;
    font-weight: 700; font-size: 13px;
}
.jd-entry-title { font-size: 14px; font-weight: 600; color: #1a1d23; }
.jd-entry-sub   { font-size: 13px; color: #6b7280; margin-top: 1px; }
.jd-entry-date  { font-size: 12px; color: #adb5bd; margin-top: 2px; }
.jd-entry-desc  { font-size: 13px; color: #4b5563; margin-top: 6px; line-height: 1.55; }

/* ── Profile header ── */
.jd-profile-banner {
    height: 80px;
    background: linear-gradient(120deg, #3b5bdb 0%, #1971c2 100%);
}
.jd-profile-body { padding: 0 24px 22px 24px; }
.jd-avatar {
    width: 68px; height: 68px; border-radius: 50%;
    background: #fff; border: 3px solid #fff;
    box-shadow: 0 2px 10px rgba(0,0,0,0.12);
    display: flex; align-items: center; justify-content: center;
    margin-top: -34px;
    font-size: 26px; font-weight: 700; color: #3b5bdb;
    font-family: 'Inter', sans-serif;
}
.jd-profile-name { font-size: 20px; font-weight: 700; color: #1a1d23; margin-top: 10px; }
.jd-profile-headline { font-size: 14px; color: #4b5563; margin-top: 3px; }
.jd-profile-meta { font-size: 12px; color: #9ca3af; margin-top: 5px; }

/* ── Buttons ── */
.jd-btn {
    display: inline-block;
    padding: 8px 18px;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s;
    border: none;
    text-align: center;
}
.jd-btn-primary { background: #3b5bdb; color: #fff; }
.jd-btn-primary:hover { background: #364fc7; }
.jd-btn-outline { background: #fff; color: #3b5bdb; border: 1.5px solid #3b5bdb; }
.jd-btn-outline:hover { background: #eef2ff; }

/* ── Skill chip ── */
.jd-chip {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 4px;
    background: #f3f4f6;
    color: #374151;
    font-size: 12px;
    font-weight: 500;
    margin: 3px 3px 3px 0;
}

/* ── Question card ── */
.q-card {
    background: #fff;
    border: 1px solid #e8eaed;
    border-radius: 10px;
    padding: 20px 22px;
    margin-bottom: 14px;
}
.q-num { font-size: 11px; font-weight: 600; color: #8a93a2; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }
.q-text { font-size: 15px; font-weight: 600; color: #1a1d23; line-height: 1.5; margin-bottom: 16px; }

/* ── Cert row ── */
.cert-row {
    display: flex; align-items: center; gap: 14px;
    padding: 14px 0; border-bottom: 1px solid #f3f4f6;
}
.cert-row:last-child { border-bottom: none; }
.cert-logo {
    width: 40px; height: 40px; border-radius: 8px;
    background: #f0f4ff; display: flex; align-items: center;
    justify-content: center; font-size: 14px; font-weight: 700;
    color: #3b5bdb; flex-shrink: 0;
}
.cert-name  { font-size: 14px; font-weight: 600; color: #1a1d23; }
.cert-meta  { font-size: 12px; color: #9ca3af; margin-top: 2px; }

/* ── Job card ── */
.job-card {
    background: #fff; border: 1px solid #e8eaed;
    border-radius: 10px; padding: 18px 20px;
    margin-bottom: 12px;
    display: flex; justify-content: space-between; align-items: flex-start;
}
.job-title   { font-size: 15px; font-weight: 700; color: #1a1d23; }
.job-company { font-size: 13px; color: #3b5bdb; margin-top: 2px; font-weight: 500; }
.job-meta    { font-size: 12px; color: #9ca3af; margin-top: 4px; }
.job-match-num { font-size: 26px; font-weight: 800; letter-spacing: -1px; }
.job-match-label { font-size: 11px; color: #9ca3af; text-align: right; }

/* ── Result banner ── */
.result-banner {
    border-radius: 10px; padding: 28px;
    text-align: center; margin-bottom: 16px;
}
.result-score { font-size: 52px; font-weight: 800; letter-spacing: -2px; line-height: 1; }
.result-sub   { font-size: 14px; margin-top: 6px; }
.result-label { font-size: 13px; margin-top: 4px; opacity: 0.7; }

/* Streamlit overrides */
div[data-testid="stVerticalBlock"] > div { padding-top: 0 !important; }
.stButton > button {
    border-radius: 6px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    font-family: 'Inter', sans-serif !important;
    transition: all 0.15s !important;
}
.stButton > button[kind="primary"] {
    background: #3b5bdb !important;
    border-color: #3b5bdb !important;
}
.stButton > button[kind="primary"]:hover {
    background: #364fc7 !important;
}
.stSelectbox label, .stTextInput label, .stCheckbox label,
.stSlider label, .stRadio label {
    font-size: 13px !important;
    font-weight: 500 !important;
    color: #374151 !important;
}
[data-testid="stSidebar"] .stRadio label,
[data-testid="stSidebar"] .stRadio label span {
    color: #4a5568 !important;
}
.stExpander { border: 1px solid #e8eaed !important; border-radius: 8px !important; }
div[data-testid="stTabs"] button {
    font-size: 13px !important; font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
}

/* Sidebar logo area */
.jd-sidebar-logo {
    padding: 20px 16px 12px 16px;
    border-bottom: 1px solid #f0f1f3;
    margin-bottom: 10px;
}
.jd-sidebar-logo-name {
    font-size: 20px; font-weight: 800; color: #1a1d23; letter-spacing: -0.5px;
}
.jd-sidebar-logo-sub {
    font-size: 11px; color: #9ca3af; margin-top: 1px; font-weight: 500;
}
.jd-sidebar-footer {
    position: absolute; bottom: 24px; left: 16px;
    font-size: 11px; color: #c1c7d0; line-height: 1.6;
}

/* ── Responsive ── */
@media (max-width: 900px) {
    .main .block-container {
        padding: 16px 16px 32px 16px !important;
    }
    .jd-metrics {
        grid-template-columns: repeat(2, 1fr) !important;
    }
    .jd-page-title { font-size: 18px !important; }
    .jd-metric-num { font-size: 22px !important; }
}

@media (max-width: 600px) {
    .main .block-container {
        padding: 10px 10px 24px 10px !important;
    }
    .jd-metrics {
        grid-template-columns: repeat(2, 1fr) !important;
        gap: 8px !important;
    }
    .jd-metric { padding: 12px 10px !important; }
    .jd-metric-num { font-size: 20px !important; }
    .jd-metric-label { font-size: 11px !important; }

    .jd-page-title { font-size: 17px !important; }
    .jd-card { padding: 14px 14px !important; }

    /* Stack profile banner on mobile */
    .jd-profile-body { padding: 0 14px 16px 14px !important; }
    .jd-avatar { width: 52px !important; height: 52px !important; font-size: 18px !important; margin-top: -26px !important; }
    .jd-profile-name { font-size: 16px !important; }

    /* Job cards — stack match % below */
    .job-card { flex-direction: column !important; gap: 10px !important; }
    .job-match-num { font-size: 20px !important; }

    /* Entry icons smaller */
    .jd-entry-icon { width: 32px !important; height: 32px !important; font-size: 9px !important; }
    .jd-entry-title { font-size: 13px !important; }
    .jd-entry-desc { font-size: 12px !important; }

    /* Result banner */
    .result-score { font-size: 38px !important; }

    /* Sidebar fixed narrow on mobile */
    [data-testid="stSidebar"] {
        min-width: 180px !important;
        max-width: 180px !important;
    }
    [data-testid="stSidebar"] .stRadio label {
        font-size: 12px !important;
        padding: 7px 10px !important;
    }
}

@media (max-width: 400px) {
    .jd-metrics {
        grid-template-columns: repeat(2, 1fr) !important;
    }
    .jd-metric-num { font-size: 18px !important; }
    .jd-section-title { font-size: 10px !important; }
}
</style>
""", unsafe_allow_html=True)

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="jd-sidebar-logo">
        <div class="jd-sidebar-logo-name">Jadeer</div>
        <div class="jd-sidebar-logo-sub">Career Intelligence Platform</div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "nav",
        ["Home", "Profile", "CV Builder", "Skills Assessment", "Certificates", "Recommendations"],
        label_visibility="hidden",
    )

    st.markdown("""
    <div class="jd-sidebar-footer">
        Powered by O*NET &amp; Nebius AI<br>
        v1.0.0 &nbsp;·&nbsp; Demo Mode
    </div>
    """, unsafe_allow_html=True)


# ─── Demo data ────────────────────────────────────────────────────────────────
SKILLS_DATA = [
    {"skill": "Critical Thinking",           "category": "Thinking", "priority": "HIGH",   "importance": 82, "level": 75},
    {"skill": "Active Learning",              "category": "Thinking", "priority": "HIGH",   "importance": 76, "level": 68},
    {"skill": "Complex Problem Solving",      "category": "Thinking", "priority": "HIGH",   "importance": 73, "level": 70},
    {"skill": "Judgment & Decision Making",   "category": "Thinking", "priority": "MEDIUM", "importance": 65, "level": 60},
    {"skill": "Monitoring",                   "category": "Thinking", "priority": "MEDIUM", "importance": 60, "level": 55},
    {"skill": "Time Management",              "category": "Thinking", "priority": "MEDIUM", "importance": 58, "level": 50},
    {"skill": "Learning Strategies",          "category": "Thinking", "priority": "MEDIUM", "importance": 54, "level": 48},
    {"skill": "Active Listening",             "category": "Thinking", "priority": "MEDIUM", "importance": 52, "level": 45},
    {"skill": "Coordination",                 "category": "Social",   "priority": "MEDIUM", "importance": 50, "level": 46},
    {"skill": "Social Perceptiveness",        "category": "Social",   "priority": "LOW",    "importance": 38, "level": 35},
    {"skill": "Persuasion",                   "category": "Social",   "priority": "LOW",    "importance": 32, "level": 30},
    {"skill": "Negotiation",                  "category": "Social",   "priority": "LOW",    "importance": 28, "level": 25},
    {"skill": "Instructing",                  "category": "Social",   "priority": "LOW",    "importance": 24, "level": 22},
    {"skill": "Service Orientation",          "category": "Social",   "priority": "LOW",    "importance": 20, "level": 18},
]
CERTS = [
    {"abbr": "AWS", "name": "AWS Certified Developer",  "issuer": "Amazon Web Services", "status": "Verified",  "date": "Jan 2024"},
    {"abbr": "PY",  "name": "Python Professional",      "issuer": "Coursera",            "status": "Verified",  "date": "Mar 2023"},
    {"abbr": "DK",  "name": "Docker Fundamentals",      "issuer": "edX",                 "status": "Pending",   "date": "Nov 2023"},
    {"abbr": "CEH", "name": "Certified Ethical Hacker", "issuer": "EC-Council",          "status": "Verified",  "date": "Jul 2023"},
]
JOBS = [
    {"title": "Senior Software Engineer",   "company": "Google",  "location": "Remote",  "match": 91, "skills": ["Python", "System Design", "ML"]},
    {"title": "AI/ML Engineer",             "company": "STC",     "location": "Riyadh",  "match": 87, "skills": ["ML", "FastAPI", "Docker"]},
    {"title": "Backend Developer",          "company": "Noon",    "location": "Riyadh",  "match": 84, "skills": ["Python", "APIs", "Cloud"]},
    {"title": "Full-Stack Developer",       "company": "Careem",  "location": "Riyadh",  "match": 79, "skills": ["Python", "React", "Supabase"]},
]
EXPERIENCES = [
    {"title": "Software Engineer",  "company": "Tech Startup, Riyadh",  "period": "2023 – Present",
     "desc": "Built microservices with FastAPI and Docker. Led AI integration using Nebius LLM and Supabase."},
    {"title": "Junior Developer",   "company": "Digital Agency",         "period": "2022 – 2023",
     "desc": "Developed REST APIs and maintained PostgreSQL databases. Collaborated in agile sprints."},
]
QUESTIONS = [
    {"q": "You notice a critical security vulnerability during a deployment not in your task list. Your team is under deadline pressure. What do you do?",
     "skill": "Judgment & Decision Making",
     "opts": {"A": "Ignore it and stay on schedule.", "B": "Document it, notify your lead, and assess risk before proceeding.", "C": "Fix it silently to save time.", "D": "Deploy and fix it in the next sprint."}, "ans": "B",
     "exp": "Sound judgment means surfacing risk and making informed decisions with your team, not ignoring or unilaterally resolving it."},
    {"q": "A new framework your team adopted has unexpected performance issues. You have 2 days to present a solution.",
     "skill": "Complex Problem Solving",
     "opts": {"A": "Revert to the old framework.", "B": "Profile the app, identify bottlenecks, test fixes, and present findings.", "C": "Delegate it to another team.", "D": "Present the problem without solutions."}, "ans": "B",
     "exp": "Systematic investigation, evidence-based fixes, and clear communication is the hallmark of effective problem solving."},
    {"q": "During a code review, a colleague proposes a design pattern you are unfamiliar with. What is your best response?",
     "skill": "Active Learning",
     "opts": {"A": "Reject it — stick with what you know.", "B": "Approve it without understanding.", "C": "Ask the colleague to explain it, research independently, then evaluate its fit.", "D": "Escalate to a manager."}, "ans": "C",
     "exp": "Active learners seek understanding before accepting or rejecting — combining peer knowledge with independent research."},
    {"q": "Your project estimate was 2 weeks but work is taking 3. What should you do?",
     "skill": "Time Management",
     "opts": {"A": "Work overtime without telling anyone.", "B": "Inform stakeholders early, reassess scope, reprioritize, and provide a revised timeline.", "C": "Submit partial work as complete.", "D": "Blame external dependencies."}, "ans": "B",
     "exp": "Effective time management includes proactive communication and realistic re-estimation, not silence or deflection."},
    {"q": "A client reports a production bug affecting 10% of users. Your first action is to:",
     "skill": "Critical Thinking",
     "opts": {"A": "Try fixes randomly until something works.", "B": "Collect logs, reproduce the issue, form a hypothesis, test, and apply a targeted fix.", "C": "Roll back all recent changes.", "D": "Tell the client it is their network issue."}, "ans": "B",
     "exp": "Critical thinking means using evidence to systematically diagnose problems rather than guessing."},
]

# ─── Session state ─────────────────────────────────────────────────────────────
for k, v in {"started": False, "answers": {}, "submitted": False, "matched": False,
             "cv_done": False, "sel_skill": "Critical Thinking"}.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ─── Helpers ──────────────────────────────────────────────────────────────────
def bar(name, val, color="#3b5bdb"):
    st.markdown(f"""
    <div class="jd-bar-wrap">
      <div class="jd-bar-header"><span>{name}</span><span style="color:#9ca3af;font-size:12px;">{val}%</span></div>
      <div class="jd-bar-track"><div class="jd-bar-fill" style="width:{val}%;background:{color};"></div></div>
    </div>""", unsafe_allow_html=True)

def badge(text, kind="blue"):
    return f'<span class="jd-badge jd-badge-{kind}">{text}</span>'

def priority_color(p):
    return "#3b5bdb" if p == "HIGH" else "#e67700" if p == "MEDIUM" else "#adb5bd"


# ══════════════════════════════════════════════════════════════════
# HOME
# ══════════════════════════════════════════════════════════════════
if page == "Home":
    # Hero banner
    st.markdown("""
    <div style="background:linear-gradient(120deg,#3b5bdb,#1971c2);border-radius:12px;
                padding:32px 36px;margin-bottom:20px;color:#fff;">
        <div style="font-size:11px;font-weight:600;letter-spacing:1px;opacity:0.7;
                    text-transform:uppercase;margin-bottom:8px;">Good evening</div>
        <div style="font-size:28px;font-weight:800;letter-spacing:-0.5px;margin-bottom:6px;">
            Welcome back, Layan
        </div>
        <div style="font-size:14px;opacity:0.8;">
            Your career intelligence dashboard &mdash; powered by O*NET &amp; Nebius AI.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Metrics
    st.markdown("""
    <div class="jd-metrics">
        <div class="jd-metric">
            <div class="jd-metric-num">312</div>
            <div class="jd-metric-label">Connections</div>
        </div>
        <div class="jd-metric">
            <div class="jd-metric-num">4</div>
            <div class="jd-metric-label">Certificates</div>
        </div>
        <div class="jd-metric">
            <div class="jd-metric-num">14</div>
            <div class="jd-metric-label">Skills Assessed</div>
        </div>
        <div class="jd-metric">
            <div class="jd-metric-num">91%</div>
            <div class="jd-metric-label">Top Job Match</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 2], gap="medium")

    with col1:
        st.markdown('<div class="jd-card">', unsafe_allow_html=True)
        st.markdown('<div class="jd-section-title">Platform Overview</div>', unsafe_allow_html=True)

        features = [
            ("LA", "Profile",             "LinkedIn-style professional profile with AI-enhanced bio."),
            ("CV", "CV Builder",          "Auto-generate a verified PDF CV from your Jadeer profile."),
            ("SK", "Skills Assessment",   "O*NET-based soft skills quiz with scenario-driven questions."),
            ("CR", "Certificates",        "Verify credentials from EC-Council, Coursera, edX & more."),
            ("JB", "Recommendations",    "AI job matching based on your occupation and skill scores."),
        ]
        for abbr, title, desc in features:
            st.markdown(f"""
            <div class="jd-entry">
                <div class="jd-entry-icon">{abbr}</div>
                <div>
                    <div class="jd-entry-title">{title}</div>
                    <div class="jd-entry-sub">{desc}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="jd-card">', unsafe_allow_html=True)
        st.markdown('<div class="jd-section-title">Occupation Match</div>', unsafe_allow_html=True)

        if not st.session_state.matched:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Match My Occupation", use_container_width=True, type="primary"):
                with st.spinner("Analyzing profile with AI..."):
                    time.sleep(2)
                st.session_state.matched = True
                st.rerun()
            st.markdown("<br>", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background:#eef2ff;border-radius:8px;padding:14px 16px;margin-bottom:14px;">
                <div style="font-size:15px;font-weight:700;color:#3b5bdb;">Software Developers</div>
                <div style="font-size:11px;color:#748ffc;margin-top:3px;font-weight:500;">O*NET &middot; 15-1252.00</div>
            </div>
            <div style="font-size:12px;font-weight:600;color:#8a93a2;text-transform:uppercase;
                        letter-spacing:0.5px;margin-bottom:10px;">Top skill importance</div>
            """, unsafe_allow_html=True)
            for s in SKILLS_DATA[:5]:
                bar(s["skill"], s["importance"])

        st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# PROFILE
# ══════════════════════════════════════════════════════════════════
elif page == "Profile":
    # Header card
    st.markdown("""
    <div class="jd-card-flat">
        <div class="jd-profile-banner"></div>
        <div class="jd-profile-body">
            <div class="jd-avatar">LA</div>
            <div class="jd-profile-name">Layan Alghamdi</div>
            <div class="jd-profile-headline">Software Engineer &middot; AI Enthusiast</div>
            <div class="jd-profile-meta">Riyadh, Saudi Arabia &nbsp;&middot;&nbsp; 312 connections</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1], gap="medium")

    with col1:
        # About
        st.markdown('<div class="jd-card">', unsafe_allow_html=True)
        st.markdown('<div class="jd-section-title">About</div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="font-size:14px;color:#374151;line-height:1.65;">
            Passionate software engineer building scalable AI-powered systems.
            Currently developing Jadeer — a career intelligence platform that combines
            O*NET occupational data with large language models to help professionals
            grow smarter and faster.
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Experience
        st.markdown('<div class="jd-card">', unsafe_allow_html=True)
        st.markdown('<div class="jd-section-title">Experience</div>', unsafe_allow_html=True)
        for i, exp in enumerate(EXPERIENCES):
            st.markdown(f"""
            <div class="jd-entry">
                <div class="jd-entry-icon" style="font-size:11px;">EXP</div>
                <div>
                    <div class="jd-entry-title">{exp["title"]}</div>
                    <div class="jd-entry-sub">{exp["company"]}</div>
                    <div class="jd-entry-date">{exp["period"]}</div>
                    <div class="jd-entry-desc">{exp["desc"]}</div>
                </div>
            </div>
            {"<hr class='jd-divider'>" if i < len(EXPERIENCES)-1 else ""}
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Education
        st.markdown('<div class="jd-card">', unsafe_allow_html=True)
        st.markdown('<div class="jd-section-title">Education</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="jd-entry">
            <div class="jd-entry-icon" style="font-size:10px;">KAU</div>
            <div>
                <div class="jd-entry-title">B.Sc. Computer Science</div>
                <div class="jd-entry-sub">King Abdulaziz University</div>
                <div class="jd-entry-date">2019 – 2023</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        # Skills
        st.markdown('<div class="jd-card">', unsafe_allow_html=True)
        st.markdown('<div class="jd-section-title">Top Skills</div>', unsafe_allow_html=True)
        for sk in ["Python", "FastAPI", "Machine Learning", "Docker", "Supabase", "PostgreSQL"]:
            st.markdown(f'<span class="jd-chip">{sk}</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Certs summary
        st.markdown('<div class="jd-card">', unsafe_allow_html=True)
        st.markdown('<div class="jd-section-title">Certificates</div>', unsafe_allow_html=True)
        for c in CERTS:
            kind = "green" if c["status"] == "Verified" else "amber"
            st.markdown(f"""
            <div style="display:flex;gap:10px;align-items:center;margin-bottom:11px;">
                <div class="cert-logo">{c["abbr"]}</div>
                <div style="flex:1;">
                    <div style="font-size:13px;font-weight:600;color:#1a1d23;">{c["name"]}</div>
                    <div style="font-size:11px;color:#9ca3af;">{c["issuer"]}</div>
                </div>
                {badge(c["status"], kind)}
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# CV BUILDER
# ══════════════════════════════════════════════════════════════════
elif page == "CV Builder":
    st.markdown('<div class="jd-page-title">CV Builder</div>', unsafe_allow_html=True)
    st.markdown('<div class="jd-page-sub">Generate a professional PDF from your Jadeer profile — with verified skill badges</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 2], gap="medium")

    with col1:
        st.markdown('<div class="jd-card">', unsafe_allow_html=True)
        st.markdown('<div class="jd-section-title">Sections</div>', unsafe_allow_html=True)
        inc_exp  = st.checkbox("Experience",          value=True)
        inc_edu  = st.checkbox("Education",           value=True)
        inc_cert = st.checkbox("Certificates",        value=True)
        inc_sk   = st.checkbox("Skills",              value=True)
        inc_sc   = st.checkbox("Skill Scores",        value=True)
        inc_bd   = st.checkbox("Verified Badges",     value=True)
        st.markdown('<hr class="jd-divider">', unsafe_allow_html=True)
        st.markdown('<div class="jd-section-title">Options</div>', unsafe_allow_html=True)
        threshold = st.slider("Badge Score Threshold (%)", 50, 90, 70)
        cv_name = st.text_input("CV Label", placeholder="e.g. Google Application")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Generate CV", use_container_width=True, type="primary"):
            with st.spinner("Building your CV..."):
                time.sleep(2)
            st.session_state.cv_done = True
            st.success("CV generated successfully.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="jd-card" style="min-height:520px;">', unsafe_allow_html=True)
        st.markdown('<div class="jd-section-title">Preview</div>', unsafe_allow_html=True)

        if st.session_state.cv_done:
            st.markdown("""
            <div style="border:1px solid #e8eaed;border-radius:8px;padding:28px;background:#fafafa;">
                <div style="border-bottom:2px solid #3b5bdb;padding-bottom:14px;margin-bottom:18px;">
                    <div style="font-size:20px;font-weight:800;color:#1a1d23;letter-spacing:-0.5px;">Layan Alghamdi</div>
                    <div style="font-size:12px;color:#6b7280;margin-top:3px;">Software Engineer &nbsp;|&nbsp; Riyadh, SA &nbsp;|&nbsp; layan@example.com</div>
                </div>

                <div style="margin-bottom:16px;">
                    <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1px;
                                color:#3b5bdb;margin-bottom:5px;">Profile</div>
                    <div style="font-size:13px;color:#374151;line-height:1.55;">
                        Passionate software engineer building scalable AI-powered systems...
                    </div>
                </div>

                <div style="margin-bottom:16px;">
                    <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1px;
                                color:#3b5bdb;margin-bottom:6px;">Experience</div>
                    <div style="font-size:13px;font-weight:600;color:#1a1d23;">Software Engineer — Tech Startup, Riyadh</div>
                    <div style="font-size:11px;color:#9ca3af;">2023 – Present</div>
                    <div style="font-size:12px;color:#4b5563;margin-top:3px;">Built microservices with FastAPI and Docker...</div>
                </div>

                <div style="margin-bottom:16px;">
                    <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1px;
                                color:#3b5bdb;margin-bottom:8px;">Verified Soft Skills</div>
                    <div style="display:flex;flex-wrap:wrap;gap:5px;">
                        <span style="background:#ebfbee;color:#2f9e44;padding:3px 8px;border-radius:4px;font-size:11px;font-weight:600;">+ Critical Thinking 82%</span>
                        <span style="background:#ebfbee;color:#2f9e44;padding:3px 8px;border-radius:4px;font-size:11px;font-weight:600;">+ Active Learning 76%</span>
                        <span style="background:#ebfbee;color:#2f9e44;padding:3px 8px;border-radius:4px;font-size:11px;font-weight:600;">+ Problem Solving 73%</span>
                        <span style="background:#f3f4f6;color:#6b7280;padding:3px 8px;border-radius:4px;font-size:11px;">Time Management 58%</span>
                    </div>
                </div>

                <div>
                    <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1px;
                                color:#3b5bdb;margin-bottom:5px;">Certificates</div>
                    <div style="font-size:12px;color:#374151;">AWS Certified Developer &nbsp;·&nbsp; Python Professional &nbsp;·&nbsp; CEH</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.download_button(
                "Download PDF",
                data=b"[Connect backend for real PDF output]",
                file_name="Jadeer_CV_Layan.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        else:
            st.markdown("""
            <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
                        height:400px;color:#c1c7d0;text-align:center;">
                <div style="font-size:36px;font-weight:200;color:#d1d5db;margin-bottom:12px;">CV</div>
                <div style="font-size:14px;font-weight:600;color:#6b7280;">Preview will appear here</div>
                <div style="font-size:13px;color:#9ca3af;margin-top:4px;">Configure options and click Generate</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# SKILLS ASSESSMENT
# ══════════════════════════════════════════════════════════════════
elif page == "Skills Assessment":
    if not st.session_state.started:
        st.markdown('<div class="jd-page-title">Skills Assessment</div>', unsafe_allow_html=True)
        st.markdown('<div class="jd-page-sub">Scenario-based evaluation across 14 O*NET soft skills for your occupation</div>', unsafe_allow_html=True)

        col1, col2 = st.columns([1, 2], gap="medium")

        with col1:
            st.markdown('<div class="jd-card">', unsafe_allow_html=True)
            st.markdown('<div class="jd-section-title">Select Skill</div>', unsafe_allow_html=True)

            names = [s["skill"] for s in SKILLS_DATA]
            sel = st.selectbox("Skill", names, label_visibility="collapsed")
            st.session_state.sel_skill = sel
            info = next(s for s in SKILLS_DATA if s["skill"] == sel)
            p = info["priority"]
            pk = "blue" if p == "HIGH" else "amber" if p == "MEDIUM" else "gray"

            st.markdown(f"""
            <div style="background:#f7f8fa;border-radius:8px;padding:14px 16px;margin-top:12px;margin-bottom:14px;">
                <div style="font-size:13px;font-weight:600;color:#1a1d23;margin-bottom:4px;">{sel}</div>
                <div style="font-size:12px;color:#8a93a2;margin-bottom:8px;">{info["category"]} Skills</div>
                {badge(p + " priority", pk)}
                <div style="margin-top:12px;">
            """, unsafe_allow_html=True)
            bar("Importance for Software Dev", info["importance"])
            bar("Required Level", info["level"], "#748ffc")
            st.markdown("</div></div>", unsafe_allow_html=True)

            if st.button("Start Assessment", use_container_width=True, type="primary"):
                st.session_state.started   = True
                st.session_state.answers   = {}
                st.session_state.submitted = False
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="jd-card">', unsafe_allow_html=True)
            st.markdown('<div class="jd-section-title">All 14 O*NET Soft Skills — Software Developer</div>', unsafe_allow_html=True)

            tab1, tab2 = st.tabs(["Thinking Skills", "Social Skills"])
            with tab1:
                for s in [x for x in SKILLS_DATA if x["category"] == "Thinking"]:
                    bar(s["skill"], s["importance"], priority_color(s["priority"]))
            with tab2:
                for s in [x for x in SKILLS_DATA if x["category"] == "Social"]:
                    bar(s["skill"], s["importance"], priority_color(s["priority"]))
            st.markdown('</div>', unsafe_allow_html=True)

    elif not st.session_state.submitted:
        st.markdown(f'<div class="jd-page-title">{st.session_state.sel_skill}</div>', unsafe_allow_html=True)
        st.markdown('<div class="jd-page-sub">Software Developers &nbsp;·&nbsp; 5 scenario-based questions &nbsp;·&nbsp; Select the best answer</div>', unsafe_allow_html=True)

        for i, q in enumerate(QUESTIONS):
            st.markdown(f"""
            <div class="q-card">
                <div class="q-num">Question {i+1} of {len(QUESTIONS)} &nbsp;&middot;&nbsp; {q["skill"]}</div>
                <div class="q-text">{q["q"]}</div>
            """, unsafe_allow_html=True)
            ans = st.radio(
                f"q{i}",
                list(q["opts"].keys()),
                format_func=lambda k, q=q: f"{k}.  {q['opts'][k]}",
                key=f"qr_{i}",
                label_visibility="collapsed",
            )
            st.session_state.answers[str(i)] = ans
            st.markdown("</div>", unsafe_allow_html=True)

        colA, colB, colC = st.columns([2, 2, 1])
        with colA:
            if st.button("Submit Assessment", use_container_width=True, type="primary"):
                st.session_state.submitted = True
                st.rerun()
        with colC:
            if st.button("Cancel", use_container_width=True):
                st.session_state.started = False
                st.rerun()

    else:
        # Results
        score = sum(1 for i, q in enumerate(QUESTIONS)
                    if st.session_state.answers.get(str(i), "").upper() == q["ans"])
        total = len(QUESTIONS)
        pct   = round(score / total * 100)
        passed = score >= 4

        bg  = "#ebfbee" if passed else "#fff5f5"
        fg  = "#2f9e44" if passed else "#e03131"
        lbl = "Passed" if passed else "Not Passed"

        st.markdown(f"""
        <div class="result-banner" style="background:{bg};border:1px solid {'#b2f2bb' if passed else '#ffc9c9'};">
            <div class="result-score" style="color:{fg};">{score}/{total}</div>
            <div class="result-sub" style="color:{fg};font-weight:700;">{lbl}</div>
            <div class="result-label" style="color:{fg};">{pct}% &nbsp;·&nbsp; Pass threshold: 4 / 5</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="jd-page-sub" style="margin-bottom:12px;">Question breakdown</div>', unsafe_allow_html=True)
        for i, q in enumerate(QUESTIONS):
            ua = st.session_state.answers.get(str(i), "")
            ok = ua.upper() == q["ans"].upper()
            with st.expander(f"{'Correct' if ok else 'Incorrect'}  —  Q{i+1}: {q['q'][:75]}..."):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**Your answer:** {ua}.  {q['opts'].get(ua.upper(), '—')}")
                with c2:
                    st.markdown(f"**Correct answer:** {q['ans']}.  {q['opts'][q['ans']]}")
                st.info(q["exp"])

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Retake Assessment", use_container_width=True):
                st.session_state.started   = True
                st.session_state.answers   = {}
                st.session_state.submitted = False
                st.rerun()
        with c2:
            if st.button("Back to Skills", use_container_width=True):
                st.session_state.started   = False
                st.session_state.submitted = False
                st.rerun()


# ══════════════════════════════════════════════════════════════════
# CERTIFICATES
# ══════════════════════════════════════════════════════════════════
elif page == "Certificates":
    st.markdown('<div class="jd-page-title">Certificate Verification</div>', unsafe_allow_html=True)
    st.markdown('<div class="jd-page-sub">Verify credentials from trusted issuers — verified certs appear as badges on your profile</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 2], gap="medium")

    with col1:
        st.markdown('<div class="jd-card">', unsafe_allow_html=True)
        st.markdown('<div class="jd-section-title">Add Certificate</div>', unsafe_allow_html=True)
        cert_name = st.text_input("Certificate Name", placeholder="e.g. AWS Certified Developer")
        issuer = st.selectbox("Issuer", ["EC-Council", "CompTIA", "edX", "Coursera", "Udemy"])
        cred_id = st.text_input("Credential ID", placeholder="e.g. ECC12345678")
        if st.button("Verify & Add", use_container_width=True, type="primary"):
            if cert_name and cred_id:
                with st.spinner("Contacting issuer..."):
                    time.sleep(2)
                st.success(f"{cert_name} verified via {issuer}.")
            else:
                st.warning("Fill in all fields.")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="jd-card">', unsafe_allow_html=True)
        st.markdown('<div class="jd-section-title">Supported Issuers</div>', unsafe_allow_html=True)
        for iss in ["EC-Council", "CompTIA", "edX", "Coursera", "Udemy"]:
            st.markdown(f'<div style="font-size:13px;color:#374151;padding:5px 0;border-bottom:1px solid #f3f4f6;">{iss}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="jd-card">', unsafe_allow_html=True)
        st.markdown('<div class="jd-section-title">My Certificates</div>', unsafe_allow_html=True)
        for c in CERTS:
            kind = "green" if c["status"] == "Verified" else "amber"
            st.markdown(f"""
            <div class="cert-row">
                <div class="cert-logo">{c["abbr"]}</div>
                <div style="flex:1;">
                    <div class="cert-name">{c["name"]}</div>
                    <div class="cert-meta">{c["issuer"]} &nbsp;·&nbsp; Issued {c["date"]}</div>
                </div>
                {badge(c["status"], kind)}
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# RECOMMENDATIONS
# ══════════════════════════════════════════════════════════════════
elif page == "Recommendations":
    st.markdown('<div class="jd-page-title">Job Recommendations</div>', unsafe_allow_html=True)
    st.markdown('<div class="jd-page-sub">AI-matched roles based on your occupation profile and O*NET skill data</div>', unsafe_allow_html=True)

    # Occupation context
    st.markdown("""
    <div class="jd-card" style="display:flex;gap:20px;align-items:center;padding:18px 22px;">
        <div style="flex:1;">
            <div style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.6px;
                        color:#8a93a2;margin-bottom:4px;">Matched Occupation</div>
            <div style="font-size:16px;font-weight:700;color:#1a1d23;">Software Developers</div>
            <div style="font-size:12px;color:#9ca3af;margin-top:2px;">O*NET 15-1252.00 &nbsp;·&nbsp; 3 yrs experience &nbsp;·&nbsp; Riyadh</div>
        </div>
        <div style="text-align:right;">
            <div style="font-size:32px;font-weight:800;color:#3b5bdb;letter-spacing:-1px;line-height:1;">91%</div>
            <div style="font-size:11px;color:#9ca3af;margin-top:2px;">Top match</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    colF1, colF2 = st.columns(2)
    with colF1:
        st.selectbox("Location", ["All locations", "Riyadh", "Remote", "Jeddah"])
    with colF2:
        st.selectbox("Job Type", ["All types", "Full-time", "Part-time", "Contract"])

    st.markdown("<br>", unsafe_allow_html=True)

    for job in JOBS:
        match_col = "#2f9e44" if job["match"] >= 85 else "#3b5bdb" if job["match"] >= 75 else "#e67700"
        chips = "".join(f'<span class="jd-chip">{s}</span>' for s in job["skills"])
        st.markdown(f"""
        <div class="job-card">
            <div style="flex:1;">
                <div class="job-title">{job["title"]}</div>
                <div class="job-company">{job["company"]}</div>
                <div class="job-meta">{job["location"]} &nbsp;·&nbsp; Full-time</div>
                <div style="margin-top:10px;">{chips}</div>
            </div>
            <div style="text-align:right;min-width:70px;padding-left:16px;">
                <div class="job-match-num" style="color:{match_col};">{job["match"]}%</div>
                <div class="job-match-label">match</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # AI Bio
    st.markdown('<div class="jd-card" style="margin-top:8px;">', unsafe_allow_html=True)
    st.markdown('<div class="jd-section-title">AI Bio Generator</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:13px;color:#6b7280;margin-bottom:12px;">Generate a tailored professional bio for a specific target role.</div>', unsafe_allow_html=True)
    role = st.text_input("Target Role", placeholder="e.g. Senior Software Engineer at Google")
    if st.button("Generate Bio", use_container_width=False, type="primary"):
        if role:
            with st.spinner("Generating with Nebius AI..."):
                time.sleep(2)
            st.markdown(f"""
            <div style="background:#f7f8fa;border:1px solid #e8eaed;border-radius:8px;
                        padding:16px;font-size:14px;color:#374151;line-height:1.65;margin-top:12px;">
                Results-driven software engineer with 3 years of experience building scalable AI-powered systems
                using Python, FastAPI, and Docker. Passionate about leveraging machine learning to deliver real-world
                impact. Seeking a <strong>{role}</strong> position where I can contribute to
                high-impact products and grow as a technical leader.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("Enter a target role first.")
    st.markdown('</div>', unsafe_allow_html=True)
