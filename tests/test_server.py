"""Tests for MCP server."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.models import JobOpeningResult, JobOpeningsResponse


@pytest.fixture
def reset_bedrock_client():
    """Reset the global bedrock client before each test."""
    import src.server
    src.server._bedrock_client = None
    yield
    src.server._bedrock_client = None


@pytest.fixture
def mock_bedrock_client():
    """Mock BedrockClient class."""
    with patch("src.server.BedrockClient") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def sample_job_results():
    """Sample job opening results."""
    return JobOpeningsResponse(
        results=[
            JobOpeningResult(
                content="Software Engineer - Remote position",
                score=0.95,
                metadata={"job_id": "12345"},
            ),
            JobOpeningResult(
                content="Senior Data Scientist role",
                score=0.87,
                metadata={"job_id": "67890"},
            ),
        ],
        total_results=2,
    )


@pytest.mark.asyncio
async def test_get_job_openings_tool_exists(mock_env_vars):
    """Test that get_job_openings tool is registered."""
    from src.server import mcp

    # Get list of tools (async in FastMCP, returns list directly)
    tools = await mcp.list_tools()
    tool_names = [tool.name for tool in tools]

    assert "get_job_openings" in tool_names


@pytest.mark.asyncio
async def test_get_job_openings_tool_has_description(mock_env_vars):
    """Test that get_job_openings tool has proper description."""
    from src.server import mcp

    tools = await mcp.list_tools()
    job_tool = next(t for t in tools if t.name == "get_job_openings")

    assert job_tool.description is not None
    assert len(job_tool.description) > 0
    assert "job" in job_tool.description.lower()


@pytest.mark.asyncio
async def test_get_job_openings_tool_schema(mock_env_vars):
    """Test that get_job_openings tool has correct input schema."""
    from src.server import mcp

    tools = await mcp.list_tools()
    job_tool = next(t for t in tools if t.name == "get_job_openings")

    # Check input schema has required fields
    schema = job_tool.inputSchema
    assert "properties" in schema
    assert "query_text" in schema["properties"]
    assert schema["properties"]["query_text"]["type"] == "string"


@pytest.mark.asyncio
async def test_get_job_openings_success(
    mock_env_vars, reset_bedrock_client, mock_bedrock_client, sample_job_results
):
    """Test successful job openings retrieval."""
    from src.server import get_job_openings

    mock_bedrock_client.retrieve_job_openings.return_value = sample_job_results

    result = await get_job_openings(query_text="software engineer")

    # Verify bedrock client was called
    mock_bedrock_client.retrieve_job_openings.assert_called_once()
    call_args = mock_bedrock_client.retrieve_job_openings.call_args
    assert call_args.kwargs["query_text"] == "software engineer"
    assert call_args.kwargs["max_results"] == 10

    # Verify result format
    assert "Found 2 job opening" in result
    assert "Software Engineer - Remote position" in result
    assert "Senior Data Scientist role" in result


@pytest.mark.asyncio
async def test_get_job_openings_with_custom_max_results(
    mock_env_vars, reset_bedrock_client, mock_bedrock_client, sample_job_results
):
    """Test job openings retrieval with custom max_results."""
    from src.server import get_job_openings

    mock_bedrock_client.retrieve_job_openings.return_value = sample_job_results

    result = await get_job_openings(query_text="engineer", max_results=5)

    call_args = mock_bedrock_client.retrieve_job_openings.call_args
    assert call_args.kwargs["max_results"] == 5


@pytest.mark.asyncio
async def test_get_job_openings_no_results(mock_env_vars, reset_bedrock_client, mock_bedrock_client):
    """Test job openings retrieval with no results."""
    from src.server import get_job_openings

    empty_response = JobOpeningsResponse(results=[], total_results=0)
    mock_bedrock_client.retrieve_job_openings.return_value = empty_response

    result = await get_job_openings(query_text="nonexistent position")

    assert "No job openings found" in result


@pytest.mark.asyncio
async def test_get_job_openings_handles_errors(
    mock_env_vars, reset_bedrock_client, mock_bedrock_client
):
    """Test job openings retrieval handles errors gracefully."""
    from src.server import get_job_openings
    from src.bedrock_client import BedrockClientError

    mock_bedrock_client.retrieve_job_openings.side_effect = BedrockClientError(
        "Test error"
    )

    result = await get_job_openings(query_text="engineer")

    assert "failed" in result.lower()


@pytest.mark.asyncio
async def test_get_job_openings_includes_scores(
    mock_env_vars, reset_bedrock_client, mock_bedrock_client, sample_job_results
):
    """Test that results include relevance scores when available."""
    from src.server import get_job_openings

    mock_bedrock_client.retrieve_job_openings.return_value = sample_job_results

    result = await get_job_openings(query_text="engineer")

    # Check that scores are included in formatted output (95.0%)
    assert "95.0%" in result
    assert "87.0%" in result


@pytest.mark.asyncio
async def test_get_job_openings_includes_metadata(
    mock_env_vars, reset_bedrock_client, mock_bedrock_client, sample_job_results
):
    """Test that results include metadata when available."""
    from src.server import get_job_openings

    mock_bedrock_client.retrieve_job_openings.return_value = sample_job_results

    result = await get_job_openings(query_text="engineer")

    # Check that job IDs from metadata are included
    assert "12345" in result
    assert "67890" in result


def test_server_initialization(mock_env_vars):
    """Test that MCP server initializes correctly."""
    from src.server import mcp

    assert mcp is not None
    assert mcp.name == "talent8-bedrock"
