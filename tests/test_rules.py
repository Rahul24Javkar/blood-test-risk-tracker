
from app.rules import assess_health_risk


def test_high_glucose():
    result = assess_health_risk(232, 13.5, 180)

    assert result["risk_level"] == "high"
    assert result["flags"]["glucose"] == "high"


def test_markedly_low_haemoglobin():
    result = assess_health_risk(85, 7.6, 163)

    assert result["risk_level"] == "high"
    assert result["flags"]["haemoglobin"] == "markedly low"


def test_moderate_risk():
    result = assess_health_risk(101, 15, 200)

    assert result["risk_level"] == "moderate"


def test_all_values_within_ranges():
    result = assess_health_risk(85, 15, 180)

    assert result["risk_level"] == "low"
    assert result["remark"]


def test_multiple_high_values():
    result = assess_health_risk(240, 18.6, 326)

    assert result["risk_level"] == "high"
    assert result["flags"]["glucose"] == "high"
    assert result["flags"]["haemoglobin"] == "high"
    assert result["flags"]["cholesterol"] == "high"
