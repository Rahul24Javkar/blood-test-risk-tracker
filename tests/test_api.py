
import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.main import app, get_db


@pytest.fixture
def client():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine
    )

    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()

        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


@pytest.fixture
def patient_payload():
    return {
        "full_name": "Alex Morgan",
        "date_of_birth": "15/05/1990",
        "email": "alex@example.com",
        "glucose": 95,
        "haemoglobin": 15,
        "cholesterol": 180
    }


def test_root_endpoint(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "Patient Dashboard" in response.text


def test_create_and_get_patient(client, patient_payload, monkeypatch):
    from app import services

    monkeypatch.setattr(
        services,
        "generate_ai_assessment",
        lambda *args: None
    )

    create_response = client.post(
        "/api/patients",
        json=patient_payload
    )

    assert create_response.status_code == 201

    created_patient = create_response.json()
    patient_id = created_patient["id"]

    assert created_patient["full_name"] == "Alex Morgan"
    assert created_patient["remarks_source"] == "rules"

    get_response = client.get(
        f"/api/patients/{patient_id}"
    )

    assert get_response.status_code == 200
    assert get_response.json()["id"] == patient_id


def test_list_patients(client, patient_payload, monkeypatch):
    from app import services

    monkeypatch.setattr(
        services,
        "generate_ai_assessment",
        lambda *args: None
    )

    client.post("/api/patients", json=patient_payload)

    response = client.get("/api/patients")

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_invalid_patient_returns_422(client, patient_payload):
    invalid_payload = patient_payload.copy()
    invalid_payload["email"] = "not-an-email"

    response = client.post(
        "/api/patients",
        json=invalid_payload
    )

    assert response.status_code == 422
    assert "email" in response.json()["detail"]["errors"]


def test_rejected_submissions_endpoint(client, patient_payload):
    invalid_payload = patient_payload.copy()
    invalid_payload["email"] = "invalid-email"

    client.post("/api/patients", json=invalid_payload)

    response = client.get("/api/rejected")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["raw_input"]["email"] == "invalid-email"


def test_update_patient(client, patient_payload, monkeypatch):
    from app import services

    monkeypatch.setattr(
        services,
        "generate_ai_assessment",
        lambda *args: None
    )

    create_response = client.post(
        "/api/patients",
        json=patient_payload
    )

    patient_id = create_response.json()["id"]

    updated_payload = patient_payload.copy()
    updated_payload["email"] = "gokul@infocare.com"

    response = client.put(
        f"/api/patients/{patient_id}",
        json=updated_payload
    )

    assert response.status_code == 200
    assert response.json()["email"] == "gokul@infocare.com"


def test_delete_patient(client, patient_payload, monkeypatch):
    from app import services

    monkeypatch.setattr(
        services,
        "generate_ai_assessment",
        lambda *args: None
    )

    create_response = client.post(
        "/api/patients",
        json=patient_payload
    )

    patient_id = create_response.json()["id"]

    response = client.delete(
        f"/api/patients/{patient_id}"
    )

    assert response.status_code == 200

    get_response = client.get(
        f"/api/patients/{patient_id}"
    )

    assert get_response.status_code == 404
