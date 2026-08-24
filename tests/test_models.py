import pytest
from pydantic import ValidationError

from models import JobPosting


def test_minimal_valid_posting_defaults_salary_fields_to_none():
    posting = JobPosting(
        title="Backend Engineer",
        seniority="Mid",
        skills=["Python"],
        location="Remote",
        remote=True,
    )

    assert posting.salary_min is None
    assert posting.salary_max is None
    assert posting.salary_period is None
    assert posting.currency is None


def test_full_posting_round_trips_through_json():
    posting = JobPosting(
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

    reloaded = JobPosting.model_validate_json(posting.model_dump_json())
    assert reloaded == posting


@pytest.mark.parametrize("period", ["hourly", "weekly", "project", "annual"])
def test_salary_period_accepts_each_valid_value(period):
    posting = JobPosting(
        title="Contractor",
        seniority="Mid",
        skills=[],
        location="Remote",
        remote=True,
        salary_period=period,
    )
    assert posting.salary_period == period


def test_salary_period_rejects_invalid_value():
    with pytest.raises(ValidationError):
        JobPosting(
            title="Contractor",
            seniority="Mid",
            skills=[],
            location="Remote",
            remote=True,
            salary_period="monthly",
        )


def test_missing_required_field_raises_validation_error():
    with pytest.raises(ValidationError):
        JobPosting(seniority="Mid", skills=[], location="Remote", remote=True)
