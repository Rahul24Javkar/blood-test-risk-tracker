from datetime import datetime, date

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Date,
    DateTime,
    Text,
)

from app.database import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)

    full_name = Column(String(100), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)

    glucose = Column(Float, nullable=False)
    haemoglobin = Column(Float, nullable=False)
    cholesterol = Column(Float, nullable=False)

    risk_level = Column(String(20), nullable=False, default="unknown")
    remarks = Column(Text, nullable=False)
    remarks_source = Column(String(20), nullable=False, default="rules")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )


class RejectedSubmission(Base):
    __tablename__ = "rejected_submissions"

    id = Column(Integer, primary_key=True, index=True)

    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    raw_input = Column(Text, nullable=False)
    errors = Column(Text, nullable=False)