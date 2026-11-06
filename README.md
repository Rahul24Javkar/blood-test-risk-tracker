# Blood Test Risk Tracker

A Python-based web application for managing patient records, validating blood test results, and generating AI-assisted health risk assessments using Google's Gemini API.

## Overview

The Blood Test Risk Tracker allows users to create, view, update, and delete patient records containing personal information and blood test results.

The application validates patient information before saving it, evaluates blood test values using a rule-based assessment engine, and integrates Google's Gemini API to generate explanatory health risk remarks.

If the external AI service is unavailable or returns an invalid response, the application automatically falls back to its rule-based assessment to ensure that patient records can still be saved.

**Disclaimer:** This application is developed for educational purposes only. The risk assessments are simplified screening indicators and are not intended to diagnose medical conditions or replace professional medical advice.

## Features

- **Patient Management:** Complete CRUD operations to create, retrieve, update, and delete patient records.
- **Input Validation:** Validates patient names, email addresses, dates of birth, and numerical blood test values.
- **Date Validation:** Supports DD.MM.YYYY, DD/MM/YYYY, and DD-MM-YYYY formats and rejects invalid or future dates.
- **Duplicate Prevention:** Ensures that each patient email address is unique.
- **Persistent Storage:** Stores patient records using SQLite and SQLAlchemy.
- **AI Integration:** Uses Google's Gemini API to generate explanatory remarks based on blood test values.
- **Rule-Based Assessment:** Evaluates glucose, haemoglobin, and cholesterol values to determine a risk category.
- **AI Fallback Handling:** Uses the rule-based assessment if the AI service fails or returns an invalid response.
- **Rejected Submissions:** Maintains a separate record of invalid submissions and their validation errors.
- **User Interface:** Provides a simple web interface built with Bootstrap, HTML, CSS, and Jinja2.
- **Automated Testing:** Includes unit and API tests using pytest.

## Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python 3.11 |
| Backend Framework | FastAPI |
| Database | SQLite |
| ORM | SQLAlchemy |
| Frontend | HTML, CSS, Bootstrap 5 |
| Template Engine | Jinja2 |
| AI Integration | Google Gemini API |
| HTTP Client | Requests |
| Environment Configuration | python-dotenv |
| Testing | pytest |

## Project Structure

```text
blood-test-risk-tracker/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── validators.py
│   ├── rules.py
│   ├── ai_service.py
│   ├── services.py
│   │
│   ├── templates/
│   │   ├── base.html
│   │   ├── list.html
│   │   ├── form.html
│   │   └── rejected.html
│   │
│   └── static/
│       └── style.css
│
├── tests/
│   ├── test_validators.py
│   ├── test_rules.py
│   ├── test_ai_service.py
│   ├── test_services.py
│   └── test_api.py
│
├── .env.example
├── .gitignore
├── init_db.py
├── requirements.txt
└── README.md
```

## Prerequisites

Before running the application, ensure you have:

- Python 3.11 or later
- Git
- A Google Gemini API key

## Installation and Setup

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd blood-test-risk-tracker
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the virtual environment

**Windows PowerShell:**

```powershell
.\.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment variables

Create a `.env` file in the project root directory.

Use `.env.example` as a reference:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=your_available_gemini_model
```

Replace the placeholders with your own Gemini API key and a model available to your account.

**Important:** Never commit your `.env` file or expose your API key publicly.

### 6. Initialize the database

The application creates the required database tables automatically during startup.

Alternatively, you can initialize the database manually:

```bash
python init_db.py
```

### 7. Run the application

```bash
uvicorn app.main:app --reload
```

The application will be available at:

http://127.0.0.1:8000/

## Application Usage

1. Open the application in your browser.
2. Navigate to **Add Patient** to create a new patient record.
3. Enter the patient's personal details and blood test values.
4. Submit the form. The backend validates the information before processing it.
5. Valid submissions are assessed using the rule-based engine and Gemini API.
6. View saved patient records on the dashboard.
7. Use the Edit and Delete options to manage existing records.
8. Visit the Rejected Submissions page to review invalid submissions and their errors.

