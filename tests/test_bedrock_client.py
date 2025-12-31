"""Tests for Bedrock client module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError, BotoCoreError


@pytest.fixture
def mock_bedrock_client():
    """Mock boto3 bedrock-agent-runtime client."""
    with patch("src.bedrock_client.boto3.client") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def sample_retrieve_response():
    """Sample response from Bedrock retrieve API."""
    return {
        "retrievalResults": [
            {
                "content": {"text": "Software Engineer - Remote position"},
                "score": 0.95,
                "location": {
                    "type": "S3",
                    "s3Location": {"uri": "s3://jobs/se.pdf"},
                },
                "metadata": {"job_id": "12345", "department": "Engineering"},
            },
            {
                "content": {"text": "Senior Data Scientist position"},
                "score": 0.87,
                "location": {
                    "type": "S3",
                    "s3Location": {"uri": "s3://jobs/ds.pdf"},
                },
                "metadata": {"job_id": "67890", "department": "Data"},
            },
        ],
        "ResponseMetadata": {"HTTPStatusCode": 200},
    }


def test_bedrock_client_initialization(mock_env_vars, mock_bedrock_client):
    """Test BedrockClient initializes correctly."""
    from src.bedrock_client import BedrockClient

    client = BedrockClient()

    assert client.knowledge_base_id == "test-kb-id-12345"
    assert client.client is not None


def test_retrieve_job_openings_success(
    mock_env_vars, mock_bedrock_client, sample_retrieve_response
):
    """Test successful retrieval of job openings."""
    from src.bedrock_client import BedrockClient

    mock_bedrock_client.retrieve.return_value = sample_retrieve_response

    client = BedrockClient()
    response = client.retrieve_job_openings("software engineer", max_results=10)

    # Verify boto3 client was called correctly
    mock_bedrock_client.retrieve.assert_called_once()
    call_kwargs = mock_bedrock_client.retrieve.call_args[1]
    assert call_kwargs["knowledgeBaseId"] == "test-kb-id-12345"
    assert call_kwargs["retrievalQuery"]["text"] == "software engineer"

    # Verify response structure
    assert response.total_results == 2
    assert len(response.results) == 2
    assert response.results[0].content == "Software Engineer - Remote position"
    assert response.results[0].score == 0.95
    assert response.results[1].content == "Senior Data Scientist position"


def test_retrieve_job_openings_empty_results(mock_env_vars, mock_bedrock_client):
    """Test retrieval with no results."""
    from src.bedrock_client import BedrockClient

    mock_bedrock_client.retrieve.return_value = {
        "retrievalResults": [],
        "ResponseMetadata": {"HTTPStatusCode": 200},
    }

    client = BedrockClient()
    response = client.retrieve_job_openings("nonexistent position")

    assert response.total_results == 0
    assert response.results == []


def test_retrieve_job_openings_with_max_results(
    mock_env_vars, mock_bedrock_client, sample_retrieve_response
):
    """Test retrieval with custom max_results."""
    from src.bedrock_client import BedrockClient

    mock_bedrock_client.retrieve.return_value = sample_retrieve_response

    client = BedrockClient()
    client.retrieve_job_openings("engineer", max_results=5)

    call_kwargs = mock_bedrock_client.retrieve.call_args[1]
    assert call_kwargs["retrievalConfiguration"]["vectorSearchConfiguration"]["numberOfResults"] == 5


def test_retrieve_job_openings_client_error(mock_env_vars, mock_bedrock_client):
    """Test handling of AWS ClientError."""
    from src.bedrock_client import BedrockClient, BedrockClientError

    mock_bedrock_client.retrieve.side_effect = ClientError(
        {"Error": {"Code": "ValidationException", "Message": "Invalid KB ID"}},
        "retrieve",
    )

    client = BedrockClient()

    with pytest.raises(BedrockClientError) as exc_info:
        client.retrieve_job_openings("software engineer")

    assert "ValidationException" in str(exc_info.value)


def test_retrieve_job_openings_network_error(mock_env_vars, mock_bedrock_client):
    """Test handling of network errors."""
    from src.bedrock_client import BedrockClient, BedrockClientError

    mock_bedrock_client.retrieve.side_effect = BotoCoreError()

    client = BedrockClient()

    with pytest.raises(BedrockClientError) as exc_info:
        client.retrieve_job_openings("software engineer")

    assert "Failed to retrieve job openings" in str(exc_info.value)


def test_retrieve_job_openings_handles_missing_fields(mock_env_vars, mock_bedrock_client):
    """Test handling of response with missing optional fields."""
    from src.bedrock_client import BedrockClient

    # Response with minimal fields
    mock_bedrock_client.retrieve.return_value = {
        "retrievalResults": [
            {
                "content": {"text": "Minimal job posting"},
                # No score, location, or metadata
            }
        ],
        "ResponseMetadata": {"HTTPStatusCode": 200},
    }

    client = BedrockClient()
    response = client.retrieve_job_openings("engineer")

    assert response.total_results == 1
    assert response.results[0].content == "Minimal job posting"
    assert response.results[0].score is None
    assert response.results[0].metadata == {}
    assert response.results[0].source is None


def test_parse_retrieve_result_with_complete_data(mock_env_vars):
    """Test parsing of complete retrieve result."""
    from src.bedrock_client import BedrockClient

    client = BedrockClient()
    result_data = {
        "content": {"text": "Job description"},
        "score": 0.9,
        "location": {
            "type": "S3",
            "s3Location": {"uri": "s3://bucket/key"},
        },
        "metadata": {"key": "value"},
    }

    result = client._parse_retrieve_result(result_data)

    assert result.content == "Job description"
    assert result.score == 0.9
    assert result.metadata == {"key": "value"}
    assert result.source.type == "S3"
    assert result.source.s3_location == {"uri": "s3://bucket/key"}
