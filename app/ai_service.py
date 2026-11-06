
import json
import logging

import requests

from app.config import GEMINI_API_KEY, GEMINI_MODEL


logger = logging.getLogger(__name__)

GEMINI_API_BASE_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
)

REQUEST_TIMEOUT = 15
MAX_ATTEMPTS = 2


def build_prompt(glucose, haemoglobin, cholesterol, flags):
    return f"""
You are an assistant producing a short, educational interpretation
of adult blood test values. You must not diagnose medical conditions.

Blood test values:
- Glucose: {glucose} mg/dL
- Haemoglobin: {haemoglobin} g/dL
- Total cholesterol: {cholesterol} mg/dL

Rule-based screening flags:
{json.dumps(flags)}

Return only a valid JSON object with this structure:
{{
    "risk_level": "low, moderate, or high",
    "possible_conditions": ["up to 3 brief items"],
    "remark": "A short explanation"
}}

Instructions:
- Use only the supplied values and screening flags.
- Do not claim that the patient has a confirmed disease.
- Describe possible patterns or risks to discuss with a doctor.
- If all values are within the configured ranges,
  return an empty possible_conditions list.
- The remark must contain no more than 40 words.
- Mention the values that contribute to the risk.
- End the remark by advising the person to consult
  a healthcare professional.
- The risk_level must agree with the supplied screening flags.
"""


def expected_risk_level(flags):
    high_flags = {"high", "markedly low"}
    moderate_flags = {"low", "elevated", "borderline"}

    if any(value in high_flags for value in flags.values()):
        return "high"

    if any(value in moderate_flags for value in flags.values()):
        return "moderate"

    return "low"


def validate_ai_result(result, flags):
    if not isinstance(result, dict):
        raise ValueError("AI response must be a JSON object.")

    risk_level = result.get("risk_level")
    possible_conditions = result.get("possible_conditions")
    remark = result.get("remark")

    if risk_level not in {"low", "moderate", "high"}:
        raise ValueError("AI returned an invalid risk level.")

    if not isinstance(possible_conditions, list):
        raise ValueError("Possible conditions must be a list.")

    if len(possible_conditions) > 3:
        raise ValueError("AI returned more than three possible conditions.")

    if not all(
        isinstance(item, str) and item.strip()
        for item in possible_conditions
    ):
        raise ValueError("Possible conditions contain invalid values.")

    if not isinstance(remark, str) or not remark.strip():
        raise ValueError("AI returned an empty remark.")

    if len(remark.split()) > 40:
        raise ValueError("AI remark exceeds 40 words.")

    # Python's rules engine is the source of truth for risk classification.
    final_risk_level = expected_risk_level(flags)

    if risk_level != final_risk_level:
        logger.warning(
            "Gemini risk level (%s) differs from rule-based risk level (%s). "
            "Using the rule-based risk level.",
            risk_level,
            final_risk_level
        )

    return {
        "risk_level": final_risk_level,
        "possible_conditions": possible_conditions,
        "remark": remark.strip()
    }


def generate_ai_assessment(
    glucose,
    haemoglobin,
    cholesterol,
    flags
):
    if not GEMINI_API_KEY or not GEMINI_MODEL:
        logger.warning("Gemini API key or model is not configured.")
        return None

    # Remove an optional models/ prefix to avoid duplicating it.
    model_name = GEMINI_MODEL.strip().removeprefix("models/")

    # Correct endpoint:
    # https://generativelanguage.googleapis.com/v1beta/models/
    # gemini-3.8-flash:generateContent
    url = (
        f"{GEMINI_API_BASE_URL}"
        f"{model_name}:generateContent"
    )

    prompt = build_prompt(
        glucose,
        haemoglobin,
        cholesterol,
        flags
    )

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY
    }

    logger.info("Calling Gemini model: %s", model_name)
    logger.info("Gemini endpoint: %s", url)

    for attempt in range(MAX_ATTEMPTS):
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=REQUEST_TIMEOUT
            )

            response.raise_for_status()

            response_data = response.json()

            candidates = response_data.get("candidates", [])

            if not candidates:
                raise ValueError(
                    "Gemini returned no response candidates."
                )

            parts = (
                candidates[0]
                .get("content", {})
                .get("parts", [])
            )

            if not parts or not parts[0].get("text"):
                raise ValueError(
                    "Gemini returned no response text."
                )

            ai_text = parts[0]["text"]

            parsed_result = json.loads(ai_text)

            validated_result = validate_ai_result(
                parsed_result,
                flags
            )

            logger.info("Gemini assessment generated successfully.")

            return validated_result

        except requests.exceptions.Timeout:
            logger.warning("Gemini request timed out.")
            return None

        except requests.exceptions.HTTPError as error:
            status_code = (
                error.response.status_code
                if error.response is not None
                else None
            )

            error_details = (
                getattr(error.response, "text", "No response body")[:1500]
                if error.response is not None
                else "No response body"
            )

            logger.warning(
                "Gemini HTTP request failed. Status: %s | Details: %s",
                status_code,
                error_details
            )

            # Retry only server-side errors.
            if status_code is not None and status_code >= 500:
                if attempt + 1 < MAX_ATTEMPTS:
                    logger.info("Retrying Gemini request...")
                    continue

            return None

        except (ValueError, KeyError, TypeError) as error:
            logger.warning(
                "Gemini response validation failed: %s. "
                "Attempt %s of %s.",
                error,
                attempt + 1,
                MAX_ATTEMPTS
            )

            if attempt + 1 < MAX_ATTEMPTS:
                continue

            return None

        except requests.exceptions.RequestException:
            logger.exception("Gemini network request failed.")
            return None

    return None
