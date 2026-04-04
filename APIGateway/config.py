import os
from dotenv import load_dotenv

load_dotenv()

APP_NAME = "API Gateway"
HOST = os.getenv("GATEWAY_HOST", "0.0.0.0")
PORT = int(os.getenv("GATEWAY_PORT", "8000"))

# JWT
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")
SUPABASE_JWT_ALG = os.getenv("SUPABASE_JWT_ALG", "HS256")

# Forwarding
REQUEST_TIMEOUT_SECONDS = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "10"))

# CORS — comma-separated list of allowed origins, e.g. "http://localhost:3000,https://app.example.com"
_cors_raw = os.getenv("CORS_ORIGINS", "http://localhost:3000")
CORS_ORIGINS = [o.strip() for o in _cors_raw.split(",") if o.strip()]
