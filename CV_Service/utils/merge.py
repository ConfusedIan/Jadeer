def dummy_bundle() -> dict:
    return {
        "profile": {
            "full_name": "John Doe",
            "phone": "+966 5X XXX XXXX",
            "bio": "Backend developer focused on microservices, FastAPI, and PostgreSQL. Builds secure APIs with JWT.",
            "linkedin_url": "linkedin.com/in/johndoe",
            "location": "Riyadh, Saudi Arabia",
            "languages": ["English"],
        },
        "experiences": [
            {
                "job_title": "Backend Intern",
                "company": "Example Co",
                "start_date": "2025-06-01",
                "end_date": "2025-09-01",
                "description": "Built FastAPI endpoints, integrated PostgreSQL queries, and supported gateway routing and auth flows.",
            }
        ],
        "education": [
            {
                "institution": "Example University",
                "degree": "BSc Computer Science",
                "field_of_study": "Software Engineering",
                "start_date": "2021-01-01",
                "end_date": "2025-01-01",
            }
        ],
        "certificates": [
            {
                "certificate_name": "AWS Cloud Practitioner",
                "issuer": "Amazon",
                "issue_date": "2024-01-01",
                "credential_url": "",
                "is_verified": True,
            }
        ],
        "skills": [
            {"custom_skill_name": "Python", "category": "Technical", "score": 90},
            {"custom_skill_name": "FastAPI", "category": "Technical", "score": 85},
            {"custom_skill_name": "PostgreSQL", "category": "Technical", "score": 80},
        ],
    }


def merge_real_with_dummy(real: dict, dummy: dict) -> dict:
    out = {"profile": {}, "experiences": [], "education": [], "certificates": [], "skills": []}

    real_profile = real.get("profile") or {}
    out["profile"] = dummy["profile"] | real_profile

    for k in ("experiences", "education", "certificates", "skills"):
        rv = real.get(k)
        out[k] = rv if rv else dummy[k]

    return out