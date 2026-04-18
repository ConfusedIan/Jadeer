from fastapi import APIRouter, Depends, HTTPException, Header
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
    "edx": verify_edx,
    "comptia": verify_comptia,
    "eccouncil": verify_eccouncil,
    "coursera": verify_coursera,
    "udemy": verify_udemy,
}

ISSUER_FIELDS = {
    "edx": {
        "required": ["certificate_id", "expiration_date"],
        "optional": ["certificate_name", "issue_date", "first_name", "last_name"],
        "hint": "Enter your edX certificate ID. Expiration Date is also required in the form.",
    },
    "coursera": {
        "required": ["certificate_id", "expiration_date"],
        "optional": ["certificate_name", "issue_date", "first_name", "last_name"],
        "hint": "Enter your Coursera verification code. Expiration Date is also required in the form.",
    },
    "udemy": {
        "required": ["certificate_id", "expiration_date"],
        "optional": ["certificate_name", "issue_date", "first_name", "last_name"],
        "hint": "Enter your Udemy certificate number. Expiration Date is also required in the form.",
    },
    "comptia": {
        "required": ["certificate_id", "expiration_date"],
        "optional": ["certificate_name", "issue_date", "first_name", "last_name"],
        "hint": "Enter your CompTIA verification code. Expiration Date is required.",
    },
    "eccouncil": {
        "required": ["certificate_id", "first_name", "last_name", "expiration_date"],
        "optional": ["certificate_name", "issue_date"],
        "hint": "EC-Council requires full name exactly as shown on the certificate. Expiration Date is also required.",
    },
}

DEFAULT_ISSUER_FIELDS = {
    "required": ["certificate_id", "expiration_date"],
    "optional": ["certificate_name", "issue_date", "first_name", "last_name"],
    "hint": "Unsupported issuers can still be added and will be saved as Unverified.",
}


def _normalize_issuer_id(issuer_id: str) -> str:
    return (issuer_id or "").strip().lower()


def _is_present(value) -> bool:
    if value is None:
        return False
    if isinstance(value, str) and not value.strip():
        return False
    return True


def _get_issuer_fields(issuer_id: str) -> dict:
    return ISSUER_FIELDS.get(_normalize_issuer_id(issuer_id), DEFAULT_ISSUER_FIELDS)


def _missing_required_fields(body: CertificateRequest, issuer_id: str) -> list[str]:
    fields = _get_issuer_fields(issuer_id)
    missing = []

    for field in fields["required"]:
        if not _is_present(getattr(body, field, None)):
            missing.append(field)

    return missing


def _unverified_status():
    """
    Best-effort fallback for different enum styles.
    If your enum uses another exact value, replace the return value accordingly.
    """
    enum_members = getattr(VerificationStatus, "__members__", {})
    if "UNVERIFIED" in enum_members:
        return enum_members["UNVERIFIED"]
    if "unverified" in enum_members:
        return enum_members["unverified"]
    return "Unverified"


@router.post("", response_model=CertificateResponse, status_code=201)
def submit_certificate(
    body: CertificateRequest,
    db: Session = Depends(get_db),
    x_user_id: str = Header(default=None, alias="X-User-Id"),
):
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id")

    normalized_issuer_id = _normalize_issuer_id(body.issuer_id)

    if db.query(Certificate).filter(Certificate.certificate_id == body.certificate_id).first():
        raise HTTPException(status_code=409, detail="Certificate already exists.")

    # Dynamic validation based on issuer
    missing_fields = _missing_required_fields(body, normalized_issuer_id)
    if missing_fields:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Missing required fields for this issuer.",
                "issuer_id": normalized_issuer_id,
                "missing_fields": missing_fields,
            },
        )

    issuer = db.query(Issuer).filter(Issuer.issuer_id == normalized_issuer_id).first()

    # Allow unsupported issuers to still be added as Unverified
    # If issuer doesn't exist, create a placeholder issuer record
    # so the certificate can still be stored.
    if not issuer:
        issuer = Issuer(
            issuer_id=normalized_issuer_id,
            issuer_name=body.issuer_id.strip() if isinstance(body.issuer_id, str) else normalized_issuer_id,
            verification_url="",   # required by schema; unsupported issuers have no URL
        )
        db.add(issuer)
        db.flush()

    cert = Certificate(
        certificate_id=body.certificate_id,
        candidate_id=body.candidate_id,
        issuer_id=normalized_issuer_id,
        certificate_name=body.certificate_name,
        issue_date=body.issue_date,
        expiration_date=body.expiration_date,
        first_name=body.first_name,
        last_name=body.last_name,
    )

    verifier = VERIFIERS.get(normalized_issuer_id)

    if verifier:
        try:
            result = verifier(cert)
        except Exception as e:
            result = {
                "status": _unverified_status(),
                "message": f"Automatic verification failed: {str(e)}",
                "data": None,
            }
    else:
        result = {
            "status": _unverified_status(),
            "message": "Issuer is not supported for automatic verification yet. Certificate was saved as Unverified.",
            "data": None,
        }

    cert.status = result.get("status", _unverified_status())
    cert.verification_details = result.get("message", "")

    if result.get("data"):
        scraped = result["data"]

        if not cert.certificate_name:
            cert.certificate_name = scraped.get("certificate_name", "Unknown")

        if not cert.first_name:
            cert.first_name = scraped.get("first_name")

        if not cert.last_name:
            cert.last_name = scraped.get("last_name")

        if not cert.issue_date:
            cert.issue_date = scraped.get("valid_from")

        if not cert.expiration_date:
            cert.expiration_date = scraped.get("valid_to")
    else:
        if not cert.certificate_name:
            cert.certificate_name = "Unknown"

    db.add(cert)
    db.commit()
    db.refresh(cert)
    return cert


@router.get("/issuers", response_model=list[dict])
def list_issuers(
    db: Session = Depends(get_db),
    x_user_id: str = Header(default=None, alias="X-User-Id"),
):
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id")

    results = []
    for i in db.query(Issuer).all():
        fields = _get_issuer_fields(i.issuer_id)
        results.append(
            {
                "issuer_id": i.issuer_id,
                "issuer_name": i.issuer_name,
                "required_fields": fields["required"],
                "optional_fields": fields["optional"],
                "hint": fields.get("hint", ""),
            }
        )

    return results


@router.get("/candidate/{candidate_id}", response_model=list[CertificateResponse])
def get_candidate_certificates(
    candidate_id: UUID,
    db: Session = Depends(get_db),
    x_user_id: str = Header(default=None, alias="X-User-Id"),
):
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id")
    return db.query(Certificate).filter(Certificate.candidate_id == candidate_id).all()


@router.get("/{certificate_id}", response_model=CertificateResponse)
def get_certificate(
    certificate_id: str,
    db: Session = Depends(get_db),
    x_user_id: str = Header(default=None, alias="X-User-Id"),
):
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id")
    cert = db.query(Certificate).filter(Certificate.certificate_id == certificate_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found.")
    return cert