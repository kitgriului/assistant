"""
Configuration management for Whisper Bot.
Loads and validates environment variables.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    """Application configuration."""
    
    # Bot configuration
    bot_token: str
    openai_api_key: str
    
    # File handling
    temp_dir: Path
    max_file_size_mb: int = 20
    
    # Whisper settings
    whisper_model: str = "whisper-1"
    
    # GPT settings
    gpt_model: str = "gpt-4o-mini"
    gpt_temperature: float = 0.7
    
    # Calendar settings
    calendar_enabled: bool = True
    calendar_timezone: str = "Europe/Moscow"
    
    # Logging
    log_level: str = "INFO"
    
    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> "Config":
        """
        Load configuration from environment variables.
        
        Args:
            env_file: Path to .env file (optional)
            
        Returns:
            Config instance
            
        Raises:
            ValueError: If required variables are missing
        """
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()
        
        # Required variables
        bot_token = os.getenv("BOT_TOKEN", "").strip()
        if not bot_token:
            raise ValueError("BOT_TOKEN is not set in environment")
        
        openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY is not set in environment")
        
        # Optional variables with defaults
        temp_dir = Path(os.getenv("TEMP_DIR", "/tmp"))
        max_file_size_mb = int(os.getenv("MAX_FILE_SIZE_MB", "20"))
        whisper_model = os.getenv("WHISPER_MODEL", "whisper-1")
        gpt_model = os.getenv("GPT_MODEL", "gpt-4o-mini")
        gpt_temperature = float(os.getenv("GPT_TEMPERATURE", "0.7"))
        calendar_enabled = os.getenv("CALENDAR_ENABLED", "true").lower() == "true"
        calendar_timezone = os.getenv("CALENDAR_TIMEZONE", "Europe/Moscow")
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        
        return cls(
            bot_token=bot_token,
            openai_api_key=openai_api_key,
            temp_dir=temp_dir,
            max_file_size_mb=max_file_size_mb,
            whisper_model=whisper_model,
            gpt_model=gpt_model,
            gpt_temperature=gpt_temperature,
            calendar_enabled=calendar_enabled,
            calendar_timezone=calendar_timezone,
            log_level=log_level,
        )
    
    def validate(self) -> None:
        """Validate configuration values."""
        if self.max_file_size_mb <= 0:
            raise ValueError("max_file_size_mb must be positive")
        
        if not 0 <= self.gpt_temperature <= 2:
            raise ValueError("gpt_temperature must be between 0 and 2")
        
        if self.log_level not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
            raise ValueError(f"Invalid log_level: {self.log_level}")
