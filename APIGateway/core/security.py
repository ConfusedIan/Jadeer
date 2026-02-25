import os, time, requests
from fastapi import Request
from core.exceptions import UnauthorizedError
from jose import jwt, JWTError
from config import SUPABASE_JWT_SECRET, SUPABASE_JWT_ALG

SUPABASE_PROJECT_REF = os.getenv("SUPABASE_PROJECT_REF", "gnwryggrdrszdelonuei")
JWKS_URL = f"https://gnwryggrdrszdelonuei.supabase.co/auth/v1/.well-known/jwks.json"

_cache = {"keys": None, "ts": 0}
TTL = 3600

def _jwks():
    now = time.time()
    if _cache["keys"] and (now - _cache["ts"] < TTL):
        return _cache["keys"]
    r = requests.get(JWKS_URL, timeout=10)
    r.raise_for_status()
    _cache["keys"] = r.json()["keys"]
    _cache["ts"] = now
    return _cache["keys"]

def get_bearer_token(request):
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise UnauthorizedError("Missing Bearer token")
    return auth.split(" ", 1)[1].strip()

def verify_supabase_jwt(token: str) -> dict:
    try:
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        if not kid:
            raise UnauthorizedError("Missing kid in token header")

        key = next((k for k in _jwks() if k.get("kid") == kid), None)
        if not key:
            raise UnauthorizedError("No matching public key (kid)")

        return jwt.decode(
            token,
            key,
            algorithms=["ES256"],
            audience="authenticated"
        )
    except requests.RequestException:
        raise UnauthorizedError("Failed to fetch Supabase JWKS")
    except JWTError:
        raise UnauthorizedError("Invalid or expired token")
