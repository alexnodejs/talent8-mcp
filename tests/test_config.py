"""Tests for configuration module."""

import pytest
from pydantic import ValidationError


def test_config_loads_from_environment(mock_env_vars):
    """Test that configuration loads successfully from environment variables."""
    from src.config import Settings

    settings = Settings()

    assert settings.aws_region == "us-east-1"
    assert settings.bedrock_knowledge_base_id == "test-kb-id-12345"
    assert settings.aws_access_key_id == "test-access-key"
    assert settings.aws_secret_access_key == "test-secret-key"


def test_config_requires_knowledge_base_id(monkeypatch, clean_env):
    """Test that configuration raises error when BEDROCK_KNOWLEDGE_BASE_ID is missing."""
    from src.config import Settings

    monkeypatch.setenv("AWS_REGION", "us-east-1")

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)

    assert "bedrock_knowledge_base_id" in str(exc_info.value).lower()


def test_config_requires_aws_region(monkeypatch, clean_env):
    """Test that configuration raises error when AWS_REGION is missing."""
    from src.config import Settings

    monkeypatch.setenv("BEDROCK_KNOWLEDGE_BASE_ID", "test-kb-id")

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)

    assert "aws_region" in str(exc_info.value).lower()


def test_config_aws_credentials_optional(monkeypatch, clean_env):
    """Test that AWS credentials are optional (can use IAM roles)."""
    from src.config import Settings

    monkeypatch.setenv("AWS_REGION", "us-west-2")
    monkeypatch.setenv("BEDROCK_KNOWLEDGE_BASE_ID", "test-kb-id")

    settings = Settings()

    assert settings.aws_region == "us-west-2"
    assert settings.bedrock_knowledge_base_id == "test-kb-id"
    assert settings.aws_access_key_id is None
    assert settings.aws_secret_access_key is None


def test_config_get_boto3_config(mock_env_vars):
    """Test that get_boto3_config returns correct dictionary for boto3 client."""
    from src.config import Settings

    settings = Settings()
    boto3_config = settings.get_boto3_config()

    assert boto3_config["region_name"] == "us-east-1"
    assert boto3_config["aws_access_key_id"] == "test-access-key"
    assert boto3_config["aws_secret_access_key"] == "test-secret-key"


def test_config_get_boto3_config_without_credentials(monkeypatch, clean_env):
    """Test that get_boto3_config works without explicit credentials (IAM roles)."""
    from src.config import Settings

    monkeypatch.setenv("AWS_REGION", "eu-west-1")
    monkeypatch.setenv("BEDROCK_KNOWLEDGE_BASE_ID", "test-kb-id")

    settings = Settings()
    boto3_config = settings.get_boto3_config()

    assert boto3_config["region_name"] == "eu-west-1"
    assert "aws_access_key_id" not in boto3_config
    assert "aws_secret_access_key" not in boto3_config


def test_config_singleton_pattern(mock_env_vars):
    """Test that get_settings returns the same instance."""
    from src.config import get_settings

    settings1 = get_settings()
    settings2 = get_settings()

    assert settings1 is settings2
