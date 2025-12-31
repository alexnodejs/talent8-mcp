"""Data models for Talent8 MCP Server."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class JobOpeningQuery(BaseModel):
    """Query parameters for job opening search."""

    query_text: str = Field(
        ...,
        min_length=1,
        description="Search query text for job openings",
    )
    max_results: int = Field(
        default=10,
        gt=0,
        le=100,
        description="Maximum number of results to return",
    )


class SourceMetadata(BaseModel):
    """Metadata about the source of a retrieved result."""

    type: str = Field(..., description="Type of source (S3, WEB, etc.)")
    s3_location: Optional[Dict[str, Any]] = Field(
        default=None,
        description="S3 location information if type is S3",
    )
    web_location: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Web location information if type is WEB",
    )


class JobOpeningResult(BaseModel):
    """A single job opening result from the knowledge base."""

    content: str = Field(..., description="The job opening content/description")
    score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Relevance score (0-1)",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the job opening",
    )
    source: Optional[SourceMetadata] = Field(
        default=None,
        description="Source information for the job opening",
    )


class JobOpeningsResponse(BaseModel):
    """Response containing multiple job opening results."""

    results: List[JobOpeningResult] = Field(
        default_factory=list,
        description="List of job opening results",
    )
    total_results: int = Field(
        default=0,
        ge=0,
        description="Total number of results returned",
    )

    @field_validator("total_results")
    @classmethod
    def validate_total_results(cls, v: int, info) -> int:
        """Ensure total_results matches the length of results list."""
        if "results" in info.data:
            return len(info.data["results"])
        return v
