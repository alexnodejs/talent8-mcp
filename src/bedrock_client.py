"""AWS Bedrock Knowledge Base client for job openings retrieval."""

import sys
from typing import Any, Dict

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from src.config import get_settings
from src.models import JobOpeningResult, JobOpeningsResponse, SourceMetadata


class BedrockClientError(Exception):
    """Custom exception for Bedrock client errors."""

    pass


class BedrockClient:
    """
    Client for interacting with AWS Bedrock Knowledge Base.

    This client uses the retrieve API (not retrieve_and_generate) for
    retrieval-only operations without generation.
    """

    def __init__(self):
        """Initialize the Bedrock client with configuration from settings."""
        self.settings = get_settings()
        self.knowledge_base_id = self.settings.bedrock_knowledge_base_id

        try:
            boto3_config = self.settings.get_boto3_config()
            self.client = boto3.client("bedrock-agent-runtime", **boto3_config)
            self._log(f"Initialized Bedrock client for KB: {self.knowledge_base_id}")
        except Exception as e:
            self._log(f"Failed to initialize Bedrock client: {str(e)}", level="ERROR")
            raise BedrockClientError(f"Failed to initialize Bedrock client: {str(e)}")

    def retrieve_job_openings(
        self, query_text: str, max_results: int = 10
    ) -> JobOpeningsResponse:
        """
        Retrieve job openings from the knowledge base using the retrieve API.

        Args:
            query_text: The search query for job openings
            max_results: Maximum number of results to return (default: 10)

        Returns:
            JobOpeningsResponse: Response containing job opening results

        Raises:
            BedrockClientError: If the retrieval fails
        """
        try:
            self._log(f"Retrieving job openings for query: '{query_text}'")

            response = self.client.retrieve(
                knowledgeBaseId=self.knowledge_base_id,
                retrievalQuery={"text": query_text},
                retrievalConfiguration={
                    "vectorSearchConfiguration": {"numberOfResults": max_results}
                },
            )

            retrieval_results = response.get("retrievalResults", [])
            self._log(f"Retrieved {len(retrieval_results)} results")

            # Parse results into our data models
            job_results = [
                self._parse_retrieve_result(result) for result in retrieval_results
            ]

            return JobOpeningsResponse(
                results=job_results,
                total_results=len(job_results),
            )

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            self._log(
                f"AWS ClientError during retrieval: {error_code} - {error_message}",
                level="ERROR",
            )
            raise BedrockClientError(
                f"AWS error during retrieval: {error_code} - {error_message}"
            )

        except BotoCoreError as e:
            self._log(f"BotoCoreError during retrieval: {str(e)}", level="ERROR")
            raise BedrockClientError(f"Failed to retrieve job openings: {str(e)}")

        except Exception as e:
            self._log(f"Unexpected error during retrieval: {str(e)}", level="ERROR")
            raise BedrockClientError(f"Unexpected error during retrieval: {str(e)}")

    def _parse_retrieve_result(self, result_data: Dict[str, Any]) -> JobOpeningResult:
        """
        Parse a single retrieve result into a JobOpeningResult model.

        Args:
            result_data: Raw result data from Bedrock retrieve API

        Returns:
            JobOpeningResult: Parsed job opening result
        """
        # Extract content (required field)
        content_data = result_data.get("content", {})
        content_text = content_data.get("text", "")

        # Extract score (optional)
        score = result_data.get("score")

        # Extract metadata (optional)
        metadata = result_data.get("metadata", {})

        # Extract and parse location/source (optional)
        source = None
        location_data = result_data.get("location")
        if location_data:
            source = self._parse_source_metadata(location_data)

        return JobOpeningResult(
            content=content_text,
            score=score,
            metadata=metadata,
            source=source,
        )

    def _parse_source_metadata(self, location_data: Dict[str, Any]) -> SourceMetadata:
        """
        Parse location data into SourceMetadata model.

        Args:
            location_data: Location data from Bedrock response

        Returns:
            SourceMetadata: Parsed source metadata
        """
        source_type = location_data.get("type", "UNKNOWN")
        s3_location = location_data.get("s3Location")
        web_location = location_data.get("webLocation")

        return SourceMetadata(
            type=source_type,
            s3_location=s3_location,
            web_location=web_location,
        )

    def _log(self, message: str, level: str = "INFO") -> None:
        """
        Log messages to stderr (required for MCP servers).

        Args:
            message: The message to log
            level: Log level (INFO, ERROR, etc.)
        """
        print(f"[BedrockClient] [{level}] {message}", file=sys.stderr)
