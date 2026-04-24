import base64
import os
from pathlib import Path

import psycopg2
import streamlit as st
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

st.set_page_config(page_title="", page_icon="🌀", layout="centered")

# ─── Jadeer brand palette ────────────────────────────────────────────────
BG = "#0A0A0F"
SURFACE = "#141420"
SURFACE_2 = "#1C1C2B"
BORDER = "#2A2A3D"
PURPLE = "#8367FF"
PURPLE_DEEP = "#6B4EFF"
TEAL = "#4DD4AC"
TEXT = "#F5F5F7"
TEXT_MID = "#A8A8BD"
TEXT_DIM = "#6E6E85"


def _logo_data_uri(filename: str) -> str:
    path = BASE_DIR / filename
    if not path.exists():
        return ""
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{data}"


LOGO_URI = _logo_data_uri("logo_transparent.png") or _logo_data_uri("image.png")


st.markdown(
    f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');

        html, body, [class*="css"] {{
            direction: rtl;
            font-family: 'IBM Plex Sans Arabic', 'Space Grotesk', sans-serif !important;
            color: {TEXT};
        }}
        .stApp {{
            background: radial-gradient(1200px 700px at 70% -10%, rgba(131,103,255,0.18) 0%, transparent 60%),
                        radial-gradient(900px 600px at -10% 110%, rgba(77,212,172,0.10) 0%, transparent 55%),
                        {BG};
        }}

        /* Hide default Streamlit chrome */
        header[data-testid="stHeader"] {{ background: transparent; }}
        #MainMenu, footer {{ visibility: hidden; }}

        .block-container {{ padding-top: 2rem !important; }}

        /* Header card */
        .jadeer-header {{
            text-align: center;
            padding: 32px 20px 24px;
            margin-bottom: 28px;
        }}
        .jadeer-logo {{
            width: 160px; height: auto;
            margin: 0 auto 12px;
            display: block;
            filter: drop-shadow(0 10px 35px rgba(131,103,255,0.35));
        }}
        .jadeer-subtitle {{
            color: {TEXT_MID};
            font-size: 15px;
            font-weight: 400;
            margin: 0;
            line-height: 1.7;
        }}
        .jadeer-divider {{
            width: 60px; height: 3px;
            background: linear-gradient(90deg, {PURPLE} 0%, {TEAL} 100%);
            border-radius: 3px;
            margin: 16px auto 0;
        }}

        /* Question cards */
        .q-card {{
            background: {SURFACE};
            border: 1px solid {BORDER};
            border-radius: 18px;
            padding: 22px 24px;
            margin-bottom: 16px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.25);
            position: relative;
            overflow: hidden;
        }}
        .q-card::before {{
            content: "";
            position: absolute;
            inset-inline-start: 0;
            top: 0;
            bottom: 0;
            width: 3px;
            background: linear-gradient(180deg, {PURPLE} 0%, {TEAL} 100%);
        }}
        .q-title {{
            color: {TEXT};
            font-weight: 600;
            font-size: 17px;
            margin-bottom: 16px;
            line-height: 1.75;
        }}
        .q-number {{
            display: inline-block;
            background: linear-gradient(135deg, {PURPLE} 0%, {PURPLE_DEEP} 100%);
            color: white;
            font-family: 'Space Grotesk', sans-serif;
            font-weight: 700;
            font-size: 13px;
            padding: 3px 12px;
            border-radius: 999px;
            margin-left: 8px;
            vertical-align: middle;
        }}
        .rank-hint {{
            color: {TEXT_MID};
            font-size: 13px;
            margin-bottom: 14px;
            padding: 8px 12px;
            background: rgba(77,212,172,0.08);
            border-right: 3px solid {TEAL};
            border-radius: 8px;
        }}

        /* Radio options */
        div[role="radiogroup"] > label {{
            background: {SURFACE_2};
            border: 1px solid {BORDER};
            border-radius: 12px;
            padding: 12px 16px;
            margin: 8px 0;
            transition: all .18s ease;
            cursor: pointer;
        }}
        div[role="radiogroup"] > label:hover {{
            background: rgba(131,103,255,0.10);
            border-color: {PURPLE};
            transform: translateX(-2px);
        }}
        div[role="radiogroup"] > label p {{
            color: {TEXT} !important;
            font-family: 'IBM Plex Sans Arabic', sans-serif !important;
            font-size: 15px !important;
            text-align: right !important;
            direction: rtl !important;
        }}
        div[role="radiogroup"] > label {{
            text-align: right !important;
        }}
        .stSelectbox > div,
        .stSelectbox div[data-baseweb="select"] div {{
            text-align: right !important;
            direction: rtl !important;
        }}
        .stForm, [data-testid="stForm"] {{
            direction: rtl !important;
        }}
        div[role="radiogroup"] > label[data-checked="true"],
        div[role="radiogroup"] input:checked ~ div {{
            background: rgba(131,103,255,0.15) !important;
            border-color: {PURPLE} !important;
        }}

        /* Selectbox */
        div[data-baseweb="select"] > div {{
            background: {SURFACE_2} !important;
            border-color: {BORDER} !important;
            color: {TEXT} !important;
            border-radius: 10px !important;
        }}
        div[data-baseweb="select"] > div:hover {{
            border-color: {PURPLE} !important;
        }}
        .stSelectbox label {{
            color: {TEXT} !important;
            font-family: 'IBM Plex Sans Arabic', sans-serif !important;
            font-weight: 500 !important;
            font-size: 15px !important;
        }}

        /* Submit button */
        .stButton > button, .stFormSubmitButton > button {{
            background: linear-gradient(135deg, {PURPLE} 0%, {PURPLE_DEEP} 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 14px 28px !important;
            font-family: 'IBM Plex Sans Arabic', sans-serif !important;
            font-weight: 600 !important;
            font-size: 16px !important;
            width: 100% !important;
            box-shadow: 0 6px 20px rgba(131,103,255,0.35) !important;
            transition: all .2s ease !important;
        }}
        .stButton > button:hover, .stFormSubmitButton > button:hover {{
            transform: translateY(-1px);
            box-shadow: 0 10px 28px rgba(131,103,255,0.5) !important;
        }}

        /* Success / error boxes */
        .success-box {{
            background: linear-gradient(135deg, rgba(77,212,172,0.15) 0%, rgba(77,212,172,0.05) 100%);
            border: 1px solid {TEAL};
            color: {TEXT};
            border-radius: 16px;
            padding: 24px;
            text-align: center;
            font-weight: 600;
            font-size: 17px;
        }}
        .success-box .ref {{
            font-family: 'Space Grotesk', monospace;
            color: {TEXT_MID};
            font-size: 12px;
            margin-top: 10px;
            direction: ltr;
        }}
        .success-box .checkmark {{
            width: 56px; height: 56px;
            background: {TEAL};
            color: {BG};
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 14px;
            font-size: 28px;
            font-weight: 700;
        }}
        .error-box {{
            background: rgba(255, 100, 100, 0.08);
            border: 1px solid rgba(255, 100, 100, 0.4);
            color: #FFB4B4;
            border-radius: 12px;
            padding: 14px 18px;
            font-size: 14px;
            line-height: 1.8;
        }}

        /* Footer */
        .jadeer-footer {{
            text-align: center;
            color: {TEXT_DIM};
            font-size: 12px;
            margin-top: 32px;
            padding-top: 20px;
            border-top: 1px solid {BORDER};
            font-family: 'Space Grotesk', sans-serif;
        }}
        .jadeer-footer .dot {{
            color: {TEAL};
            margin: 0 6px;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)


def _cfg(key: str, default=None):
    try:
        if key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return os.getenv(key, default)


def get_connection():
    return psycopg2.connect(
        host=_cfg("SUPABASE_DB_HOST"),
        port=int(_cfg("SUPABASE_DB_PORT", "6543")),
        dbname=_cfg("SUPABASE_DB_NAME", "postgres"),
        user=_cfg("SUPABASE_DB_USER"),
        password=_cfg("SUPABASE_DB_PASSWORD"),
        sslmode=_cfg("SUPABASE_DB_SSLMODE", "disable"),
        connect_timeout=10,
    )


def ensure_schema():
    sql = (BASE_DIR / "schema.sql").read_text(encoding="utf-8")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)


def insert_response(payload: dict):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into survey_responses (
                    q1_skills_proof, q2_cert_verification,
                    q3_cv_tailoring, q4_cv_biggest_problem,
                    q5_rank_skills_assessment, q5_rank_cert_verification,
                    q5_rank_cv_tailoring, q5_rank_smart_matching
                ) values (%s, %s, %s, %s, %s, %s, %s, %s)
                returning id;
                """,
                (
                    payload["q1"], payload["q2"], payload["q3"], payload["q4"],
                    payload["q5_skills"], payload["q5_cert"],
                    payload["q5_cv"], payload["q5_match"],
                ),
            )
            return cur.fetchone()[0]


Q1_OPTIONS = [
    "أ) المقابلة الشخصية كافية",
    "ب) اختبار مواقف عملية",
    "ج) توصية من شخص اشتغل معه",
    "د) خبرته السابقة بالسيرة الذاتية تكفي",
]
Q2_OPTIONS = [
    "أ) الشركة هي اللي لازم تتحقق بنفسها قبل التوظيف",
    "ب) لازم يكون فيه جهة أو منصة توثق الشهادات من البداية",
    "ج) الشهادات ما تفرق، الخبرة العملية أهم من أي شهادة",
    "د) المقابلة الشخصية كفيلة تبين مين فاهم ومين لا",
]
Q3_OPTIONS = [
    "أ) أرسل نفس السيرة للوظيفتين",
    "ب) أعدل يدوي بس ما أعرف وش بالضبط أغير",
    "ج) أتمنى لو فيه أداة تعدلها لي حسب كل وظيفة",
    "د) أقدم على وحدة بس عشان ما أتعب",
]
Q4_OPTIONS = [
    "أ) ما أعرف كيف أبرز مهاراتي الشخصية",
    "ب) ما أدري وش الشركات فعلا تدور عليه",
    "ج) كل السير الذاتية تطلع نفس الشكل",
    "د) ما عندي مشكلة بصراحة",
]
RANK_CHOICES = [1, 2, 3, 4]
Q5_ITEMS = [
    ("q5_skills", "تقييم مهاراتك الشخصية باختبار مواقف"),
    ("q5_cert", "التحقق من شهاداتك وتوثيقها"),
    ("q5_cv", "تعديل سيرتك الذاتية حسب كل وظيفة"),
    ("q5_match", "بحث ذكي يربطك بالشركة المناسبة"),
]


logo_html = f'<img class="jadeer-logo" src="{LOGO_URI}" alt="Jadeer" />' if LOGO_URI else ""
st.markdown(
    f"""
    <div class="jadeer-header">
        {logo_html}
        <p class="jadeer-subtitle">شاركنا رأيك وساعدنا نبني منصة تخدمك بشكل أفضل</p>
        <div class="jadeer-divider"></div>
    </div>
    """,
    unsafe_allow_html=True,
)

if "submitted_id" not in st.session_state:
    st.session_state.submitted_id = None

if st.session_state.submitted_id:
    st.markdown(
        f"""
        <div class="success-box">
            <div class="checkmark">✓</div>
            تم تسجيل ردك بنجاح. شكرا لوقتك!
            <div class="ref">REF: {st.session_state.submitted_id}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("إرسال رد جديد"):
        st.session_state.submitted_id = None
        st.rerun()
    st.stop()


with st.form("survey_form", clear_on_submit=False):
    st.markdown(
        '<div class="q-card"><div class="q-title"><span class="q-number">Q1</span> '
        'وش أكثر شي يثبت إن الشخص عنده مهارات شخصية زي التواصل والقيادة؟</div>',
        unsafe_allow_html=True,
    )
    q1 = st.radio("q1", Q1_OPTIONS, index=None, label_visibility="collapsed", key="q1")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        '<div class="q-card"><div class="q-title"><span class="q-number">Q2</span> '
        'لو شركة عاملت شهادتك الأونلاين اللي درست عليها شهر نفس معاملة شهادة شراها أحد ب ٥٠ ريال، وش تشوف الحل؟</div>',
        unsafe_allow_html=True,
    )
    q2 = st.radio("q2", Q2_OPTIONS, index=None, label_visibility="collapsed", key="q2")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        '<div class="q-card"><div class="q-title"><span class="q-number">Q3</span> '
        'قدمت على وظيفتين مختلفة، وحدة "مدير مشاريع" والثانية "أخصائي موارد بشرية". وش تسوي بسيرتك الذاتية؟</div>',
        unsafe_allow_html=True,
    )
    q3 = st.radio("q3", Q3_OPTIONS, index=None, label_visibility="collapsed", key="q3")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        '<div class="q-card"><div class="q-title"><span class="q-number">Q4</span> '
        'وش أكبر مشكلة تواجهك بسيرتك الذاتية؟</div>',
        unsafe_allow_html=True,
    )
    q4 = st.radio("q4", Q4_OPTIONS, index=None, label_visibility="collapsed", key="q4")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        '<div class="q-card"><div class="q-title"><span class="q-number">Q5</span> '
        'لو فيه منصة تقدم لك هالخدمات، رتبها من الأهم لك إلى الأقل</div>'
        '<div class="rank-hint">اختر رقم فريد من ١ إلى ٤ لكل خدمة، ١ = الأهم</div>',
        unsafe_allow_html=True,
    )
    ranks = {}
    for key, label in Q5_ITEMS:
        ranks[key] = st.selectbox(
            label, RANK_CHOICES, index=None, key=f"rank_{key}", placeholder="اختر الترتيب…"
        )
    st.markdown("</div>", unsafe_allow_html=True)

    submitted = st.form_submit_button("إرسال الإجابات")


