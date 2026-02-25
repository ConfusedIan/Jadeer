import os
from fastapi import FastAPI, Header, HTTPException
from supabase import create_client, Client

from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import date
from fastapi.encoders import jsonable_encoder

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY env vars")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

app = FastAPI(title="Profile Service")

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    linkedin_url: Optional[str] = None
    location: Optional[str] = None
    languages: Optional[List[str]] = None

class ExperienceCreate(BaseModel):
    job_title: str
    company: str
    start_date: date
    end_date: Optional[date] = None
    description: Optional[str] = None

class ExperienceUpdate(BaseModel):
    job_title: Optional[str] = None
    company: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = None

@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "service": "profile"}

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
def list_my_experiences(x_user_id: str = Header(default=None, alias="X-User-Id")):
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id")

    res = supabase.table("experiences").select("*").eq("candidate_id", x_user_id).execute()
    return {"items": res.data or []}

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