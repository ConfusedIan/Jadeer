from jose import jwt, JWTError
from fastapi import Request
from core.exceptions import UnauthorizedError
from config import JWT_SECRET_KEY, JWT_ALGORITHM

def get_bearer_token(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise UnauthorizedError("Missing Bearer token")
    return auth.replace("Bearer ", "", 1).strip()

def decode_jwt(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise UnauthorizedError("Invalid or expired token")
