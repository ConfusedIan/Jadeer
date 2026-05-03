import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import APIRouter, HTTPException
import re
from pydantic import BaseModel, field_validator

from config import (
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, CONTACT_TO_EMAIL
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/contact", tags=["contact"])


_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

class ContactForm(BaseModel):
    email: str
    title: str
    message: str

    @field_validator("email")
    @classmethod
    def valid_email(cls, v: str) -> str:
        v = v.strip()
        if not _EMAIL_RE.match(v):
            raise ValueError("Invalid email address")
        return v

    @field_validator("title", "message")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field must not be empty")
        return v.strip()


@router.post("")
def send_contact(form: ContactForm):
    if not SMTP_USER or not SMTP_PASS:
        logger.error("SMTP credentials not configured")
        raise HTTPException(status_code=503, detail="Email service not configured")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Jadeer: {form.title}"
    msg["From"] = SMTP_USER
    msg["To"] = CONTACT_TO_EMAIL
    msg["Reply-To"] = form.email

    body = (
        f"From: {form.email}\n\n"
        f"{form.message}"
    )
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, CONTACT_TO_EMAIL, msg.as_string())
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP authentication failed")
        raise HTTPException(status_code=503, detail="Email service authentication failed")
    except Exception as exc:
        logger.error("Failed to send contact email: %s", exc)
        raise HTTPException(status_code=503, detail="Failed to send message. Please try again.")

    return {"ok": True}
