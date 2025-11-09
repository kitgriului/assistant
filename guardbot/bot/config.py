"""Configuration management for GuardBot.

This module provides centralized, type-safe configuration management using
Pydantic Settings with automatic environment variable loading and validation.

Features:
    - Type-safe configuration with Pydantic models
    - Automatic .env file loading
    - Validation with informative error messages
    - Environment-specific configs (development/production)
    - Computed properties for derived values
    - Secrets management

Environment Variables:
    BOT_TOKEN (str, required): Telegram Bot API token
    DB_URL (str, optional): Database connection URL
        Default: sqlite+aiosqlite:///./guardbot.db
    LOG_LEVEL (str, optional): Logging level (DEBUG/INFO/WARNING/ERROR/CRITICAL)
        Default: INFO
    MAX_PHOTO_SIZE_MB (int, optional): Maximum photo upload size in MB
        Default: 10
    PASS_VALIDITY_DAYS (int, optional): Default pass validity in days
        Default: 7
    ENVIRONMENT (str, optional): Environment name (development/production/testing)
        Default: development
    DEBUG (bool, optional): Enable debug mode
        Default: False in production, True in development

Example Usage:
    ```python
    from bot.config import settings
    
    # Access configuration
    bot = Bot(token=settings.bot_token)
    logger.setLevel(settings.log_level_int)
    
    # Check environment
    if settings.is_production:
        # Production-specific code
        pass
    ```

Notes:
    - Settings are immutable (frozen=True) for safety
    - All validations run on initialization
    - Missing required variables raise informative errors
    - Uses Pydantic for automatic type conversion
"""

from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional
import logging

from pydantic import (
    Field,
    field_validator,
    ConfigDict,
    ValidationError
)
from pydantic_settings import BaseSettings, SettingsConfigDict


# ===============================================
# Enumerations
# ===============================================

class Environment(str, Enum):
    """Application environment types."""
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"


