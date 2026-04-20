import os
import json
import logging
import time
from fastapi import FastAPI, Header, HTTPException, Request, Query
from fastapi.responses import JSONResponse
from supabase import create_client, Client
from fastapi.encoders import jsonable_encoder
from dotenv import load_dotenv
import uuid as _uuid 

_CUSTOM_ISSUER_SLUG = "custom"


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return json.dumps({
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        })

_handler = logging.StreamHandler()
_handler.setFormatter(_JsonFormatter())
logging.basicConfig(level=logging.INFO, handlers=[_handler])

from models.profile import ProfileUpdate
from models.experiences import ExperienceCreate, ExperienceUpdate
from models.education import EducationCreate, EducationUpdate
from models.certificates import CertificateCreate, CertificateUpdate
from models.skills import SkillCreate, SkillUpdate

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY env vars")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

app = FastAPI(title="Profile Service")

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail, "code": exc.status_code})

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": "Internal server error", "code": 500})

@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "service": "profile"}

@app.get("/profile/me/bundle", tags=["profile"])
def get_profile_bundle(x_user_id: str = Header(default=None, alias="X-User-Id")):
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id")

    profile_res = supabase.table("profiles").select("*").eq("id", x_user_id).maybe_single().execute()
    experiences_res = supabase.table("experiences").select("*").eq("candidate_id", x_user_id).execute()
    education_res = supabase.table("education").select("*").eq("candidate_id", x_user_id).execute()
    certificates_res = supabase.table("certificates").select("*").eq("candidate_id", x_user_id).execute()
    skills_res = supabase.table("skills").select("*").eq("candidate_id", x_user_id).execute()

    return {
        "profile": profile_res.data or {},
        "experiences": experiences_res.data or [],
        "education": education_res.data or [],
        "certificates": certificates_res.data or [],
        "skills": skills_res.data or [],
    }


@app.get("/profile/me", tags=["profile"])
def get_me(x_user_id: str = Header(default=None, alias="X-User-Id")):
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id")

    res = supabase.table("profiles").select("*").eq("id", x_user_id).maybe_single().execute()

    if not res.data:
        raise HTTPException(status_code=404, detail="Profile not found")

    return res.data

