import os
from dotenv import load_dotenv

load_dotenv()

PORT                    = int(os.getenv("PORT", "5007"))
SUPABASE_URL            = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
