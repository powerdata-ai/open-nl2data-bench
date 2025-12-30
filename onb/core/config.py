"""
Configuration management for OpenNL2SQL-Bench.

This module provides type-safe configuration loading and validation using Pydantic.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings

from onb.core.exceptions import (
    ConfigError,
    InvalidConfigError,
    MissingConfigError,
)
from onb.core.types import DatabaseType, QualityLevel


# ============================================================================
# Environment Settings
# ============================================================================


class Settings(BaseSettings):
    """Global settings loaded from environment variables."""

    # General
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "onb_test"

    # SUT API
    SUT_API_KEY: Optional[str] = None
    SUT_API_URL: Optional[str] = None

    # Paths
    DATA_DIR: Path = Path("data")
    REPORT_DIR: Path = Path("data/reports")

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# ============================================================================
# Database Configuration
# ============================================================================


class DatabaseConfigModel(BaseModel):
    """Database connection configuration."""

    type: DatabaseType
    host: str
    port: int
    user: str
    password: str
    database: str
    ssl: bool = False
    connection_params: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_env(cls, settings: Settings) -> "DatabaseConfigModel":
        """Create from environment settings."""
        return cls(
            type=DatabaseType.MYSQL,
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME,
        )


# ============================================================================
# SUT Configuration
# ============================================================================


class EndpointConfig(BaseModel):
    """HTTP endpoint configuration."""

    url: str
    method: str = "POST"
    headers: Dict[str, str] = Field(default_factory=dict)
    timeout_ms: int = 30000


class ResponseMappingConfig(BaseModel):
    """JSONPath response field mappings."""

    success: Optional[str] = None
    generated_sql: str
    result_data: str
    token_usage_total: Optional[str] = Field(None, alias="token_usage.total_tokens")
    token_usage_input: Optional[str] = Field(None, alias="token_usage.input_tokens")
    token_usage_output: Optional[str] = Field(None, alias="token_usage.output_tokens")
    timing_nl2sql: Optional[str] = Field(None, alias="timing_breakdown.nl2sql_time_ms")
    timing_sql_gen: Optional[str] = Field(
        None, alias="timing_breakdown.sql_generation_time_ms"
    )
    timing_sql_exec: Optional[str] = Field(
        None, alias="timing_breakdown.sql_execution_time_ms"
    )
    error_message: Optional[str] = Field(None, alias="error.message")
    error_code: Optional[str] = Field(None, alias="error.code")

    class Config:
        """Pydantic configuration."""

        populate_by_name = True


class SUTConfigModel(BaseModel):
    """SUT (System Under Test) configuration."""

    name: str
    type: str  # "rest_api", "python_sdk", "http_generic"
    version: str = "1.0.0"

    # HTTP generic adapter config
    endpoint: Optional[EndpointConfig] = None
    response_mapping: Optional[ResponseMappingConfig] = None

    # Python SDK adapter config
    class_path: Optional[str] = Field(None, alias="class")

    # General config
    config: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Validate SUT type."""
        valid_types = ["rest_api", "python_sdk", "http_generic"]
        if v not in valid_types:
            raise ValueError(f"Invalid SUT type: {v}. Must be one of {valid_types}")
        return v

    class Config:
        """Pydantic configuration."""

        populate_by_name = True


# ============================================================================
# Test Configuration
# ============================================================================


class TestConfigModel(BaseModel):
    """Test execution configuration."""

    domain: str
    quality: List[QualityLevel] = Field(default=[QualityLevel.HIGH])
    complexity_levels: List[str] = Field(default=["L1", "L2", "L3"])

    # Performance profiling
    warmup_runs: int = 2
    measurement_runs: int = 5

    # Timeouts
    query_timeout_ms: int = 30000

    # Parallel execution
    max_workers: int = 1


# ============================================================================
# Configuration Loader
# ============================================================================


class ConfigLoader:
    """Configuration loader from YAML files."""

    @staticmethod
    def load_yaml(file_path: Path) -> Dict[str, Any]:
        """Load YAML file."""
        if not file_path.exists():
            raise MissingConfigError(f"Configuration file not found: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data is None:
                    raise InvalidConfigError(f"Empty configuration file: {file_path}")
                return data
        except yaml.YAMLError as e:
            raise InvalidConfigError(f"Invalid YAML in {file_path}: {e}")
        except (InvalidConfigError, MissingConfigError):
            # Re-raise config errors without wrapping
            raise
        except Exception as e:
            raise ConfigError(f"Failed to load configuration from {file_path}: {e}")

    @classmethod
    def load_database_config(cls, file_path: Path) -> DatabaseConfigModel:
        """Load database configuration."""
        data = cls.load_yaml(file_path)
        try:
            return DatabaseConfigModel(**data.get("database", {}))
        except Exception as e:
            raise InvalidConfigError(f"Invalid database configuration: {e}")

    @classmethod
    def load_sut_config(cls, file_path: Path) -> SUTConfigModel:
        """Load SUT configuration."""
        data = cls.load_yaml(file_path)
        try:
            sut_data = data.get("sut_adapter", {})
            return SUTConfigModel(**sut_data)
        except Exception as e:
            raise InvalidConfigError(f"Invalid SUT configuration: {e}")

    @classmethod
    def load_test_config(cls, file_path: Optional[Path] = None) -> TestConfigModel:
        """Load test configuration."""
        if file_path is None or not file_path.exists():
            return TestConfigModel(domain="ecommerce")

        data = cls.load_yaml(file_path)
        try:
            return TestConfigModel(**data.get("test", {}))
        except Exception as e:
            raise InvalidConfigError(f"Invalid test configuration: {e}")


# ============================================================================
# Helper Functions
# ============================================================================


def load_settings() -> Settings:
    """Load global settings from environment."""
    return Settings()


def expand_env_vars(config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively expand environment variables in config dict.

    Supports ${VAR_NAME} syntax, including multiple variables in a single string.
    Examples:
        - "${VAR}" -> expanded value
        - "${VAR1}/${VAR2}" -> "value1/value2"
        - "prefix_${VAR}_suffix" -> "prefix_value_suffix"
    """
    import re

    def expand(value: Any) -> Any:
        if isinstance(value, str):
            # Pattern to match ${VAR_NAME}
            pattern = r'\$\{([^}]+)\}'

            def replace_var(match):
                var_name = match.group(1)
                return os.getenv(var_name, match.group(0))  # Keep original if not found

            # Replace all ${VAR} patterns in the string
            expanded = re.sub(pattern, replace_var, value)
            return expanded
        elif isinstance(value, dict):
            return {k: expand(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [expand(item) for item in value]
        return value

    return expand(config_dict)
