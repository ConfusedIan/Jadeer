import os
import enum
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import (create_engine, text, Column, String, Text, DateTime, Enum, ForeignKey)
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class VerificationStatus(str, enum.Enum):
    VERIFIED   = "VERIFIED"
    NOT_FOUND  = "NOT_FOUND"
    ERROR      = "ERROR"


class Issuer(Base):
    __tablename__ = "issuers"
    issuer_id        = Column(String, primary_key=True)
    issuer_name      = Column(String, nullable=False)
    verification_url = Column(String, nullable=True, default="")


class Certificate(Base):
    __tablename__ = "certificates"
    certificate_id       = Column(String, primary_key=True)
    candidate_id         = Column(UUID(as_uuid=True), nullable=False)
    issuer_id            = Column(String, ForeignKey("issuers.issuer_id", ondelete="CASCADE"), nullable=False)
    certificate_name     = Column(String, nullable=True)
    issue_date           = Column(String, nullable=True)
    expiration_date      = Column(String, nullable=True)
    first_name           = Column(String, nullable=True)
    last_name            = Column(String, nullable=True)
    status               = Column(Enum(VerificationStatus), nullable=False)
    verification_details = Column(Text, nullable=True)
    created_at           = Column(DateTime, default=datetime.utcnow)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_connection():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))