## REST API Endpoints

The application also exposes REST API endpoints through FastAPI.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api` | API information |
| POST | `/api/patients` | Create a patient |
| GET | `/api/patients` | Retrieve all patients |
| GET | `/api/patients/{id}` | Retrieve a patient by ID |
| PUT | `/api/patients/{id}` | Update a patient |
| DELETE | `/api/patients/{id}` | Delete a patient |
| GET | `/api/rejected` | Retrieve rejected submissions |

Interactive API documentation is available at:

http://127.0.0.1:8000/docs

## Input Validation

The application performs backend validation before processing patient records.

| Field | Validation |
|---|---|
| Full Name | Required, 2–100 characters; letters, spaces, hyphens and apostrophes |
| Date of Birth | Valid calendar date; supported formats; cannot be in the future |
| Email | Valid email format; normalized to lowercase; must be unique |
| Glucose | Numeric value between 20 and 800 mg/dL |
| Haemoglobin | Numeric value between 3 and 25 g/dL |
| Cholesterol | Numeric value between 50 and 600 mg/dL |

All applicable validation errors are collected and returned together.

Invalid submissions are stored separately in the `rejected_submissions` table.

## AI Integration and Risk Assessment

The application uses a hybrid assessment approach combining Python-based rules and Google's Gemini API.

### Rule-Based Assessment

The rules engine evaluates the three blood test values using configured screening thresholds.

**Glucose (mg/dL):**

- Below 70: Low
- 70–99: Normal
- 100–125: Elevated
- 126 and above: High

**Haemoglobin (g/dL):**

- Below 8: Markedly low
- 8–11.9: Low
- 12–17.5: Normal
- Above 17.5: High

**Total Cholesterol (mg/dL):**

- Below 200: Desirable
- 200–239: Borderline
- 240 and above: High

The overall risk category is determined using these individual screening flags.

### Gemini API Integration

After successful validation:

1. The application evaluates the blood test values using the Python rules engine.
2. It sends the three numerical values and screening flags to Gemini.
3. Gemini generates possible conditions and a short explanatory remark.
4. The response is validated before being stored.
5. Python's rule-based assessment remains authoritative for the final risk category.

Patient names, email addresses, and dates of birth are not included in the AI request.

### Fallback Mechanism

If the Gemini API is unavailable, times out, or returns an invalid response, the application uses its rule-based assessment instead.

The `Remarks Source` field indicates whether the assessment came from the AI service or the rule-based fallback.

This ensures that an external API failure does not prevent valid patient records from being saved.

## Running Automated Tests

The project uses pytest for automated testing.

Run the complete test suite:

```bash
python -m pytest -v
```

The tests cover:

- Patient input validation
- Rule-based risk assessment
- Patient creation, updating, and deletion
- Rejected submission handling
- REST API endpoints
- AI service behaviour

## Database Design

The application uses two primary database tables:

**1. patients**

Stores patient information, blood test values, risk assessments, remarks, and timestamps.

**2. rejected_submissions**

Stores the original submitted input and corresponding validation errors for submissions that fail validation.

SQLite provides persistent storage, while SQLAlchemy manages database operations through ORM models.

## Security Considerations

- API credentials are stored in environment variables.
- The `.env` file is excluded from version control.
- Database files and virtual environments are excluded through `.gitignore`.
- Only the required numerical blood test values and screening flags are sent to the AI service.
- No real patient information should be used for testing or demonstration.

## Future Improvements

- Add user authentication and role-based access control.
- Introduce pagination and more advanced patient search.
- Add audit logging for patient record modifications.
- Support additional blood test parameters.
- Migrate SQLite to PostgreSQL for larger deployments.
- Introduce more comprehensive automated and integration tests.

## Author

Developed as part of the Python Skills Evaluation assessment.

## Disclaimer

This project is intended for educational and demonstration purposes. The blood test thresholds and generated remarks are simplified screening indicators. They are not clinically validated diagnostic tools. All results should be interpreted by qualified healthcare professionals.