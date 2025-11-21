"""Tests for configuration module."""

import pytest
from pathlib import Path

from src.config import Config


def test_config_validation():
    """Test configuration validation."""
    config = Config(
        bot_token="test_token",
        openai_api_key="test_key",
        temp_dir=Path("/tmp"),
        max_file_size_mb=20,
        gpt_temperature=0.7,
        log_level="INFO"
    )
    
    # Should not raise
    config.validate()


def test_config_invalid_temperature():
    """Test invalid temperature validation."""
    config = Config(
        bot_token="test_token",
        openai_api_key="test_key",
        temp_dir=Path("/tmp"),
        gpt_temperature=3.0,  # Invalid
    )
    
    with pytest.raises(ValueError, match="gpt_temperature"):
        config.validate()


def test_config_invalid_log_level():
    """Test invalid log level validation."""
    config = Config(
        bot_token="test_token",
        openai_api_key="test_key",
        temp_dir=Path("/tmp"),
        log_level="INVALID"
    )
    
    with pytest.raises(ValueError, match="log_level"):
        config.validate()
