
import json

import pytest
import requests

from app import ai_service


FLAGS = {
    "glucose": "high",
    "haemoglobin": "normal",
    "cholesterol": "desirable"
}


VALID_AI_RESPONSE = {
    "risk_level": "high",
    "possible_conditions": [
        "Elevated glucose pattern"
    ],
    "remark": (
        "Glucose is elevated at 232 mg/dL. "
        "Discuss these findings with a healthcare professional."
    )
}


class FakeResponse:
    def __init__(self, data, status_code=200):
        self.data = data
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            error = requests.exceptions.HTTPError(
                f"HTTP {self.status_code}"
            )
            error.response = self
            raise error

    def json(self):
        return self.data


def make_gemini_response(ai_result):
    return {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {"text": json.dumps(ai_result)}
                    ]
                }
            }
        ]
    }


@pytest.fixture(autouse=True)
def configure_gemini(monkeypatch):
    monkeypatch.setattr(
        ai_service,
        "GEMINI_API_KEY",
        "test-api-key"
    )
    monkeypatch.setattr(
        ai_service,
        "GEMINI_MODEL",
        "test-model"
    )


def test_successful_ai_assessment(monkeypatch):
    def fake_post(*args, **kwargs):
        return FakeResponse(
            make_gemini_response(VALID_AI_RESPONSE)
        )

    monkeypatch.setattr(ai_service.requests, "post", fake_post)

    result = ai_service.generate_ai_assessment(
        232,
        13.5,
        180,
        FLAGS
    )

    assert result is not None
    assert result["risk_level"] == "high"
    assert result["possible_conditions"] == [
        "Elevated glucose pattern"
    ]


def test_invalid_json_is_retried(monkeypatch):
    calls = {"count": 0}

    def fake_post(*args, **kwargs):
        calls["count"] += 1

        if calls["count"] == 1:
            return FakeResponse({
                "candidates": [
                    {
                        "content": {
                            "parts": [{"text": "not valid JSON"}]
                        }
                    }
                ]
            })

        return FakeResponse(
            make_gemini_response(VALID_AI_RESPONSE)
        )

    monkeypatch.setattr(ai_service.requests, "post", fake_post)

    result = ai_service.generate_ai_assessment(
        232,
        13.5,
        180,
        FLAGS
    )

    assert result is not None
    assert calls["count"] == 2


def test_server_error_is_retried(monkeypatch):
    calls = {"count": 0}

    def fake_post(*args, **kwargs):
        calls["count"] += 1

        if calls["count"] == 1:
            return FakeResponse({}, status_code=500)

        return FakeResponse(
            make_gemini_response(VALID_AI_RESPONSE)
        )

    monkeypatch.setattr(ai_service.requests, "post", fake_post)

    result = ai_service.generate_ai_assessment(
        232,
        13.5,
        180,
        FLAGS
    )

    assert result is not None
    assert calls["count"] == 2


def test_timeout_returns_none(monkeypatch):
    def fake_post(*args, **kwargs):
        raise requests.exceptions.Timeout()

    monkeypatch.setattr(ai_service.requests, "post", fake_post)

    result = ai_service.generate_ai_assessment(
        232,
        13.5,
        180,
        FLAGS
    )

    assert result is None


def test_ai_risk_level_is_overridden_by_rules(monkeypatch):
    invalid_result = {
        **VALID_AI_RESPONSE,
        "risk_level": "low"
    }

    def fake_post(*args, **kwargs):
        return FakeResponse(
            make_gemini_response(invalid_result)
        )

    monkeypatch.setattr(ai_service.requests, "post", fake_post)

    result = ai_service.generate_ai_assessment(
        232,
        13.5,
        180,
        FLAGS
    )

    assert result is not None
    assert result["risk_level"] == "high"
    assert result["possible_conditions"] == (
        VALID_AI_RESPONSE["possible_conditions"]
    )
    assert result["remark"] == VALID_AI_RESPONSE["remark"]
