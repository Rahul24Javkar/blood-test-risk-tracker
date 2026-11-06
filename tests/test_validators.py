
import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Patient
from app.validators import validate_patient_data


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


TEST_RECORDS = [
    {
        "full_name": "Robyn Pears",
        "date_of_birth": "28.01.1960",
        "email": "robyn@gmail.com",
        "glucose": 232,
        "haemoglobin": 13.5,
        "cholesterol": 180,
        "valid": True,
        "errors": []
    },
    {
        "full_name": "John Hunter",
        "date_of_birth": "10.12.1990",
        "email": "hunter@gmail",
        "glucose": 94,
        "haemoglobin": 15,
        "cholesterol": 200,
        "valid": False,
        "errors": ["email"]
    },
    {
        "full_name": "Darryl Tim",
        "date_of_birth": "12.11.1993",
        "email": "timd@smh.com.au",
        "glucose": 240,
        "haemoglobin": 18.6,
        "cholesterol": 326,
        "valid": True,
        "errors": []
    },
    {
        "full_name": "Peter Larry",
        "date_of_birth": "31.11.2001",
        "email": "Larry@hotmail.com",
        "glucose": 88,
        "haemoglobin": 11.5,
        "cholesterol": 165,
        "valid": False,
        "errors": ["date_of_birth"]
    },
    {
        "full_name": "Sam Kerr",
        "date_of_birth": "09.12.2006",
        "email": "sam@news.com.au",
        "glucose": 198,
        "haemoglobin": 8.9,
        "cholesterol": 192,
        "valid": True,
        "errors": []
    },
    {
        "full_name": "Robyn Pears",
        "date_of_birth": "28.01.1960",
        "email": "robyn@gmail.com",
        "glucose": 232,
        "haemoglobin": 13.5,
        "cholesterol": 180,
        "valid": False,
        "errors": ["email"]
    },
    {
        "full_name": "Madison XI",
        "date_of_birth": "12.09.1998",
        "email": "madison@hotmail.com",
        "glucose": 85,
        "haemoglobin": 7.6,
        "cholesterol": 163,
        "valid": True,
        "errors": []
    },
    {
        "full_name": "Kris Wu",
        "date_of_birth": "19.10.2030",
        "email": "Kris.wu.gmail.com",
        "glucose": 79,
        "haemoglobin": 16.5,
        "cholesterol": 197,
        "valid": False,
        "errors": ["date_of_birth", "email"]
    },
    {
        "full_name": "Tenille Singh",
        "date_of_birth": "30.11.1991",
        "email": "Tenille@yahoo.com",
        "glucose": 101,
        "haemoglobin": 15,
        "cholesterol": 310,
        "valid": True,
        "errors": []
    },
    {
        "full_name": "Prem Kumar",
        "date_of_birth": "28.04.1990",
        "email": "prem@telstra.com",
        "glucose": 155,
        "haemoglobin": 12.5,
        "cholesterol": 265,
        "valid": True,
        "errors": []
    }
]


def test_all_ten_patient_records(db_session):
    saved_count = 0
    rejected_count = 0

    for index, record in enumerate(TEST_RECORDS, start=1):

        patient_data = {
            key: value
            for key, value in record.items()
            if key not in ("valid", "errors")
        }

        clean_data, errors = validate_patient_data(
            patient_data,
            db_session
        )

        actual_errors = set(errors.keys())
        expected_errors = set(record["errors"])

        assert actual_errors == expected_errors, (
            f"Test {index} failed: {errors}"
        )

        if record["valid"]:
            patient = Patient(
                **clean_data,
                risk_level="unknown",
                remarks="Validation test",
                remarks_source="rules"
            )

            db_session.add(patient)
            db_session.commit()

            saved_count += 1

        else:
            rejected_count += 1

    assert saved_count == 6
    assert rejected_count == 4

    assert db_session.query(Patient).count() == 6
