from pathlib import Path
from contextlib import asynccontextmanager
import json

from fastapi import (
    Body,
    Depends,
    FastAPI,
    Form,
    HTTPException,
    Request,
    status
)
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine
from app import services
from app.models import RejectedSubmission


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Blood Test Risk Tracker",
    description=(
        "An educational application for managing patient blood test "
        "records and generating screening risk indications."
    ),
    version="1.0.0",
    lifespan=lifespan
)

APP_DIR = Path(__file__).resolve().parent

app.mount(
    "/static",
    StaticFiles(directory=APP_DIR / "static"),
    name="static"
)

templates = Jinja2Templates(
    directory=str(APP_DIR / "templates")
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def serialize_patient(patient):
    return {
        "id": patient.id,
        "full_name": patient.full_name,
        "date_of_birth": patient.date_of_birth.isoformat(),
        "email": patient.email,
        "glucose": patient.glucose,
        "haemoglobin": patient.haemoglobin,
        "cholesterol": patient.cholesterol,
        "risk_level": patient.risk_level,
        "remarks": patient.remarks,
        "remarks_source": patient.remarks_source,
        "created_at": patient.created_at.isoformat(),
        "updated_at": patient.updated_at.isoformat()
    }


def serialize_rejected_submission(submission):
    return {
        "id": submission.id,
        "submitted_at": submission.submitted_at.isoformat(),
        "raw_input": json.loads(submission.raw_input),
        "errors": json.loads(submission.errors)
    }


def render_patient_form(
    request,
    page_title,
    form_action,
    form_data=None,
    errors=None,
    status_code=200
):
    return templates.TemplateResponse(
        request=request,
        name="form.html",
        context={
            "page_title": page_title,
            "form_action": form_action,
            "form_data": form_data or {},
            "errors": errors or {},
            "message": None
        },
        status_code=status_code
    )


# --------------------------------------------------
# HTML FRONTEND ROUTES
# --------------------------------------------------

@app.get("/")
def dashboard(
    request: Request,
    q: str = "",
    message: str = "",
    db: Session = Depends(get_db)
):
    all_patients = services.get_all_patients(db)

    high_risk_count = sum(
        1 for patient in all_patients
        if patient.risk_level == "high"
    )

    search_query = q.strip().lower()

    if search_query:
        patients = [
            patient for patient in all_patients
            if search_query in patient.full_name.lower()
            or search_query in patient.email.lower()
        ]
    else:
        patients = all_patients

    rejected_count = db.query(RejectedSubmission).count()

    return templates.TemplateResponse(
        request=request,
        name="list.html",
        context={
            "patients": patients,
            "high_risk_count": high_risk_count,
            "rejected_count": rejected_count,
            "search_query": q,
            "message": message
        }
    )


@app.get("/patients/new")
def new_patient_page(request: Request):
    return render_patient_form(
        request=request,
        page_title="Add New Patient",
        form_action="/patients/new"
    )


@app.post("/patients/new")
def create_patient_page(
    request: Request,
    full_name: str = Form(...),
    date_of_birth: str = Form(...),
    email: str = Form(...),
    glucose: str = Form(...),
    haemoglobin: str = Form(...),
    cholesterol: str = Form(...),
    db: Session = Depends(get_db)
):
    patient_data = {
        "full_name": full_name,
        "date_of_birth": date_of_birth,
        "email": email,
        "glucose": glucose,
        "haemoglobin": haemoglobin,
        "cholesterol": cholesterol
    }

    patient, errors = services.create_patient(
        db,
        patient_data
    )

    if errors:
        return render_patient_form(
            request=request,
            page_title="Add New Patient",
            form_action="/patients/new",
            form_data=patient_data,
            errors=errors,
            status_code=422
        )

    return RedirectResponse(
        url="/?message=Patient+created+successfully",
        status_code=303
    )


@app.get("/patients/{patient_id}/edit")
def edit_patient_page(
    patient_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    patient = services.get_patient(db, patient_id)

    if patient is None:
        raise HTTPException(
            status_code=404,
            detail="Patient not found."
        )

    form_data = {
        "full_name": patient.full_name,
        "date_of_birth": patient.date_of_birth.strftime("%d/%m/%Y"),
        "email": patient.email,
        "glucose": patient.glucose,
        "haemoglobin": patient.haemoglobin,
        "cholesterol": patient.cholesterol
    }

    return render_patient_form(
        request=request,
        page_title="Edit Patient",
        form_action=f"/patients/{patient_id}/edit",
        form_data=form_data
    )


@app.post("/patients/{patient_id}/edit")
def update_patient_page(
    patient_id: int,
    request: Request,
    full_name: str = Form(...),
    date_of_birth: str = Form(...),
    email: str = Form(...),
    glucose: str = Form(...),
    haemoglobin: str = Form(...),
    cholesterol: str = Form(...),
    db: Session = Depends(get_db)
):
    patient_data = {
        "full_name": full_name,
        "date_of_birth": date_of_birth,
        "email": email,
        "glucose": glucose,
        "haemoglobin": haemoglobin,
        "cholesterol": cholesterol
    }

    patient, errors = services.update_patient(
        db,
        patient_id,
        patient_data
    )

    if "patient" in errors:
        raise HTTPException(
            status_code=404,
            detail=errors["patient"]
        )

    if errors:
        return render_patient_form(
            request=request,
            page_title="Edit Patient",
            form_action=f"/patients/{patient_id}/edit",
            form_data=patient_data,
            errors=errors,
            status_code=422
        )

    return RedirectResponse(
        url="/?message=Patient+updated+successfully",
        status_code=303
    )


@app.post("/patients/{patient_id}/delete")
def delete_patient_page(
    patient_id: int,
    db: Session = Depends(get_db)
):
    deleted = services.delete_patient(
        db,
        patient_id
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Patient not found."
        )

    return RedirectResponse(
        url="/?message=Patient+deleted+successfully",
        status_code=303
    )


@app.get("/rejected")
def rejected_submissions_page(
    request: Request,
    db: Session = Depends(get_db)
):
    submissions = services.get_rejected_submissions(db)

    for submission in submissions:
        submission.raw_input = json.loads(submission.raw_input)
        submission.errors = json.loads(submission.errors)

    return templates.TemplateResponse(
        request=request,
        name="rejected.html",
        context={
            "submissions": submissions,
            "message": None
        }
    )


# --------------------------------------------------
# JSON REST API ROUTES
# --------------------------------------------------

@app.get("/api")
def api_root():
    return {
        "message": "Blood Test Risk Tracker API",
        "documentation": "/docs",
        "patient_endpoint": "/api/patients"
    }


@app.post(
    "/api/patients",
    status_code=status.HTTP_201_CREATED
)
def create_patient(
    patient_data: dict = Body(...),
    db: Session = Depends(get_db)
):
    patient, errors = services.create_patient(
        db,
        patient_data
    )

    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "message": "Patient validation failed.",
                "errors": errors
            }
        )

    return serialize_patient(patient)


