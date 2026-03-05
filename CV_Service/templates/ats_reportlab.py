from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

LEFT, RIGHT, TOP, BOTTOM = 50, 50, 60, 50
FONT, FONT_BOLD = "Helvetica", "Helvetica-Bold"


def _wrap_text(
    c,
    text: str,
    x: float,
    y: float,
    max_width: float,
    font: str,
    size: int,
    leading: int,
):
    c.setFont(font, size)
    words = (text or "").split()
    line = ""
    for w in words:
        test = (line + " " + w).strip()
        if stringWidth(test, font, size) <= max_width:
            line = test
        else:
            if line:
                c.drawString(x, y, line)
                y -= leading
            line = w
    if line:
        c.drawString(x, y, line)
        y -= leading
    return y


def _date_only(v):
    if not v:
        return ""
    s = str(v)
    return s.split("T")[0]


def generate_cv_pdf(
    data: dict,
    include_experience: bool,
    include_education: bool,
    include_certificates: bool,
    include_skills: bool,
    include_scores: bool,
    include_verified_badges: bool,
) -> bytes:
    profile = data.get("profile", {}) or {}
    experiences = data.get("experiences", []) or []
    education = data.get("education", []) or []
    certs = data.get("certificates", []) or []
    skills = data.get("skills", []) or []

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    max_width = w - LEFT - RIGHT
    y = h - TOP

    def new_page_if_needed(min_y=120):
        nonlocal y
        if y < BOTTOM + min_y:
            c.showPage()
            y = h - TOP

    def section(title: str):
        nonlocal y
        new_page_if_needed(140)
        y -= 6
        c.setFont(FONT_BOLD, 12)
        c.drawString(LEFT, y, title.upper())
        y -= 6
        c.setLineWidth(1)
        c.line(LEFT, y, LEFT + max_width, y)
        y -= 14

    # ── Header ───────────────────────────────────────────────────────────────
    full_name = profile.get("full_name") or "Unnamed Candidate"
    c.setFont(FONT_BOLD, 18)
    c.drawString(LEFT, y, full_name)
    y -= 10

    # Divider line under name (clean/pro feel)
    c.setLineWidth(1)
    c.line(LEFT, y, LEFT + max_width, y)
    y -= 12

    meta_parts = []
    if profile.get("location"):
        meta_parts.append(profile["location"])
    if profile.get("phone"):
        meta_parts.append(profile["phone"])
    if profile.get("linkedin_url"):
        meta_parts.append(profile["linkedin_url"])
    meta = " | ".join(meta_parts)

    if meta:
        c.setFont(FONT, 10)
        y = _wrap_text(c, meta, LEFT, y, max_width, FONT, 10, 12)
        y -= 6

    # ── Summary ──────────────────────────────────────────────────────────────
    bio = profile.get("bio")
    if bio:
        section("Summary")
        y = _wrap_text(c, bio, LEFT, y, max_width, FONT, 10, 13)

    # ── Experience ───────────────────────────────────────────────────────────
    if include_experience and experiences:
        section("Experience")
        for exp in experiences:
            new_page_if_needed(170)

            title = exp.get("job_title") or "Role"
            company = exp.get("company") or "Company"

            # Left: title/company
            c.setFont(FONT_BOLD, 11)
            c.drawString(LEFT, y, f"{title} — {company}")

            # Right: dates (aligned to the right edge)
            dates = " - ".join(
                [d for d in [_date_only(exp.get("start_date")), _date_only(exp.get("end_date"))] if d]
            )
            if dates:
                c.setFont(FONT, 10)
                date_width = stringWidth(dates, FONT, 10)
                c.drawString(LEFT + max_width - date_width, y, dates)

            y -= 14

            desc = exp.get("description") or ""
            if desc:
                # Bullet formatting
                y = _wrap_text(c, "• " + desc, LEFT + 8, y, max_width - 8, FONT, 10, 13)
                y -= 4

            y -= 6

    # ── Education ────────────────────────────────────────────────────────────
    if include_education and education:
        section("Education")
        for edu in education:
            new_page_if_needed(140)

            degree = edu.get("degree") or "Degree"
            inst = edu.get("institution") or "Institution"
            field = edu.get("field_of_study")

            line = f"{degree} — {inst}"
            if field:
                line += f" ({field})"

            c.setFont(FONT_BOLD, 11)
            c.drawString(LEFT, y, line)

            dates = " - ".join(
                [d for d in [_date_only(edu.get("start_date")), _date_only(edu.get("end_date"))] if d]
            )
            if dates:
                c.setFont(FONT, 10)
                date_width = stringWidth(dates, FONT, 10)
                c.drawString(LEFT + max_width - date_width, y, dates)

            y -= 16

    # ── Certificates ─────────────────────────────────────────────────────────
    if include_certificates and certs:
        section("Certificates")
        for cert in certs:
            new_page_if_needed(140)

            name = cert.get("certificate_name") or "Certificate"
            issuer = cert.get("issuer") or ""
            issue_date = _date_only(cert.get("issue_date"))

            badge = ""
            if include_verified_badges:
                badge = "Verified" if cert.get("is_verified") else "Unverified"

            line = name
            if issuer:
                line += f" — {issuer}"
            if issue_date:
                line += f" ({issue_date})"
            if badge:
                line += f" [{badge}]"

            c.setFont(FONT, 10)
            y = _wrap_text(c, "• " + line, LEFT + 8, y, max_width - 8, FONT, 10, 12)

        y -= 6

    # ── Skills ───────────────────────────────────────────────────────────────
    if include_skills and skills:
        section("Skills")

        items = []
        for s in skills:
            name = s.get("custom_skill_name") or s.get("name") or "Skill"
            score = s.get("score")
            if include_scores and score is not None:
                try:
                    items.append(f"{name} ({int(score)}/100)")
                except Exception:
                    items.append(name)
            else:
                items.append(name)

        # Cleaner than commas: " • " separators
        skills_text = " • ".join(items)
        y = _wrap_text(c, skills_text, LEFT, y, max_width, FONT, 10, 13)

    c.showPage()
    c.save()
    return buf.getvalue()