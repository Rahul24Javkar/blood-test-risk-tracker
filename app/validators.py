
import math
import re
from datetime import datetime, date

from app.models import Patient


# Accepted date formats
DATE_FORMATS = ("%d/%m/%Y", "%d.%m.%Y", "%d-%m-%Y")


# Allowed numeric ranges
NUMERIC_RANGES = {
    "glucose": (20, 800),
    "haemoglobin": (3, 25),
    "cholesterol": (50, 600),
}


def validate_full_name(value):
    """Check whether the patient's full name is valid."""

    if not isinstance(value, str):
        return None, "Full name is required."

    name = value.strip()

    if not name:
        return None, "Full name is required."

    if len(name) < 2 or len(name) > 100:
        return None, "Full name must contain 2 to 100 characters."

    if not all(char.isalpha() or char in " -'" for char in name):
        return None, "Name can contain only letters, spaces, hyphens and apostrophes."

    return name, None


def validate_date_of_birth(value):
    """Parse and validate the patient's date of birth."""

    if not isinstance(value, str) or not value.strip():
        return None, "Date of birth is required."

    dob = None

    for date_format in DATE_FORMATS:
        try:
            dob = datetime.strptime(value.strip(), date_format).date()
            break
        except ValueError:
            continue

    if dob is None:
        return None, "Enter a valid date in dd/mm/yyyy format."

    if dob > date.today():
        return None, "Date of birth cannot be in the future."

    if dob < date(1900, 1, 1):
        return None, "Date of birth cannot be before 01/01/1900."

    return dob, None


def validate_email(value):
    """Check the email format and normalize it to lowercase."""

    if not isinstance(value, str) or not value.strip():
        return None, "Email address is required."

    email = value.strip().lower()

    email_pattern = (
        r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+"
        r"@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*"
        r"\.[A-Za-z]{2,}$"
    )

    if email.count("@") != 1 or not re.fullmatch(email_pattern, email):
        return None, "Enter a valid email address."

    return email, None


def validate_numeric_value(field_name, value):
    """Check whether a blood test value is numeric and within range."""

    if isinstance(value, bool) or value is None:
        return None, f"{field_name.capitalize()} must be a valid number."

    try:
        number = float(value)
    except (ValueError, TypeError):
        return None, f"{field_name.capitalize()} must be a valid number."

    if not math.isfinite(number):
        return None, f"{field_name.capitalize()} must be a finite number."

    minimum, maximum = NUMERIC_RANGES[field_name]

    if not minimum <= number <= maximum:
        return None, (
            f"{field_name.capitalize()} must be between "
            f"{minimum} and {maximum}."
        )

    return number, None


def validate_patient_data(data, db_session, patient_id=None):
    """
    Validate all patient fields and check email uniqueness.

    patient_id is excluded during updates so a patient can
    retain their existing email address.
    """

    clean_data = {}
    errors = {}

    # Validate full name
    name, error = validate_full_name(data.get("full_name"))

    if error:
        errors["full_name"] = error
    else:
        clean_data["full_name"] = name

    # Validate date of birth
    dob, error = validate_date_of_birth(data.get("date_of_birth"))

    if error:
        errors["date_of_birth"] = error
    else:
        clean_data["date_of_birth"] = dob

    # Validate email
    email, error = validate_email(data.get("email"))

    if error:
        errors["email"] = error
    else:
        existing_patient = db_session.query(Patient).filter(
            Patient.email == email,
            Patient.id != patient_id if patient_id is not None else True
        ).first()

        if existing_patient:
            errors["email"] = "This email address is already registered."
        else:
            clean_data["email"] = email

    # Validate blood test values
    for field_name in NUMERIC_RANGES:
        number, error = validate_numeric_value(
            field_name,
            data.get(field_name)
        )

        if error:
            errors[field_name] = error
        else:
            clean_data[field_name] = number

    return clean_data, errors
