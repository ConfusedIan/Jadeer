import os

SERVICES = {
    "profile": os.getenv("PROFILE_SERVICE_URL", "http://127.0.0.1:5002"),
    "assessment": os.getenv("ASSESSMENT_SERVICE_URL", "http://127.0.0.1:5003"),
    "cv": os.getenv("CV_SERVICE_URL", "http://127.0.0.1:5004"),
    "recommendation": os.getenv("RECOMMENDATION_SERVICE_URL", "http://127.0.0.1:5005"),
    "ranking": os.getenv("RANKING_SERVICE_URL", "http://127.0.0.1:5007"),
    "certificates": os.getenv("CERT_SERVICE_URL", "http://127.0.0.1:5006"),
}
