from fastapi import FastAPI
from database import Base, engine, SessionLocal, Issuer, check_connection
from routers import certificates

app = FastAPI(
    title="Certification Verification Service",  version="3.0.0",)

app.include_router(certificates.router)


TRUSTED_ISSUERS = [
    {"issuer_id": "eccouncil", "issuer_name": "EC-Council", "verification_url": "https://aspen.eccouncil.org/Verify"},
    {"issuer_id": "comptia",   "issuer_name": "CompTIA", "verification_url": "https://cp.certmetrics.com/CompTIA/en/public/verify/credential"},
    {"issuer_id": "edx",       "issuer_name": "edX", "verification_url": "https://verify.edx.org/cert/"},
    {"issuer_id": "coursera",    "issuer_name": "Coursera", "verification_url": "https://www.coursera.org/verify/"},
    {"issuer_id": "udemy",       "issuer_name": "Udemy","verification_url": "https://www.udemy.com/certificate/"},
]


@app.on_event("startup")
def on_startup():
    check_connection()
    print(" Database connected.")

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        for row in TRUSTED_ISSUERS:
            if not db.query(Issuer).filter(Issuer.issuer_id == row["issuer_id"]).first():
                db.add(Issuer(**row))
        db.commit()
        print("Issuers ready.")
    finally:
        db.close()


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "service": "cert-verification"}
