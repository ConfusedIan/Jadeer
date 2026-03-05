from typing import Any
import httpx

from config import PROFILE_SERVICE_URL, HTTP_TIMEOUT_SECONDS


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
    Fetch the profile bundle using the gateway contract:
    - We pass X-User-Id (injected by the API Gateway).
    - Profile service scopes all queries with candidate_id = X-User-Id.
    """
    bundle = {
        "profile": {},
        "experiences": [],
        "education": [],
        "certificates": [],
        "skills": [],
    }

    async def fetch_json(client: httpx.AsyncClient, path: str) -> Any:
        url = f"{PROFILE_SERVICE_URL}{path}"
        r = await client.get(url, headers={"X-User-Id": user_id})
        r.raise_for_status()
        return r.json()

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
        # Profile
        try:
            data = await fetch_json(client, "/profile/me")
            bundle["profile"] = _as_dict(data)
        except Exception:
            pass

        # Lists
        for key, path in [
            ("experiences", "/profile/me/experiences"),
            ("education", "/profile/me/education"),
            ("certificates", "/profile/me/certificates"),
            ("skills", "/profile/me/skills"),
        ]:
            try:
                data = await fetch_json(client, path)
                bundle[key] = _as_list(data)
            except Exception:
                pass

    return bundle