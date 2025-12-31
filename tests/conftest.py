"""Pytest configuration and fixtures."""

import os
import pytest
from typing import Generator


@pytest.fixture
def mock_env_vars(monkeypatch) -> Generator[dict, None, None]:
    """Mock environment variables for testing."""
    env_vars = {
        "AWS_REGION": "us-east-1",
        "BEDROCK_KNOWLEDGE_BASE_ID": "test-kb-id-12345",
        "AWS_ACCESS_KEY_ID": "test-access-key",
        "AWS_SECRET_ACCESS_KEY": "test-secret-key",
    }

    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    yield env_vars

    # Cleanup
    for key in env_vars.keys():
        monkeypatch.delenv(key, raising=False)


@pytest.fixture
def clean_env(monkeypatch) -> None:
    """Remove all relevant environment variables for testing."""
    env_keys = [
        "AWS_REGION",
        "BEDROCK_KNOWLEDGE_BASE_ID",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
    ]

    for key in env_keys:
        monkeypatch.delenv(key, raising=False)
