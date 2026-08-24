from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app
from models import JobPosting

client = TestClient(app)

VALID_AUTH_HEADERS = {"X-API-Key": "test-app-api-key"}

SAMPLE_POSTING = JobPosting(
    title="Senior Backend Engineer",
    seniority="Senior",
    skills=["Python", "FastAPI"],
    location="Remote (US)",
    remote=True,
    salary_min=140000,
    salary_max=175000,
    salary_period="annual",
    currency="USD",
)


def test_extract_returns_structured_job_posting():
    with patch("main.client.chat.completions.create", return_value=SAMPLE_POSTING) as mock_create:
        response = client.post(
            "/extract",
            json={"text": "Senior Backend Engineer, remote, $140k-175k"},
            headers=VALID_AUTH_HEADERS,
        )

    assert response.status_code == 200
    assert response.json() == SAMPLE_POSTING.model_dump()
    mock_create.assert_called_once()


def test_extract_requires_text_field():
    response = client.post("/extract", json={}, headers=VALID_AUTH_HEADERS)
    assert response.status_code == 422


def test_extract_rejects_empty_text():
    response = client.post("/extract", json={"text": ""}, headers=VALID_AUTH_HEADERS)
    assert response.status_code == 422


def test_extract_returns_502_when_upstream_call_fails():
    with patch(
        "main.client.chat.completions.create", side_effect=RuntimeError("upstream failure")
    ):
        response = client.post(
            "/extract", json={"text": "some posting"}, headers=VALID_AUTH_HEADERS
        )

    assert response.status_code == 502
    assert "detail" in response.json()


def test_extract_rejects_missing_api_key():
    response = client.post("/extract", json={"text": "some posting"})
    assert response.status_code == 401


def test_extract_rejects_invalid_api_key():
    response = client.post(
        "/extract", json={"text": "some posting"}, headers={"X-API-Key": "wrong-key"}
    )
    assert response.status_code == 401


def test_extract_rejects_oversized_text():
    response = client.post(
        "/extract", json={"text": "x" * 20001}, headers=VALID_AUTH_HEADERS
    )
    assert response.status_code == 422


def test_extract_sends_untrusted_data_system_message():
    with patch("main.client.chat.completions.create", return_value=SAMPLE_POSTING) as mock_create:
        client.post(
            "/extract",
            json={"text": "Senior Backend Engineer, remote, $140k-175k"},
            headers=VALID_AUTH_HEADERS,
        )

    messages = mock_create.call_args.kwargs["messages"]
    system_messages = [m["content"] for m in messages if m["role"] == "system"]
    assert len(system_messages) == 1
    assert "untrusted" in system_messages[0].lower()