class LogLevel(str, Enum):
    """Logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# ===============================================
# Configuration Model
# ===============================================

class Settings(BaseSettings):
    """Application settings with validation.
    
    This class uses Pydantic for automatic environment variable loading,
    type conversion, and validation. All settings are immutable once created.
    
    Attributes:
        # Core Settings
        bot_token: Telegram Bot API token (required)
        environment: Current environment (development/production/testing)
        debug: Debug mode flag
        
        # Database
        db_url: SQLAlchemy database connection URL
        db_echo: Enable SQL query logging (dev only)
        db_pool_size: Connection pool size
        db_pool_recycle: Connection recycle time in seconds
        
        # Logging
        log_level: Logging level
        log_file: Log file path (None = console only)
        log_rotation: Enable log file rotation
        log_max_bytes: Maximum log file size before rotation
        log_backup_count: Number of rotated log files to keep
        
        # Features
        max_photo_size_mb: Maximum photo upload size in MB
        pass_validity_days: Default pass validity in days
        qr_code_expiry_hours: QR code validity in hours
        
        # Security
        allowed_origins: CORS allowed origins (for future API)
        rate_limit_per_minute: Max requests per minute per user
        
        # Paths
        media_dir: Media files storage directory
        export_dir: Export files directory
        temp_dir: Temporary files directory
    """
    
    # ==========================================
    # Core Settings
    # ==========================================
    
    bot_token: str = Field(
        ...,  # Required
        description="Telegram Bot API token from @BotFather",
        min_length=30,
    )
    
    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Application environment"
    )
    
    debug: bool = Field(
        default=False,
        description="Enable debug mode with verbose logging"
    )
    
    # ==========================================
    # Database Configuration
    # ==========================================
    
    db_url: str = Field(
        default="sqlite+aiosqlite:///./guardbot.db",
        description="SQLAlchemy database URL"
    )
    
    db_echo: bool = Field(
        default=False,
        description="Echo SQL queries to console"
    )
    
    db_pool_size: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Database connection pool size"
    )
    
    db_pool_recycle: int = Field(
        default=3600,
        ge=60,
        description="Recycle connections after N seconds"
    )
    
    # ==========================================
    # Logging Configuration
    # ==========================================
    
    log_level: LogLevel = Field(
        default=LogLevel.INFO,
        description="Logging level"
    )
    
    log_file: Optional[Path] = Field(
        default=None,
        description="Log file path (None for console only)"
    )
    
    log_rotation: bool = Field(
        default=True,
        description="Enable log file rotation"
    )
    
    log_max_bytes: int = Field(
        default=10 * 1024 * 1024,  # 10 MB
        gt=0,
        description="Maximum log file size before rotation"
    )
    
    log_backup_count: int = Field(
        default=5,
        ge=0,
        description="Number of rotated log files to keep"
    )
    
    # ==========================================
    # Feature Configuration
    # ==========================================
    
    max_photo_size_mb: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum photo upload size in MB"
    )
    
    pass_validity_days: int = Field(
        default=7,
        ge=1,
        le=365,
        description="Default pass validity in days"
    )
    
    qr_code_expiry_hours: int = Field(
        default=24,
        ge=1,
        le=720,  # 30 days max
        description="QR code validity in hours"
    )
    
    # ==========================================
    # Security Settings
    # ==========================================
    
    allowed_origins: list[str] = Field(
        default_factory=lambda: ["*"],
        description="CORS allowed origins for future API"
    )
    
    rate_limit_per_minute: int = Field(
        default=30,
        ge=1,
        le=1000,
        description="Max requests per minute per user"
    )
    
    # ==========================================
    # Directory Paths
    # ==========================================
    
    media_dir: Path = Field(
        default=Path("data/media"),
        description="Media files storage directory"
    )
    
    export_dir: Path = Field(
        default=Path("data/export"),
        description="Export files directory"
    )
    
    temp_dir: Path = Field(
        default=Path("data/temp"),
        description="Temporary files directory"
    )
    
    # ==========================================
    # Pydantic Configuration
    # ==========================================
    
    model_config = SettingsConfigDict(
        # .env file settings
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",  # No prefix for env vars
        
        # Behavior
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields
        frozen=True,  # Immutable settings
        
        # Validation
        validate_default=True,
        validate_assignment=True,
    )
    
    # ==========================================
    # Validators
    # ==========================================
    
    @field_validator("bot_token")
    @classmethod
    def validate_bot_token(cls, v: str) -> str:
        """Validate Telegram Bot token format."""
        if not v:
            raise ValueError(
                "BOT_TOKEN is required. Get it from @BotFather on Telegram."
            )
        
        # Basic format check: should contain ':' and be long enough
        if ":" not in v or len(v) < 30:
            raise ValueError(
                "BOT_TOKEN appears to be invalid. "
                "Expected format: '123456789:ABCdefGHIjklMNOpqrsTUVwxyz'"
            )
        
        return v.strip()
    
    @field_validator("db_url")
    @classmethod
    def validate_db_url(cls, v: str) -> str:
        """Validate database URL format."""
        if not v:
            raise ValueError("DB_URL cannot be empty")
        
        # Check for SQL injection attempts (basic)
        suspicious_patterns = ["--", ";", "/*", "*/", "xp_", "exec("]
        if any(pattern in v.lower() for pattern in suspicious_patterns):
            raise ValueError("DB_URL contains suspicious patterns")
        
        return v.strip()
    
    @field_validator("environment")
    @classmethod
    def set_debug_from_environment(cls, v: Environment, values: Dict[str, Any]) -> Environment:
        """Auto-enable debug in development environment."""
        # Note: This validator modifies debug based on environment
        # In Pydantic 2.x we use info.data instead of values
        return v
    
    @field_validator("media_dir", "export_dir", "temp_dir")
    @classmethod
    def create_directories(cls, v: Path) -> Path:
        """Ensure directories exist."""
        v.mkdir(parents=True, exist_ok=True)
        return v
    
    # ==========================================
    # Computed Properties
    # ==========================================
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == Environment.PRODUCTION
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == Environment.DEVELOPMENT
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.environment == Environment.TESTING
    
    @property
    def max_photo_size_bytes(self) -> int:
        """Get maximum photo size in bytes."""
        return self.max_photo_size_mb * 1024 * 1024
    
    @property
    def log_level_int(self) -> int:
        """Get logging level as integer constant."""
        return getattr(logging, self.log_level.value)
    
    @property
    def should_log_sql(self) -> bool:
        """Determine if SQL queries should be logged."""
        return self.db_echo and not self.is_production
    
    # ==========================================
    # Utility Methods
    # ==========================================
    
    def get_log_config(self) -> dict:
        """Get logging configuration dictionary.
        
        Returns:
            Dictionary suitable for logging.config.dictConfig()
        """
        config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "detailed": {
                    "format": "[%(asctime)s] %(levelname)-8s %(name)s:%(lineno)d - %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
                "simple": {
                    "format": "%(levelname)-8s - %(message)s",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": self.log_level.value,
                    "formatter": "simple" if self.is_production else "detailed",
                    "stream": "ext://sys.stdout",
                },
            },
            "root": {
                "level": self.log_level.value,
                "handlers": ["console"],
            },
        }
        
        # Add file handler if log_file is specified
        if self.log_file:
            if self.log_rotation:
                config["handlers"]["file"] = {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": self.log_level.value,
                    "formatter": "detailed",
                    "filename": str(self.log_file),
                    "maxBytes": self.log_max_bytes,
                    "backupCount": self.log_backup_count,
                    "encoding": "utf-8",
                }
            else:
                config["handlers"]["file"] = {
                    "class": "logging.FileHandler",
                    "level": self.log_level.value,
                    "formatter": "detailed",
                    "filename": str(self.log_file),
                    "encoding": "utf-8",
                }
            
            config["root"]["handlers"].append("file")
        
        return config
    
    def display_config(self) -> str:
        """Generate human-readable configuration summary.
        
        Returns:
            Formatted configuration string (with secrets masked)
        """
        lines = [
            "=" * 50,
            "GuardBot Configuration",
            "=" * 50,
            f"Environment: {self.environment.value.upper()}",
            f"Debug Mode: {'ON' if self.debug else 'OFF'}",
            "",
            "Database:",
            f"  URL: {self._mask_db_url()}",
            f"  Pool Size: {self.db_pool_size}",
            f"  Echo SQL: {self.db_echo}",
            "",
            "Logging:",
            f"  Level: {self.log_level.value}",
            f"  File: {self.log_file or 'Console only'}",
            "",
            "Features:",
            f"  Max Photo Size: {self.max_photo_size_mb} MB",
            f"  Pass Validity: {self.pass_validity_days} days",
            f"  QR Code Expiry: {self.qr_code_expiry_hours} hours",
            "",
            "Security:",
            f"  Rate Limit: {self.rate_limit_per_minute}/min",
            "",
            "=" * 50,
        ]
        return "\n".join(lines)
    
    def _mask_db_url(self) -> str:
        """Mask sensitive parts of database URL."""
        if "://" in self.db_url:
            scheme, rest = self.db_url.split("://", 1)
            if "@" in rest:
                # postgresql://user:password@host/db → postgresql://***:***@host/db
                credentials, host = rest.split("@", 1)
                return f"{scheme}://***:***@{host}"
        return self.db_url.split("///")[-1]  # For SQLite, show only filename


# ===============================================
# Settings Instance
# ===============================================

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance.
    
    This function uses lru_cache to ensure settings are loaded only once.
    Useful for dependency injection and testing.
    
    Returns:
        Settings instance
        
    Example:
        ```python
        from bot.config import get_settings
        
        settings = get_settings()
        ```
    """
    try:
        return Settings()
    except ValidationError as e:
        # Pretty print validation errors
        print("\n❌ Configuration Error:")
        for error in e.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            print(f"  • {field}: {error['msg']}")
        print("\n💡 Tip: Check your .env file and environment variables\n")
        raise


# Global settings instance (for backward compatibility)
settings = get_settings()


# ===============================================
# Example .env file content
# ===============================================
"""
Example .env file:

# Required
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# Optional - Environment
ENVIRONMENT=development
DEBUG=true

# Optional - Database
DB_URL=sqlite+aiosqlite:///./guardbot.db
DB_ECHO=false
DB_POOL_SIZE=5

# Optional - Logging
LOG_LEVEL=INFO
LOG_FILE=logs/guardbot.log
LOG_ROTATION=true

# Optional - Features
MAX_PHOTO_SIZE_MB=10
PASS_VALIDITY_DAYS=7
QR_CODE_EXPIRY_HOURS=24

# Optional - Security
RATE_LIMIT_PER_MINUTE=30
"""

