from fastapi import FastAPI, Header, Response, Query, HTTPException

from clients.profile_client import get_profile_bundle
from utils.merge import dummy_bundle, merge_real_with_dummy
from templates.ats_reportlab import generate_cv_pdf

app = FastAPI(title="CV Generation Service", version="0.2.1")


@app.get("/cv/health", tags=["system"])
def health():
    return {"status": "ok", "service": "cv"}


@app.get("/cv/me.pdf", tags=["cv"])
async def cv_me_pdf(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),

    # section toggles
    include_experience: bool = Query(True),
    include_education: bool = Query(True),
    include_certificates: bool = Query(True),
    include_skills: bool = Query(True),

    # display toggles
    include_scores: bool = Query(True),
    include_verified_badges: bool = Query(True),

    # optional dev/demo mode (explicit only)
    demo: bool = Query(False),
):
    # ✅ Gateway contract: CV service must receive X-User-Id from gateway
    if not x_user_id and not demo:
        raise HTTPException(status_code=401, detail="Missing X-User-Id")

    if demo:
        real = {"profile": {}, "experiences": [], "education": [], "certificates": [], "skills": []}
        data = merge_real_with_dummy(real, dummy_bundle())
    else:
        real = await get_profile_bundle(x_user_id)  # type: ignore[arg-type]
        data = merge_real_with_dummy(real, dummy_bundle())

    pdf_bytes = generate_cv_pdf(
        data=data,
        include_experience=include_experience,
        include_education=include_education,
        include_certificates=include_certificates,
        include_skills=include_skills,
        include_scores=include_scores,
        include_verified_badges=include_verified_badges,
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "inline; filename=cv.pdf"},
    )

@app.get("/cv/demo.pdf")
async def cv_demo_pdf(x_user_id: str | None = Header(default=None, alias="X-User-Id")):

    if x_user_id:
        real = await get_profile_bundle(x_user_id)
    else:
        real = {}

    data = merge_real_with_dummy(real, dummy_bundle())

    pdf_bytes = generate_cv_pdf(
        data=data,
        include_experience=True,
        include_education=True,
        include_certificates=True,
        include_skills=True,
        include_scores=True,
        include_verified_badges=True,
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "inline; filename=cv.pdf"},
    )