@app.get("/api/patients")
def list_patients(db: Session = Depends(get_db)):
    patients = services.get_all_patients(db)

    return [
        serialize_patient(patient)
        for patient in patients
    ]


@app.get("/api/patients/{patient_id}")
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db)
):
    patient = services.get_patient(db, patient_id)

    if patient is None:
        raise HTTPException(
            status_code=404,
            detail="Patient not found."
        )

    return serialize_patient(patient)


@app.put("/api/patients/{patient_id}")
def update_patient(
    patient_id: int,
    patient_data: dict = Body(...),
    db: Session = Depends(get_db)
):
    patient, errors = services.update_patient(
        db,
        patient_id,
        patient_data
    )

    if "patient" in errors:
        raise HTTPException(
            status_code=404,
            detail=errors["patient"]
        )

    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "message": "Patient validation failed.",
                "errors": errors
            }
        )

    return serialize_patient(patient)


@app.delete("/api/patients/{patient_id}")
def remove_patient(
    patient_id: int,
    db: Session = Depends(get_db)
):
    deleted = services.delete_patient(
        db,
        patient_id
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Patient not found."
        )

    return {
        "message": "Patient deleted successfully.",
        "patient_id": patient_id
    }


@app.get("/api/rejected")
def list_rejected_submissions(
    db: Session = Depends(get_db)
):
    submissions = services.get_rejected_submissions(db)

    return [
        serialize_rejected_submission(submission)
        for submission in submissions
    ]
