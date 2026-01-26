import os

SERVICES = {
    "AUTH": os.getenv("AUTH_SERVICE_URL", "http://127.0.0.1:5001"),
    "ASSESSMENT": os.getenv("ASSESSMENT_SERVICE_URL", "http://127.0.0.1:5002"),
    "CV": os.getenv("CV_SERVICE_URL", "http://127.0.0.1:5003"),
    "RECOMMENDATION": os.getenv("RECOMMENDATION_SERVICE_URL", "http://127.0.0.1:5004"),
    "RANKING": os.getenv("RANKING_SERVICE_URL", "http://127.0.0.1:5005"),
}
