from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, Certificate, Issuer, VerificationStatus
from schemas import CertificateRequest, CertificateResponse
from automation.verify_edx import verify_edx
from automation.verify_comptia import verify_comptia
from automation.verify_eccouncil import verify_eccouncil
from automation.verify_coursera import verify_coursera
from automation.verify_udemy import verify_udemy
from uuid import UUID

router = APIRouter(prefix="/certificates", tags=["Certificates"])

VERIFIERS = {
    "edx":       verify_edx,
    "comptia":   verify_comptia,
    "eccouncil": verify_eccouncil,
    "coursera":  verify_coursera,
    "udemy":     verify_udemy,
}


@router.post("", response_model=CertificateResponse, status_code=201)
def submit_certificate(body: CertificateRequest, db: Session = Depends(get_db)):

    if db.query(Certificate).filter(Certificate.certificate_id == body.certificate_id).first():
        raise HTTPException(status_code=409, detail="Certificate already exists.")

    issuer = db.query(Issuer).filter(Issuer.issuer_id == body.issuer_id.lower()).first()
    if not issuer:
        raise HTTPException(status_code=400, detail=f"Issuer '{body.issuer_id}' not found in trusted registry.")

    cert = Certificate(
        certificate_id   = body.certificate_id,
        candidate_id     = body.candidate_id,
        issuer_id        = body.issuer_id.lower(),
        certificate_name = body.certificate_name,
        issue_date       = body.issue_date,
        expiration_date  = body.expiration_date,
        first_name       = body.first_name,
        last_name        = body.last_name,
    )

    verifier = VERIFIERS.get(issuer.issuer_id)
    if not verifier:
        raise HTTPException(status_code=400, detail=f"No verifier available for '{body.issuer_id}'.")
    result = verifier(cert)

    cert.status               = result["status"]
    cert.verification_details = result["message"]

    if result.get("data"):
        scraped = result["data"]
        if not cert.certificate_name:  cert.certificate_name = scraped.get("certificate_name", "Unknown")
        if not cert.first_name:        cert.first_name       = scraped.get("first_name")
        if not cert.last_name:         cert.last_name        = scraped.get("last_name")
        if not cert.issue_date:        cert.issue_date       = scraped.get("valid_from")
        if not cert.expiration_date:   cert.expiration_date  = scraped.get("valid_to")
    else:
        if not cert.certificate_name:
            cert.certificate_name = "Unknown"

    db.add(cert)
    db.commit()
    db.refresh(cert)
    return cert


@router.get("/issuers", response_model=list[dict])
def list_issuers(db: Session = Depends(get_db)):
    return [{"issuer_id": i.issuer_id, "issuer_name": i.issuer_name} for i in db.query(Issuer).all()]


@router.get("/candidate/{candidate_id}", response_model=list[CertificateResponse])
def get_candidate_certificates(candidate_id: UUID, db: Session = Depends(get_db)):
    return db.query(Certificate).filter(Certificate.candidate_id == candidate_id).all()


@router.get("/{certificate_id}", response_model=CertificateResponse)
def get_certificate(certificate_id: str, db: Session = Depends(get_db)):
    cert = db.query(Certificate).filter(Certificate.certificate_id == certificate_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found.")
    return cert