if submitted:
    errors = []
    if not q1: errors.append("الرجاء الإجابة على السؤال الأول")
    if not q2: errors.append("الرجاء الإجابة على السؤال الثاني")
    if not q3: errors.append("الرجاء الإجابة على السؤال الثالث")
    if not q4: errors.append("الرجاء الإجابة على السؤال الرابع")
    if any(v is None for v in ranks.values()):
        errors.append("الرجاء ترتيب جميع الخدمات في السؤال الخامس")
    elif len(set(ranks.values())) != len(ranks):
        errors.append("لازم ترتيب الخدمات بأرقام مختلفة (١ و ٢ و ٣ و ٤) بدون تكرار")

    if errors:
        st.markdown(
            '<div class="error-box">' + "<br>".join(f"• {e}" for e in errors) + "</div>",
            unsafe_allow_html=True,
        )
    else:
        try:
            ensure_schema()
            new_id = insert_response({
                "q1": q1, "q2": q2, "q3": q3, "q4": q4,
                "q5_skills": ranks["q5_skills"],
                "q5_cert": ranks["q5_cert"],
                "q5_cv": ranks["q5_cv"],
                "q5_match": ranks["q5_match"],
            })
            st.session_state.submitted_id = str(new_id)
            st.rerun()
        except Exception as e:
            st.markdown(
                f'<div class="error-box">تعذر حفظ الرد في قاعدة البيانات:<br><code>{e}</code></div>',
                unsafe_allow_html=True,
            )


st.markdown(
    f'<div class="jadeer-footer">Jadeer <span class="dot">●</span> Rising by merit</div>',
    unsafe_allow_html=True,
)
