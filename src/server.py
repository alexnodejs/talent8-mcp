"""Talent8 MCP Server for AWS Bedrock Knowledge Base job openings."""

import sys
from typing import Optional

from mcp.server.fastmcp import FastMCP

from src.bedrock_client import BedrockClient, BedrockClientError
from src.models import JobOpeningQuery

# Initialize MCP server
mcp = FastMCP("talent8-bedrock")

# Initialize Bedrock client (will be created once on first use)
_bedrock_client: Optional[BedrockClient] = None


def get_bedrock_client() -> BedrockClient:
    """
    Get or create the Bedrock client instance (singleton pattern).

    Returns:
        BedrockClient: The Bedrock client instance
    """
    global _bedrock_client
    if _bedrock_client is None:
        _bedrock_client = BedrockClient()
    return _bedrock_client


@mcp.tool()
async def get_job_openings(
    query_text: str,
    max_results: int = 10,
) -> str:
    """
    Retrieve job openings from AWS Bedrock Knowledge Base.

    This tool searches the knowledge base for job openings matching the query
    and returns detailed information including job descriptions, relevance scores,
    and metadata.

    Args:
        query_text: Search query for job openings (e.g., "software engineer", "data scientist")
        max_results: Maximum number of results to return (default: 10, max: 100)

    Returns:
        str: Formatted string containing job opening results with scores and metadata
    """
    try:
        # Validate input using Pydantic model
        query = JobOpeningQuery(query_text=query_text, max_results=max_results)

        _log(f"Processing query: '{query.query_text}' (max_results={query.max_results})")

        # Get Bedrock client and retrieve results
        client = get_bedrock_client()
        response = client.retrieve_job_openings(
            query_text=query.query_text,
            max_results=query.max_results,
        )

        # Format response for display
        return _format_job_openings_response(response)

    except BedrockClientError as e:
        _log(f"Error retrieving job openings: {str(e)}", level="ERROR")
        return "Failed to retrieve job openings. Please try again later."

    except Exception as e:
        _log(f"Unexpected error: {str(e)}", level="ERROR")
        return "An unexpected error occurred. Please try again later."


def _format_job_openings_response(response) -> str:
    """
    Format job openings response into a human-readable string.

    Args:
        response: JobOpeningsResponse object

    Returns:
        str: Formatted string with job opening details
    """
    if response.total_results == 0:
        return "No job openings found matching your query."

    lines = [f"Found {response.total_results} job opening(s):\n"]

    for idx, result in enumerate(response.results, start=1):
        lines.append(f"\n--- Job Opening #{idx} ---")

        # Add relevance score if available
        if result.score is not None:
            score_pct = result.score * 100
            lines.append(f"Relevance Score: {score_pct:.1f}%")

        # Add content
        lines.append(f"\n{result.content}")

        # Add metadata if available
        if result.metadata:
            lines.append("\nMetadata:")
            for key, value in result.metadata.items():
                lines.append(f"  - {key}: {value}")

        # Add source information if available
        if result.source:
            lines.append(f"\nSource Type: {result.source.type}")
            if result.source.s3_location:
                uri = result.source.s3_location.get("uri", "N/A")
                lines.append(f"Location: {uri}")
            elif result.source.web_location:
                url = result.source.web_location.get("url", "N/A")
                lines.append(f"URL: {url}")

        lines.append("")  # Empty line between results

    return "\n".join(lines)


def _log(message: str, level: str = "INFO") -> None:
    """
    Log messages to stderr (required for MCP servers).

    Args:
        message: The message to log
        level: Log level (INFO, ERROR, etc.)
    """
    print(f"[MCP Server] [{level}] {message}", file=sys.stderr)


if __name__ == "__main__":
    _log("Starting Talent8 MCP Server for AWS Bedrock")
    mcp.run()
