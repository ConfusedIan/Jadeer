import logging
from typing import Any
import httpx

from config import PROFILE_SERVICE_URL, HTTP_TIMEOUT_SECONDS

logger = logging.getLogger(__name__)


def _as_list(payload: Any) -> list:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for k in ("items", "data", "result"):
            v = payload.get(k)
            if isinstance(v, list):
                return v
    return []


def _as_dict(payload: Any) -> dict:
    if isinstance(payload, dict):
        v = payload.get("data")
        if isinstance(v, dict):
            return v
        return payload
    return {}


async def get_profile_bundle(user_id: str) -> dict:
    """
    Fetch the profile bundle via the single /profile/me/bundle endpoint.
    Falls back to individual calls if the bundle endpoint fails.
    """
    headers = {"X-User-Id": user_id}

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
        try:
            r = await client.get(f"{PROFILE_SERVICE_URL}/profile/me/bundle", headers=headers)
            r.raise_for_status()
            data = r.json()
            return {
                "profile": _as_dict(data.get("profile", {})),
                "experiences": _as_list(data.get("experiences", [])),
                "education": _as_list(data.get("education", [])),
                "certificates": _as_list(data.get("certificates", [])),
                "skills": _as_list(data.get("skills", [])),
            }
        except Exception as exc:
            logger.warning("Bundle endpoint failed for user %s (%s), falling back to individual calls", user_id, exc)

        # Fallback: individual calls
        bundle: dict[str, Any] = {
            "profile": {},
            "experiences": [],
            "education": [],
            "certificates": [],
            "skills": [],
        }

        async def fetch_json(path: str) -> Any:
            r = await client.get(f"{PROFILE_SERVICE_URL}{path}", headers=headers)
            r.raise_for_status()
            return r.json()

        try:
            bundle["profile"] = _as_dict(await fetch_json("/profile/me"))
        except Exception as exc:
            logger.warning("Failed to fetch /profile/me for user %s: %s", user_id, exc)

        for key, path in [
            ("experiences", "/profile/me/experiences"),
            ("education", "/profile/me/education"),
            ("certificates", "/profile/me/certificates"),
            ("skills", "/profile/me/skills"),
        ]:
            try:
                bundle[key] = _as_list(await fetch_json(path))
            except Exception as exc:
                logger.warning("Failed to fetch %s for user %s: %s", path, user_id, exc)

        return bundle