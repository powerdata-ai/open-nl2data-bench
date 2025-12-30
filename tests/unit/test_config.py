"""Unit tests for configuration management module."""
import tempfile
from pathlib import Path

import pytest
import yaml

from onb.core.config import (
    ConfigLoader,
    DatabaseConfigModel,
    EndpointConfig,
    ResponseMappingConfig,
    Settings,
    SUTConfigModel,
    TestConfigModel,
    expand_env_vars,
)
from onb.core.exceptions import InvalidConfigError, MissingConfigError
from onb.core.types import DatabaseType, QualityLevel


class TestSettings:
    """Test Settings class."""

    def test_settings_defaults(self):
        """Test Settings default values."""
        settings = Settings()

        assert settings.DEBUG is False
        assert settings.LOG_LEVEL == "INFO"
        assert settings.DB_HOST == "localhost"
        assert settings.DB_PORT == 3306

    def test_settings_from_env(self, monkeypatch):
        """Test Settings loading from environment variables."""
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("DB_HOST", "testhost")
        monkeypatch.setenv("DB_PORT", "3307")

        settings = Settings()

        assert settings.DEBUG is True
        assert settings.DB_HOST == "testhost"
        assert settings.DB_PORT == 3307


class TestDatabaseConfigModel:
    """Test DatabaseConfigModel."""

    def test_database_config_creation(self):
        """Test creating DatabaseConfigModel instance."""
        config = DatabaseConfigModel(
            type=DatabaseType.MYSQL,
            host="localhost",
            port=3306,
            user="root",
            password="secret",
            database="test_db",
        )

        assert config.type == DatabaseType.MYSQL
        assert config.host == "localhost"
        assert config.password == "secret"

    def test_database_config_from_env(self):
        """Test creating DatabaseConfigModel from Settings."""
        settings = Settings(
            DB_HOST="testhost",
            DB_PORT=3307,
            DB_USER="testuser",
            DB_PASSWORD="testpass",
            DB_NAME="testdb",
        )

        config = DatabaseConfigModel.from_env(settings)

        assert config.host == "testhost"
        assert config.port == 3307
        assert config.user == "testuser"

    def test_database_config_ssl_default(self):
        """Test DatabaseConfigModel SSL default value."""
        config = DatabaseConfigModel(
            type=DatabaseType.MYSQL,
            host="localhost",
            port=3306,
            user="root",
            password="",
            database="test",
        )

        assert config.ssl is False


class TestEndpointConfig:
    """Test EndpointConfig model."""

    def test_endpoint_config_creation(self):
        """Test creating EndpointConfig instance."""
        config = EndpointConfig(
            url="https://api.example.com/nl2sql",
            method="POST",
            headers={"Authorization": "Bearer token"},
        )

        assert config.url == "https://api.example.com/nl2sql"
        assert config.method == "POST"
        assert "Authorization" in config.headers

    def test_endpoint_config_defaults(self):
        """Test EndpointConfig default values."""
        config = EndpointConfig(url="https://api.example.com")

        assert config.method == "POST"
        assert config.timeout_ms == 30000
        assert config.headers == {}


class TestResponseMappingConfig:
    """Test ResponseMappingConfig model."""

    def test_response_mapping_creation(self):
        """Test creating ResponseMappingConfig instance."""
        mapping = ResponseMappingConfig(
            generated_sql="$.data.sql",
            result_data="$.data.result",
        )

        assert mapping.generated_sql == "$.data.sql"
        assert mapping.result_data == "$.data.result"

    def test_response_mapping_with_aliases(self):
        """Test ResponseMappingConfig with field aliases."""
        mapping = ResponseMappingConfig(
            generated_sql="$.sql",
            result_data="$.result",
            **{"token_usage.total_tokens": "$.usage.total"}
        )

        assert mapping.token_usage_total == "$.usage.total"


class TestSUTConfigModel:
    """Test SUTConfigModel."""

    def test_sut_config_http_generic(self):
        """Test SUTConfigModel for HTTP generic adapter."""
        endpoint = EndpointConfig(url="https://api.example.com")
        mapping = ResponseMappingConfig(
            generated_sql="$.sql",
            result_data="$.result",
        )

        config = SUTConfigModel(
            name="TestSUT",
            type="http_generic",
            endpoint=endpoint,
            response_mapping=mapping,
        )

        assert config.name == "TestSUT"
        assert config.type == "http_generic"
        assert config.endpoint.url == "https://api.example.com"

    def test_sut_config_python_sdk(self):
        """Test SUTConfigModel for Python SDK adapter."""
        config = SUTConfigModel(
            name="MySUT",
            type="python_sdk",
            class_path="my_adapter.MyAdapter",
        )

        assert config.type == "python_sdk"
        assert config.class_path == "my_adapter.MyAdapter"

    def test_sut_config_invalid_type(self):
        """Test SUTConfigModel with invalid type."""
        with pytest.raises(ValueError, match="Invalid SUT type"):
            SUTConfigModel(
                name="BadSUT",
                type="invalid_type",
            )


class TestTestConfigModel:
    """Test TestConfigModel."""

    def test_test_config_defaults(self):
        """Test TestConfigModel default values."""
        config = TestConfigModel(domain="ecommerce")

        assert config.domain == "ecommerce"
        assert QualityLevel.HIGH in config.quality
        assert "L1" in config.complexity_levels

    def test_test_config_custom(self):
        """Test TestConfigModel with custom values."""
        config = TestConfigModel(
            domain="finance",
            quality=[QualityLevel.HIGH, QualityLevel.MEDIUM],
            complexity_levels=["L1", "L2", "L3", "L4"],
            warmup_runs=3,
            measurement_runs=7,
        )

        assert config.domain == "finance"
        assert len(config.quality) == 2
        assert len(config.complexity_levels) == 4
        assert config.warmup_runs == 3


