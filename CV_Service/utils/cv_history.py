import logging
import uuid

from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

logger = logging.getLogger(__name__)

_CV_BUCKET = "cv-pdfs"


def _client():
    from supabase import create_client  # type: ignore
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


async def save_cv(user_id: str, pdf_bytes: bytes, cv_name: str | None, settings: dict) -> str:
    """
    Upload PDF to Supabase Storage and insert a metadata row.
    Returns the cv_id (UUID string). Raises on failure.
    """
    cv_id = str(uuid.uuid4())
    storage_path = f"{user_id}/{cv_id}.pdf"

    sb = _client()

    sb.storage.from_(_CV_BUCKET).upload(
        path=storage_path,
        file=pdf_bytes,
        file_options={"content-type": "application/pdf"},
    )

    sb.table("cv_history").insert({
        "id": cv_id,
        "user_id": user_id,
        "cv_name": cv_name or "My CV",
        "settings": settings,
    }).execute()

    return cv_id


async def list_cvs(user_id: str) -> list[dict]:
    """Return cv_history rows for this user, newest first."""
    sb = _client()
    result = (
        sb.table("cv_history")
        .select("id, cv_name, created_at, settings")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []


async def get_cv(user_id: str, cv_id: str) -> bytes:
    """Download and return PDF bytes from Supabase Storage. Raises on failure."""
    storage_path = f"{user_id}/{cv_id}.pdf"
    sb = _client()
    data = sb.storage.from_(_CV_BUCKET).download(storage_path)
    return data
