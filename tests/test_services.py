
import json

import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app import services
from app.models import Patient, RejectedSubmission


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

    Base.metadata.create_all(bind=engine)

    TestingSession = sessionmaker(bind=engine)
    session = TestingSession()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def valid_patient_data():
    return {
        "full_name": "Alex Morgan",
        "date_of_birth": "15/05/1990",
        "email": "alex@example.com",
        "glucose": "95",
        "haemoglobin": "15",
        "cholesterol": "180"
    }


def test_create_patient_uses_rules_fallback(
    db_session,
    valid_patient_data,
    monkeypatch
):
    monkeypatch.setattr(
        services,
        "generate_ai_assessment",
        lambda *args: None
    )

    patient, errors = services.create_patient(
        db_session,
        valid_patient_data
    )

    assert errors == {}
    assert patient is not None
    assert patient.full_name == "Alex Morgan"
    assert patient.remarks_source == "rules"
    assert patient.risk_level == "low"
    assert patient.remarks


def test_invalid_submission_is_logged(
    db_session,
    valid_patient_data,
    monkeypatch
):
    monkeypatch.setattr(
        services,
        "generate_ai_assessment",
        lambda *args: None
    )

    invalid_data = valid_patient_data.copy()
    invalid_data["email"] = "invalid-email"

    patient, errors = services.create_patient(
        db_session,
        invalid_data
    )

    assert patient is None
    assert "email" in errors
    assert db_session.query(Patient).count() == 0

    rejected = db_session.query(RejectedSubmission).first()

    assert rejected is not None
    assert json.loads(rejected.raw_input)["email"] == "invalid-email"
    assert "email" in json.loads(rejected.errors)


def test_update_without_blood_changes_does_not_call_ai(
    db_session,
    valid_patient_data,
    monkeypatch
):
    monkeypatch.setattr(
        services,
        "generate_ai_assessment",
        lambda *args: None
    )

    patient, errors = services.create_patient(
        db_session,
        valid_patient_data
    )

    assert errors == {}

    original_remarks = patient.remarks
    original_risk = patient.risk_level

    def unexpected_ai_call(*args):
        raise AssertionError(
            "Gemini should not be called when blood values are unchanged."
        )

    monkeypatch.setattr(
        services,
        "generate_ai_assessment",
        unexpected_ai_call
    )

    updated_data = valid_patient_data.copy()
    updated_data["full_name"] = "Alex Morgan Updated"
    updated_data["email"] = "alex.updated@example.com"

    updated_patient, errors = services.update_patient(
        db_session,
        patient.id,
        updated_data
    )

    assert errors == {}
    assert updated_patient.full_name == "Alex Morgan Updated"
    assert updated_patient.remarks == original_remarks
    assert updated_patient.risk_level == original_risk


def test_update_with_blood_changes_uses_rules_fallback(
    db_session,
    valid_patient_data,
    monkeypatch
):
    monkeypatch.setattr(
        services,
        "generate_ai_assessment",
        lambda *args: None
    )

    patient, errors = services.create_patient(
        db_session,
        valid_patient_data
    )

    assert errors == {}

    updated_data = valid_patient_data.copy()
    updated_data["glucose"] = "232"

    updated_patient, errors = services.update_patient(
        db_session,
        patient.id,
        updated_data
    )

    assert errors == {}
    assert updated_patient.glucose == 232
    assert updated_patient.risk_level == "high"
    assert updated_patient.remarks_source == "rules"


def test_delete_patient(
    db_session,
    valid_patient_data,
    monkeypatch
):
    monkeypatch.setattr(
        services,
        "generate_ai_assessment",
        lambda *args: None
    )

    patient, errors = services.create_patient(
        db_session,
        valid_patient_data
    )

    assert errors == {}
    patient_id = patient.id

    deleted = services.delete_patient(
        db_session,
        patient_id
    )

    assert deleted is True
    assert services.get_patient(db_session, patient_id) is None
    assert db_session.query(Patient).count() == 0