class TestConfigLoader:
    """Test ConfigLoader class."""

    def test_load_yaml_success(self, tmp_path):
        """Test loading valid YAML file."""
        config_file = tmp_path / "test_config.yaml"
        config_data = {"database": {"type": "mysql", "host": "localhost"}}

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        data = ConfigLoader.load_yaml(config_file)

        assert data == config_data
        assert data["database"]["type"] == "mysql"

    def test_load_yaml_file_not_found(self, tmp_path):
        """Test loading non-existent YAML file."""
        config_file = tmp_path / "nonexistent.yaml"

        with pytest.raises(MissingConfigError, match="not found"):
            ConfigLoader.load_yaml(config_file)

    def test_load_yaml_invalid_yaml(self, tmp_path):
        """Test loading invalid YAML file."""
        config_file = tmp_path / "invalid.yaml"

        with open(config_file, "w") as f:
            f.write("invalid: yaml: content:")

        with pytest.raises(InvalidConfigError, match="Invalid YAML"):
            ConfigLoader.load_yaml(config_file)

    def test_load_yaml_empty_file(self, tmp_path):
        """Test loading empty YAML file."""
        config_file = tmp_path / "empty.yaml"
        config_file.touch()

        with pytest.raises(InvalidConfigError, match="Empty configuration"):
            ConfigLoader.load_yaml(config_file)

    def test_load_database_config(self, tmp_path):
        """Test loading database configuration."""
        config_file = tmp_path / "db_config.yaml"
        config_data = {
            "database": {
                "type": "mysql",
                "host": "localhost",
                "port": 3306,
                "user": "root",
                "password": "secret",
                "database": "test_db",
            }
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        db_config = ConfigLoader.load_database_config(config_file)

        assert db_config.type == DatabaseType.MYSQL
        assert db_config.host == "localhost"
        assert db_config.database == "test_db"

    def test_load_sut_config(self, tmp_path):
        """Test loading SUT configuration."""
        config_file = tmp_path / "sut_config.yaml"
        config_data = {
            "sut_adapter": {
                "name": "TestSUT",
                "type": "http_generic",
                "version": "1.0.0",
                "endpoint": {
                    "url": "https://api.test.com",
                    "method": "POST",
                },
                "response_mapping": {
                    "generated_sql": "$.sql",
                    "result_data": "$.result",
                },
            }
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        sut_config = ConfigLoader.load_sut_config(config_file)

        assert sut_config.name == "TestSUT"
        assert sut_config.type == "http_generic"
        assert sut_config.endpoint.url == "https://api.test.com"

    def test_load_test_config(self, tmp_path):
        """Test loading test configuration."""
        config_file = tmp_path / "test_config.yaml"
        config_data = {
            "test": {
                "domain": "ecommerce",
                "quality": ["high", "medium"],
                "complexity_levels": ["L1", "L2", "L3"],
            }
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        test_config = ConfigLoader.load_test_config(config_file)

        assert test_config.domain == "ecommerce"
        assert len(test_config.quality) == 2

    def test_load_test_config_defaults(self):
        """Test loading test configuration with defaults."""
        # Pass non-existent file
        test_config = ConfigLoader.load_test_config(Path("nonexistent.yaml"))

        assert test_config.domain == "ecommerce"
        assert QualityLevel.HIGH in test_config.quality


class TestExpandEnvVars:
    """Test expand_env_vars function."""

    def test_expand_simple_var(self, monkeypatch):
        """Test expanding simple environment variable."""
        monkeypatch.setenv("TEST_VAR", "test_value")

        config = {"key": "${TEST_VAR}"}
        result = expand_env_vars(config)

        assert result["key"] == "test_value"

    def test_expand_nested_dict(self, monkeypatch):
        """Test expanding environment variables in nested dict."""
        monkeypatch.setenv("HOST", "localhost")
        monkeypatch.setenv("PORT", "3306")

        config = {
            "database": {
                "host": "${HOST}",
                "port": "${PORT}",
            }
        }

        result = expand_env_vars(config)

        assert result["database"]["host"] == "localhost"
        assert result["database"]["port"] == "3306"

    def test_expand_in_list(self, monkeypatch):
        """Test expanding environment variables in list."""
        monkeypatch.setenv("VAR1", "value1")
        monkeypatch.setenv("VAR2", "value2")

        config = {"items": ["${VAR1}", "${VAR2}", "literal"]}

        result = expand_env_vars(config)

        assert result["items"][0] == "value1"
        assert result["items"][1] == "value2"
        assert result["items"][2] == "literal"

    def test_expand_missing_var(self):
        """Test expanding non-existent environment variable."""
        config = {"key": "${NONEXISTENT_VAR}"}
        result = expand_env_vars(config)

        # Should return original value if env var doesn't exist
        assert result["key"] == "${NONEXISTENT_VAR}"

    def test_expand_non_env_string(self):
        """Test that non-env strings are not modified."""
        config = {
            "url": "https://api.example.com",
            "value": 123,
            "flag": True,
        }

        result = expand_env_vars(config)

        assert result["url"] == "https://api.example.com"
        assert result["value"] == 123
        assert result["flag"] is True
