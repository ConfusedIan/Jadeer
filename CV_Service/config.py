import os
from dotenv import load_dotenv

load_dotenv()

PROFILE_SERVICE_URL = os.getenv("PROFILE_SERVICE_URL", "http://127.0.0.1:5002").rstrip("/")
PORT = int(os.getenv("PORT", "5004"))
HTTP_TIMEOUT_SECONDS = float(os.getenv("HTTP_TIMEOUT_SECONDS", "10"))

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")