@app.patch("/profile/me", tags=["profile"])
def update_me(payload: ProfileUpdate, x_user_id: str = Header(default=None, alias="X-User-Id")):
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id")

    update_data = {k: v for k, v in jsonable_encoder(payload).items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided")

    res = supabase.table("profiles").update(update_data).eq("id", x_user_id).execute()
    return {"updated": True, "data": res.data}

@app.get("/profile/me/experiences", tags=["experience"])
def list_my_experiences(
    x_user_id: str = Header(default=None, alias="X-User-Id"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id")

    res = supabase.table("experiences").select("*").eq("candidate_id", x_user_id).range(offset, offset + limit - 1).execute()
    return {"items": res.data or [], "limit": limit, "offset": offset}

@app.post("/profile/me/experiences", tags=["experience"])
def add_experience(payload: ExperienceCreate, x_user_id: str = Header(default=None, alias="X-User-Id")):
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id")

    data = jsonable_encoder(payload)
    data["candidate_id"] = x_user_id

    res = supabase.table("experiences").insert(data).execute()
    return {"created": True, "data": res.data}

@app.put("/profile/me/experiences/{exp_id}", tags=["experience"])
def update_experience(exp_id: str, payload: ExperienceUpdate, x_user_id: str = Header(default=None, alias="X-User-Id")):
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id")

    update_data = {k: v for k, v in jsonable_encoder(payload).items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided")

    res = supabase.table("experiences") \
        .update(update_data) \
        .eq("exp_id", exp_id) \
        .eq("candidate_id", x_user_id) \
        .execute()

    if not res.data:
        raise HTTPException(status_code=404, detail="Experience not found")
    return {"updated": True, "data": res.data}

@app.delete("/profile/me/experiences/{exp_id}", tags=["experience"])
def delete_experience(exp_id: str, x_user_id: str = Header(default=None, alias="X-User-Id")):
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id")

    res = supabase.table("experiences") \
        .delete() \
        .eq("exp_id", exp_id) \
        .eq("candidate_id", x_user_id) \
        .execute()

    if not res.data:
        raise HTTPException(status_code=404, detail="Experience not found")
    return {"deleted": True}

@app.get("/profile/me/education", tags=["education"])
def list_my_education(
    x_user_id: str = Header(default=None, alias="X-User-Id"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id")

    res = supabase.table("education").select("*").eq("candidate_id", x_user_id).range(offset, offset + limit - 1).execute()
    return {"items": res.data or [], "limit": limit, "offset": offset}


@app.post("/profile/me/education", tags=["education"])
def add_education(payload: EducationCreate, x_user_id: str = Header(default=None, alias="X-User-Id")):
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id")

    data = jsonable_encoder(payload)
    data["candidate_id"] = x_user_id

    res = supabase.table("education").insert(data).execute()
    return {"created": True, "data": res.data}


@app.put("/profile/me/education/{edu_id}", tags=["education"])
def update_education(edu_id: str, payload: EducationUpdate, x_user_id: str = Header(default=None, alias="X-User-Id")):
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id")

    update_data = {k: v for k, v in jsonable_encoder(payload).items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided")

    res = (
        supabase.table("education")
        .update(update_data)
        .eq("edu_id", edu_id)
        .eq("candidate_id", x_user_id)
        .execute()
    )

    if not res.data:
        raise HTTPException(status_code=404, detail="Education record not found")
    return {"updated": True, "data": res.data}


@app.delete("/profile/me/education/{edu_id}", tags=["education"])
def delete_education(edu_id: str, x_user_id: str = Header(default=None, alias="X-User-Id")):
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id")

    res = (
        supabase.table("education")
        .delete()
        .eq("edu_id", edu_id)
        .eq("candidate_id", x_user_id)
        .execute()
    )

    if not res.data:
        raise HTTPException(status_code=404, detail="Education record not found")
    return {"deleted": True}

@app.get("/profile/me/certificates", tags=["certificates"])
def list_my_certificates(
    x_user_id: str = Header(default=None, alias="X-User-Id"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id")

    res = supabase.table("certificates").select("*").eq("candidate_id", x_user_id).range(offset, offset + limit - 1).execute()
    return {"items": res.data or [], "limit": limit, "offset": offset}


@app.post("/profile/me/certificates", tags=["certificates"])
def add_certificate(payload: CertificateCreate, x_user_id: str = Header(default=None, alias="X-User-Id")):
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id")

    data = jsonable_encoder(payload)

    # certificate_id is the PRIMARY KEY — auto-generate if not provided
    if not data.get("certificate_id"):
        data["certificate_id"] = f"manual-{_uuid.uuid4().hex[:12]}"

    # Resolve issuer_id: supported issuers have it set;
    # custom issuers fall back to 'custom' sentinel row
    if not data.get("issuer_id"):
        data["issuer_id"] = _CUSTOM_ISSUER_SLUG

    # Manual saves default to NOT_FOUND (= Unverified in the UI)
    if "status" not in data or not data["status"]:
        data["status"] = "NOT_FOUND"

    # Preserve the real custom issuer name instead of overwriting it with `custom`
    if data["issuer_id"] == _CUSTOM_ISSUER_SLUG:
        issuer_name = (data.get("issuer") or "").strip()
        if issuer_name:
            data["issuer"] = issuer_name
            if not data.get("verification_details"):
                data["verification_details"] = f"Manual issuer: {issuer_name}"
        else:
            data.pop("issuer", None)
        data.pop("credential_url", None)
        data.pop("supported_cert_id", None)
        data.pop("issuer", None)

    else:
        data.pop("issuer", None)

    # Drop fields not in the certificates table
    data.pop("supported_cert_id", None)

    data["candidate_id"] = x_user_id

    try:
        res = supabase.table("certificates").insert(data).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Insert failed: {str(e)[:200]}")

    return {"created": True, "data": res.data}


@app.put("/profile/me/certificates/{cert_id}", tags=["certificates"])
def update_certificate(
    cert_id: str,
    payload: CertificateUpdate,
    x_user_id: str = Header(default=None, alias="X-User-Id")
):
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id")

    update_data = {k: v for k, v in jsonable_encoder(payload).items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided")

    current_res = (
        supabase.table("certificates")
        .select("*")
        .eq("certificate_id", cert_id)
        .eq("candidate_id", x_user_id)
        .maybe_single()
        .execute()
    )

    current = current_res.data
    if not current:
        raise HTTPException(status_code=404, detail="Certificate not found")

    is_custom = (current.get("issuer_id") or "").strip().lower() == _CUSTOM_ISSUER_SLUG

    # Supported issuers keep their stricter behavior
    if not is_custom:
        update_data.pop("issuer", None)
        update_data.pop("issuer_id", None)
        update_data.pop("certificate_id", None)
    else:
        if "issuer" in update_data:
            issuer_name = (update_data.get("issuer") or "").strip()
            if issuer_name:
                update_data["issuer"] = issuer_name
                if not update_data.get("verification_details"):
                    update_data["verification_details"] = f"Manual issuer: {issuer_name}"
            else:
                update_data.pop("issuer", None)

    res = (
        supabase.table("certificates")
        .update(update_data)
        .eq("certificate_id", cert_id)
        .eq("candidate_id", x_user_id)
        .execute()
    )

    if not res.data:
        raise HTTPException(status_code=404, detail="Certificate not found")

    return {"updated": True, "data": res.data}


@app.delete("/profile/me/certificates/{cert_id}", tags=["certificates"])
def delete_certificate(cert_id: str, x_user_id: str = Header(default=None, alias="X-User-Id")):
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id")

    res = (
        supabase.table("certificates")
        .delete()
        .eq("certificate_id", cert_id)
        .eq("candidate_id", x_user_id)
        .execute()
    )

    if not res.data:
        raise HTTPException(status_code=404, detail="Certificate not found")
    return {"deleted": True}

@app.get("/profile/skills-catalog", tags=["skills"])
def list_standard_skills():
    """Return the standardized skills catalog with IDs."""
    res = supabase.table("standard_skills").select("*").execute()
    return {"items": res.data or []}

@app.get("/profile/me/skills", tags=["skills"])
def list_my_skills(
    x_user_id: str = Header(default=None, alias="X-User-Id"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id")

    res = supabase.table("skills").select("*").eq("candidate_id", x_user_id).range(offset, offset + limit - 1).execute()
    return {"items": res.data or [], "limit": limit, "offset": offset}


@app.post("/profile/me/skills", tags=["skills"])
def add_skill(payload: SkillCreate, x_user_id: str = Header(default=None, alias="X-User-Id")):
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id")

    data = jsonable_encoder(payload)

    # Enforce your DB check rule in the API layer too (clear error message)
    has_std = data.get("skill_id") is not None
    has_custom = data.get("custom_skill_name") is not None
    if has_std == has_custom:  # both true OR both false
        raise HTTPException(status_code=400, detail="Provide exactly one of: skill_id OR custom_skill_name")

    data["candidate_id"] = x_user_id

    try:
        res = supabase.table("skills").insert(data).execute()
        return {"created": True, "data": res.data}
    except Exception as e:
        # unique(candidate_id, skill_id) will throw if duplicate
        raise HTTPException(status_code=400, detail=f"Failed to add skill: {str(e)}")


@app.put("/profile/me/skills/{row_id}", tags=["skills"])
def update_skill(row_id: str, payload: SkillUpdate, x_user_id: str = Header(default=None, alias="X-User-Id")):
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id")

    update_data = {k: v for k, v in jsonable_encoder(payload).items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided")

    # Do not allow user to set is_verified here (system-only)

    res = (
        supabase.table("skills")
        .update(update_data)
        .eq("id", row_id)
        .eq("candidate_id", x_user_id)
        .execute()
    )

    if not res.data:
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"updated": True, "data": res.data}


@app.delete("/profile/me/skills/{row_id}", tags=["skills"])
def delete_skill(row_id: str, x_user_id: str = Header(default=None, alias="X-User-Id")):
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id")

    res = (
        supabase.table("skills")
        .delete()
        .eq("id", row_id)
        .eq("candidate_id", x_user_id)
        .execute()
    )

    if not res.data:
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"deleted": True}