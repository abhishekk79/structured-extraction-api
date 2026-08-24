from unittest.mock import patch

from app import (
    RATE_LIMIT_MAX_CALLS,
    RATE_LIMIT_WINDOW_SECONDS,
    check_rate_limit,
    extract_posting,
    handle_submit,
)
from models import JobPosting

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


def test_check_rate_limit_allows_up_to_max_calls():
    ip = "1.1.1.1"
    for _ in range(RATE_LIMIT_MAX_CALLS):
        assert check_rate_limit(ip) is True


def test_check_rate_limit_blocks_call_over_max():
    ip = "2.2.2.2"
    for _ in range(RATE_LIMIT_MAX_CALLS):
        check_rate_limit(ip)
    assert check_rate_limit(ip) is False


def test_check_rate_limit_allows_again_after_window_expires():
    ip = "3.3.3.3"
    start = 1000.0
    for _ in range(RATE_LIMIT_MAX_CALLS):
        check_rate_limit(ip, now=start)
    assert check_rate_limit(ip, now=start + RATE_LIMIT_WINDOW_SECONDS + 1) is True


def test_check_rate_limit_tracks_ips_independently():
    for _ in range(RATE_LIMIT_MAX_CALLS):
        check_rate_limit("4.4.4.4")
    assert check_rate_limit("5.5.5.5") is True


def test_extract_posting_rejects_empty_text():
    result = extract_posting("", None, "6.6.6.6")
    assert "error" in result


def test_extract_posting_rejects_oversized_text():
    result = extract_posting("x" * 20001, None, "7.7.7.7")
    assert "error" in result


def test_extract_posting_uses_embedded_client_when_no_user_key():
    with patch(
        "app.embedded_client.chat.completions.create", return_value=SAMPLE_POSTING
    ) as mock_create:
        result = extract_posting("Senior Backend Engineer, remote", None, "8.8.8.8")

    mock_create.assert_called_once()
    assert result == SAMPLE_POSTING.model_dump()


def test_extract_posting_blocks_when_embedded_rate_limit_exceeded():
    ip = "9.9.9.9"
    for _ in range(RATE_LIMIT_MAX_CALLS):
        check_rate_limit(ip)

    with patch(
        "app.embedded_client.chat.completions.create", return_value=SAMPLE_POSTING
    ) as mock_create:
        result = extract_posting("some posting", None, ip)

    assert "error" in result
    mock_create.assert_not_called()


def test_extract_posting_with_user_key_bypasses_rate_limit():
    ip = "10.10.10.10"
    for _ in range(RATE_LIMIT_MAX_CALLS):
        check_rate_limit(ip)

    with patch("app.build_client") as mock_build_client:
        mock_build_client.return_value.chat.completions.create.return_value = SAMPLE_POSTING
        result = extract_posting("some posting", "user-supplied-key", ip)

    mock_build_client.assert_called_once_with("user-supplied-key")
    assert result == SAMPLE_POSTING.model_dump()


def test_extract_posting_returns_error_on_upstream_failure():
    with patch("app.embedded_client.chat.completions.create", side_effect=RuntimeError("boom")):
        result = extract_posting("some posting", None, "11.11.11.11")

    assert "error" in result


def test_handle_submit_treats_none_api_key_as_not_provided():
    with patch("app.extract_posting", return_value={"ok": True}) as mock_extract:
        handle_submit("some text", None, None)

    mock_extract.assert_called_once_with("some text", None, "unknown")


def test_handle_submit_treats_blank_api_key_as_not_provided():
    with patch("app.extract_posting", return_value={"ok": True}) as mock_extract:
        handle_submit("some text", "   ", None)

    mock_extract.assert_called_once_with("some text", None, "unknown")
