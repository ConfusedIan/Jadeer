import logging
import re
import uuid

from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

logger = logging.getLogger(__name__)

_CV_BUCKET = "cv-pdfs"
_SIGNED_URL_EXPIRY = 60 * 60 * 24 * 7  # 7 days


def _client():
    from supabase import create_client  # type: ignore
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")[:40]


def _unslugify(slug: str) -> str:
    slug = re.sub(r"-[a-f0-9]{8}$", "", slug)
    return slug.replace("-", " ").title()


async def save_cv(user_id: str, pdf_bytes: bytes, cv_name: str | None, settings: dict) -> str:
    """
    Upload PDF to Supabase Storage.
    Returns the file stem (used as cv_id for downloads). Raises on failure.
    """
    sb = _client()

    if not cv_name:
        existing = sb.storage.from_(_CV_BUCKET).list(path=user_id) or []
        n = len([f for f in existing if f.get("name", "").endswith(".pdf")]) + 1
        cv_name = f"CV{n}"

    short_id = str(uuid.uuid4()).replace("-", "")[:8]
    slug = _slugify(cv_name)
    file_stem = f"{slug}-{short_id}"
    storage_path = f"{user_id}/{file_stem}.pdf"

    sb.storage.from_(_CV_BUCKET).upload(
        path=storage_path,
        file=pdf_bytes,
        file_options={"content-type": "application/pdf"},
    )

    return file_stem


async def list_cvs(user_id: str) -> list[dict]:
    """List PDFs for this user from Supabase Storage, newest first."""
    sb = _client()
    files = sb.storage.from_(_CV_BUCKET).list(path=user_id) or []
    pdf_files = [f for f in files if f.get("name", "").endswith(".pdf")]
    pdf_files.sort(key=lambda f: f.get("created_at") or "", reverse=True)
    return [
        {
            "id": f["name"].replace(".pdf", ""),
            "cv_name": _unslugify(f["name"].replace(".pdf", "")),
            "created_at": f.get("created_at"),
        }
        for f in pdf_files
    ]


async def delete_cv(user_id: str, cv_id: str) -> None:
    """Delete a PDF from Supabase Storage. Raises on failure."""
    sb = _client()
    storage_path = f"{user_id}/{cv_id}.pdf"
    sb.storage.from_(_CV_BUCKET).remove([storage_path])


async def get_cv_url(user_id: str, cv_id: str) -> str:
    """Return a signed download URL. Raises on failure."""
    sb = _client()
    storage_path = f"{user_id}/{cv_id}.pdf"
    signed = sb.storage.from_(_CV_BUCKET).create_signed_url(storage_path, _SIGNED_URL_EXPIRY)
    url = signed.get("signedURL") or signed.get("signedUrl")
    if not url:
        raise FileNotFoundError(f"CV {cv_id} not found")
    return url
