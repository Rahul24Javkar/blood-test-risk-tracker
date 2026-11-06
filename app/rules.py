
"""
Rule-based evaluation of patient blood test values.

These thresholds are general adult screening references.
They are educational indicators, not diagnostic criteria.
"""


# Glucose thresholds (mg/dL)
GLUCOSE_LOW = 70
GLUCOSE_NORMAL_MAX = 99
GLUCOSE_ELEVATED_MAX = 125

# Haemoglobin thresholds (g/dL)
HAEMOGLOBIN_MARKEDLY_LOW = 8
HAEMOGLOBIN_LOW_MAX = 11.9
HAEMOGLOBIN_NORMAL_MAX = 17.5

# Total cholesterol thresholds (mg/dL)
CHOLESTEROL_DESIRABLE_MAX = 200
CHOLESTEROL_BORDERLINE_MAX = 239


def evaluate_glucose(value):
    """Classify a glucose reading."""

    if value < GLUCOSE_LOW:
        return "low"

    if value <= GLUCOSE_NORMAL_MAX:
        return "normal"

    if value <= GLUCOSE_ELEVATED_MAX:
        return "elevated"

    return "high"


def evaluate_haemoglobin(value):
    """Classify a haemoglobin reading."""

    if value < HAEMOGLOBIN_MARKEDLY_LOW:
        return "markedly low"

    if value <= HAEMOGLOBIN_LOW_MAX:
        return "low"

    if value <= HAEMOGLOBIN_NORMAL_MAX:
        return "normal"

    return "high"


def evaluate_cholesterol(value):
    """Classify a total cholesterol reading."""

    if value < CHOLESTEROL_DESIRABLE_MAX:
        return "desirable"

    if value <= CHOLESTEROL_BORDERLINE_MAX:
        return "borderline"

    return "high"


def assess_health_risk(glucose, haemoglobin, cholesterol):
    """
    Evaluate all three blood test values and produce
    an overall risk level with a fallback remark.
    """

    flags = {
        "glucose": evaluate_glucose(glucose),
        "haemoglobin": evaluate_haemoglobin(haemoglobin),
        "cholesterol": evaluate_cholesterol(cholesterol)
    }

    high_risk_flags = {"high", "markedly low"}

    moderate_risk_flags = {
        "low",
        "elevated",
        "borderline"
    }

    if any(flag in high_risk_flags for flag in flags.values()):
        risk_level = "high"

    elif any(flag in moderate_risk_flags for flag in flags.values()):
        risk_level = "moderate"

    else:
        risk_level = "low"

    abnormal_results = []

    if flags["glucose"] != "normal":
        abnormal_results.append(
            f"Glucose is {flags['glucose']} at {glucose} mg/dL"
        )

    if flags["haemoglobin"] != "normal":
        abnormal_results.append(
            f"Haemoglobin is {flags['haemoglobin']} at "
            f"{haemoglobin} g/dL"
        )

    if flags["cholesterol"] != "desirable":
        abnormal_results.append(
            f"Total cholesterol is {flags['cholesterol']} "
            f"at {cholesterol} mg/dL"
        )

    if abnormal_results:
        findings = "; ".join(abnormal_results)

        remark = (
            f"Screening flags: {findings}. "
            "Discuss these results with a healthcare professional."
        )

    else:
        remark = (
            "All three blood test values are within the configured "
            "screening ranges. Discuss results with a healthcare "
            "professional for individual interpretation."
        )

    return {
        "risk_level": risk_level,
        "flags": flags,
        "remark": remark
    }
