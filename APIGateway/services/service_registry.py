import os

SERVICES = {
    "profile": os.getenv("PROFILE_SERVICE_URL", "http://127.0.0.1:5002"),
    "ASSESSMENT": os.getenv("ASSESSMENT_SERVICE_URL", "http://127.0.0.1:5003"),
    "cv": os.getenv("CV_SERVICE_URL", "http://127.0.0.1:5004"),
    "RECOMMENDATION": os.getenv("RECOMMENDATION_SERVICE_URL", "http://127.0.0.1:5005"),
    "RANKING": os.getenv("RANKING_SERVICE_URL", "http://127.0.0.1:5005"),
}
