"""Tests for data models."""

import pytest
from pydantic import ValidationError


def test_job_opening_query_valid():
    """Test JobOpeningQuery model with valid data."""
    from src.models import JobOpeningQuery

    query = JobOpeningQuery(query_text="software engineer positions")

    assert query.query_text == "software engineer positions"
    assert query.max_results == 10  # Default value


def test_job_opening_query_custom_max_results():
    """Test JobOpeningQuery with custom max_results."""
    from src.models import JobOpeningQuery

    query = JobOpeningQuery(query_text="data scientist", max_results=20)

    assert query.query_text == "data scientist"
    assert query.max_results == 20


def test_job_opening_query_requires_text():
    """Test that JobOpeningQuery requires query_text."""
    from src.models import JobOpeningQuery

    with pytest.raises(ValidationError) as exc_info:
        JobOpeningQuery()

    assert "query_text" in str(exc_info.value)


def test_job_opening_query_empty_text_fails():
    """Test that JobOpeningQuery rejects empty query_text."""
    from src.models import JobOpeningQuery

    with pytest.raises(ValidationError):
        JobOpeningQuery(query_text="")


def test_job_opening_query_max_results_positive():
    """Test that max_results must be positive."""
    from src.models import JobOpeningQuery

    with pytest.raises(ValidationError):
        JobOpeningQuery(query_text="engineer", max_results=0)

    with pytest.raises(ValidationError):
        JobOpeningQuery(query_text="engineer", max_results=-1)


def test_source_metadata_valid():
    """Test SourceMetadata model with valid data."""
    from src.models import SourceMetadata

    metadata = SourceMetadata(
        type="S3",
        s3_location={"uri": "s3://bucket/key.pdf"},
    )

    assert metadata.type == "S3"
    assert metadata.s3_location == {"uri": "s3://bucket/key.pdf"}
    assert metadata.web_location is None


def test_source_metadata_web_location():
    """Test SourceMetadata with web location."""
    from src.models import SourceMetadata

    metadata = SourceMetadata(
        type="WEB",
        web_location={"url": "https://example.com/job"},
    )

    assert metadata.type == "WEB"
    assert metadata.web_location == {"url": "https://example.com/job"}
    assert metadata.s3_location is None


def test_job_opening_result_valid():
    """Test JobOpeningResult model with valid data."""
    from src.models import JobOpeningResult, SourceMetadata

    result = JobOpeningResult(
        content="Software Engineer - Remote position available",
        score=0.95,
        metadata={"job_id": "12345", "department": "Engineering"},
        source=SourceMetadata(
            type="S3",
            s3_location={"uri": "s3://jobs/position.pdf"},
        ),
    )

    assert result.content == "Software Engineer - Remote position available"
    assert result.score == 0.95
    assert result.metadata["job_id"] == "12345"
    assert result.source.type == "S3"


def test_job_opening_result_optional_fields():
    """Test JobOpeningResult with only required fields."""
    from src.models import JobOpeningResult

    result = JobOpeningResult(content="Job description")

    assert result.content == "Job description"
    assert result.score is None
    assert result.metadata == {}
    assert result.source is None


def test_job_openings_response_valid():
    """Test JobOpeningsResponse model with multiple results."""
    from src.models import JobOpeningResult, JobOpeningsResponse

    results = [
        JobOpeningResult(content="Job 1", score=0.9),
        JobOpeningResult(content="Job 2", score=0.8),
    ]

    response = JobOpeningsResponse(
        results=results,
        total_results=2,
    )

    assert len(response.results) == 2
    assert response.total_results == 2
    assert response.results[0].content == "Job 1"


def test_job_openings_response_empty():
    """Test JobOpeningsResponse with no results."""
    from src.models import JobOpeningsResponse

    response = JobOpeningsResponse(results=[], total_results=0)

    assert response.results == []
    assert response.total_results == 0
