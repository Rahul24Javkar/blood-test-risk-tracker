
import json
import logging

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.ai_service import generate_ai_assessment
from app.models import Patient, RejectedSubmission
from app.rules import assess_health_risk
from app.validators import validate_patient_data


logger = logging.getLogger(__name__)


def record_rejected_submission(db: Session, raw_data: dict, errors: dict):
    rejected = RejectedSubmission(
        raw_input=json.dumps(raw_data, default=str),
        errors=json.dumps(errors)
    )

    db.add(rejected)
    db.commit()


def get_patient(db: Session, patient_id: int):
    return db.query(Patient).filter(
        Patient.id == patient_id
    ).first()


def get_all_patients(db: Session):
    return db.query(Patient).order_by(
        Patient.created_at.desc()
    ).all()


def get_rejected_submissions(db: Session):
    return db.query(RejectedSubmission).order_by(
        RejectedSubmission.submitted_at.desc()
    ).all()


def create_patient(db: Session, patient_data: dict):
    clean_data, errors = validate_patient_data(
        patient_data,
        db
    )

    if errors:
        record_rejected_submission(db, patient_data, errors)
        return None, errors

    rule_assessment = assess_health_risk(
        clean_data["glucose"],
        clean_data["haemoglobin"],
        clean_data["cholesterol"]
    )

    ai_assessment = generate_ai_assessment(
        clean_data["glucose"],
        clean_data["haemoglobin"],
        clean_data["cholesterol"],
        rule_assessment["flags"]
    )

    if ai_assessment:
        risk_level = ai_assessment["risk_level"]
        remarks = ai_assessment["remark"]
        remarks_source = "ai"
    else:
        risk_level = rule_assessment["risk_level"]
        remarks = rule_assessment["remark"]
        remarks_source = "rules"

    patient = Patient(
        **clean_data,
        risk_level=risk_level,
        remarks=remarks,
        remarks_source=remarks_source
    )

    try:
        db.add(patient)
        db.commit()
        db.refresh(patient)
        return patient, {}

    except IntegrityError:
        db.rollback()

        errors = {
            "email": "This email address is already registered."
        }

        record_rejected_submission(db, patient_data, errors)
        return None, errors


def update_patient(
    db: Session,
    patient_id: int,
    patient_data: dict
):
    patient = get_patient(db, patient_id)

    if patient is None:
        return None, {"patient": "Patient not found."}

    clean_data, errors = validate_patient_data(
        patient_data,
        db,
        patient_id=patient_id
    )

    if errors:
        record_rejected_submission(db, patient_data, errors)
        return None, errors

    blood_value_fields = (
        "glucose",
        "haemoglobin",
        "cholesterol"
    )

    blood_values_changed = any(
        clean_data[field] != getattr(patient, field)
        for field in blood_value_fields
    )

    for field, value in clean_data.items():
        setattr(patient, field, value)

    if blood_values_changed:
        rule_assessment = assess_health_risk(
            patient.glucose,
            patient.haemoglobin,
            patient.cholesterol
        )

        ai_assessment = generate_ai_assessment(
            patient.glucose,
            patient.haemoglobin,
            patient.cholesterol,
            rule_assessment["flags"]
        )

        if ai_assessment:
            patient.risk_level = ai_assessment["risk_level"]
            patient.remarks = ai_assessment["remark"]
            patient.remarks_source = "ai"
        else:
            patient.risk_level = rule_assessment["risk_level"]
            patient.remarks = rule_assessment["remark"]
            patient.remarks_source = "rules"

    try:
        db.commit()
        db.refresh(patient)
        return patient, {}

    except IntegrityError:
        db.rollback()

        errors = {
            "email": "This email address is already registered."
        }

        record_rejected_submission(db, patient_data, errors)
        return None, errors


def delete_patient(db: Session, patient_id: int):
    patient = get_patient(db, patient_id)

    if patient is None:
        return False

    db.delete(patient)
    db.commit()

    return True
