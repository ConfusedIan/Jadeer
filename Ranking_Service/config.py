import os
from dotenv import load_dotenv

load_dotenv()

PORT = int(os.getenv("PORT", "5007"))

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# Max number of ranked candidates to return in a single response.
MAX_RESULTS = int(os.getenv("RANKING_MAX_RESULTS", "100"))
