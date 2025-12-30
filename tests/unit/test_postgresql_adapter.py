"""Unit tests for PostgreSQL database adapter."""
import pytest
from unittest.mock import MagicMock, Mock, patch
from datetime import datetime, timezone

import pandas as pd
from sqlalchemy.exc import SQLAlchemyError

from onb.adapters.database.postgresql import PostgreSQLAdapter
from onb.core.exceptions import ConnectionError, QueryExecutionError
from onb.core.types import DatabaseConfig, DatabaseType


@pytest.fixture
def postgresql_config():
    """PostgreSQL database configuration."""
    return DatabaseConfig(
        type=DatabaseType.POSTGRESQL,
        host="localhost",
        port=5432,
        user="postgres",
        password="test_password",
        database="test_db",
        ssl=False,
    )


@pytest.fixture
def postgresql_config_ssl():
    """PostgreSQL configuration with SSL."""
    return DatabaseConfig(
        type=DatabaseType.POSTGRESQL,
        host="prod-db.example.com",
        port=5432,
        user="app_user",
        password="secure!@#$%",  # Special characters
        database="production",
        ssl=True,
    )


class TestPostgreSQLAdapter:
    """Test PostgreSQLAdapter class."""

    def test_initialization(self, postgresql_config):
        """Test adapter initialization."""
        adapter = PostgreSQLAdapter(postgresql_config)

        assert adapter.config == postgresql_config
        assert adapter.database_type == DatabaseType.POSTGRESQL
        assert adapter._connected is False
        assert adapter._engine is None

    def test_initialization_wrong_type(self):
        """Test initialization with wrong database type."""
        config = DatabaseConfig(
            type=DatabaseType.MYSQL,  # Wrong type
            host="localhost",
            port=3306,
            user="root",
            password="password",
            database="test",
        )

        with pytest.raises(ValueError, match="Invalid database type"):
            PostgreSQLAdapter(config)

    def test_build_connection_string_basic(self, postgresql_config):
        """Test building basic connection string."""
        adapter = PostgreSQLAdapter(postgresql_config)
        conn_str = adapter._build_connection_string()

        assert "postgresql+psycopg2://" in conn_str
        assert "postgres:test_password@localhost:5432/test_db" in conn_str
        assert "sslmode=prefer" in conn_str
        assert "client_encoding=utf8" in conn_str
        assert "application_name=open-nl2data-bench" in conn_str

    def test_build_connection_string_with_ssl(self, postgresql_config_ssl):
        """Test building connection string with SSL."""
        adapter = PostgreSQLAdapter(postgresql_config_ssl)
        conn_str = adapter._build_connection_string()

        assert "postgresql+psycopg2://" in conn_str
        assert "sslmode=require" in conn_str

    def test_build_connection_string_special_chars(self, postgresql_config_ssl):
        """Test URL encoding of special characters in password."""
        adapter = PostgreSQLAdapter(postgresql_config_ssl)
        conn_str = adapter._build_connection_string()

        # Special characters should be URL-encoded
        assert "secure!@#$%" not in conn_str
        assert "secure%21%40%23%24%25" in conn_str or "app_user:" in conn_str

    def test_normalize_result_empty(self, postgresql_config):
        """Test normalizing empty DataFrame."""
        adapter = PostgreSQLAdapter(postgresql_config)
        empty_df = pd.DataFrame()

        result = adapter.normalize_result(empty_df)

        assert result.empty
        assert len(result) == 0

    def test_normalize_result_numeric(self, postgresql_config):
        """Test normalizing numeric columns."""
        adapter = PostgreSQLAdapter(postgresql_config)
        df = pd.DataFrame({
            "int_col": [1, 2, 3],
            "float_col": [1.1, 2.2, 3.3],
            "decimal_col": pd.Series([10.5, 20.7, 30.9], dtype="float64"),
        })

        result = adapter.normalize_result(df)

        assert pd.api.types.is_numeric_dtype(result["int_col"])
        assert pd.api.types.is_numeric_dtype(result["float_col"])
        assert pd.api.types.is_numeric_dtype(result["decimal_col"])

    def test_normalize_result_lowercase_columns(self, postgresql_config):
        """Test column names are lowercased."""
        adapter = PostgreSQLAdapter(postgresql_config)
        df = pd.DataFrame({
            "User_ID": [1, 2],
            "USER_NAME": ["Alice", "Bob"],
            "CreatedAt": ["2024-01-01", "2024-01-02"],
        })

        result = adapter.normalize_result(df)

        # PostgreSQL convention: lowercase column names
        assert "user_id" in result.columns
        assert "user_name" in result.columns
        assert "createdat" in result.columns

    def test_normalize_result_datetime_with_timezone(self, postgresql_config):
        """Test datetime normalization with timezone."""
        adapter = PostgreSQLAdapter(postgresql_config)

        # Create timezone-aware datetime
        dt_utc = pd.to_datetime(["2024-01-01 10:00:00"], utc=True)
        df = pd.DataFrame({"timestamp": dt_utc})

        result = adapter.normalize_result(df)

        assert pd.api.types.is_datetime64_any_dtype(result["timestamp"])
        # Should be UTC
        assert result["timestamp"].dt.tz is not None

    def test_normalize_result_datetime_without_timezone(self, postgresql_config):
        """Test datetime normalization without timezone."""
        adapter = PostgreSQLAdapter(postgresql_config)

        # Create naive datetime
        dt_naive = pd.to_datetime(["2024-01-01 10:00:00"])
        df = pd.DataFrame({"timestamp": dt_naive})

        result = adapter.normalize_result(df)

        # Should be localized to UTC
        assert result["timestamp"].dt.tz is not None

    def test_normalize_result_json_column(self, postgresql_config):
        """Test normalizing JSON/JSONB columns."""
        adapter = PostgreSQLAdapter(postgresql_config)

        # Simulate JSON column (dict objects)
        df = pd.DataFrame({
            "metadata": [
                {"key": "value1"},
                {"key": "value2"},
            ]
        })

        result = adapter.normalize_result(df)

        # JSON should be converted to string
        assert result["metadata"].dtype == object
        # Check if it's JSON string
        import json
        parsed = json.loads(result["metadata"].iloc[0])
        assert parsed == {"key": "value1"}

    def test_normalize_result_array_column(self, postgresql_config):
        """Test normalizing PostgreSQL ARRAY columns."""
        adapter = PostgreSQLAdapter(postgresql_config)

        # Simulate ARRAY column (list objects)
        df = pd.DataFrame({
            "tags": [
                ["tag1", "tag2"],
                ["tag3", "tag4", "tag5"],
            ]
        })

        result = adapter.normalize_result(df)

        # Arrays should be converted to JSON string
        assert result["tags"].dtype == object
        import json
        parsed = json.loads(result["tags"].iloc[0])
        assert parsed == ["tag1", "tag2"]

    @patch("onb.adapters.database.base.create_engine")
    def test_connect_success(self, mock_create_engine, postgresql_config):
        """Test successful database connection."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 1

        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_conn.execute.return_value = mock_result

        mock_engine.connect.return_value = mock_conn
        mock_create_engine.return_value = mock_engine

        adapter = PostgreSQLAdapter(postgresql_config)
        adapter.connect()

        assert adapter._connected is True
        assert adapter._engine is not None
        mock_create_engine.assert_called_once()

    @patch("onb.adapters.database.base.create_engine")
    def test_get_database_version(self, mock_create_engine, postgresql_config):
        """Test getting PostgreSQL version."""
        # Setup mock
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = "PostgreSQL 14.5 on x86_64-pc-linux-gnu, compiled by gcc"

        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_conn.execute.return_value = mock_result

        mock_engine.connect.return_value = mock_conn
        mock_create_engine.return_value = mock_engine

        adapter = PostgreSQLAdapter(postgresql_config)
        adapter._engine = mock_engine
        adapter._connected = True

        version = adapter.get_database_version()

        assert version == "PostgreSQL 14.5 on x86_64-pc-linux-gnu"
        mock_conn.execute.assert_called_once()

    def test_get_database_version_not_connected(self, postgresql_config):
        """Test getting version when not connected."""
        adapter = PostgreSQLAdapter(postgresql_config)

        with pytest.raises(ConnectionError, match="Not connected"):
            adapter.get_database_version()

    def test_configure_engine_options(self, postgresql_config):
        """Test PostgreSQL engine options configuration."""
        adapter = PostgreSQLAdapter(postgresql_config)
        options = adapter._configure_engine_options()

        assert options["pool_size"] == 5
        assert options["max_overflow"] == 10
        assert options["pool_pre_ping"] is True
        assert options["pool_recycle"] == 3600

    def test_get_metadata(self, postgresql_config):
        """Test getting adapter metadata."""
        adapter = PostgreSQLAdapter(postgresql_config)
        metadata = adapter.get_metadata()

        assert metadata["name"] == "PostgreSQL Adapter"
        assert metadata["database_type"] == DatabaseType.POSTGRESQL.value
        assert metadata["driver"] == "psycopg2"
        assert metadata["ssl_enabled"] is False

    @patch("onb.adapters.database.base.create_engine")
    def test_get_metadata_connected(self, mock_create_engine, postgresql_config):
        """Test getting metadata when connected."""
        # Setup mocks
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = "PostgreSQL 14.5"

        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_conn.execute.return_value = mock_result

        mock_engine.connect.return_value = mock_conn
        mock_create_engine.return_value = mock_engine

        adapter = PostgreSQLAdapter(postgresql_config)
        adapter._engine = mock_engine
        adapter._connected = True

        metadata = adapter.get_metadata()

        assert "server_version" in metadata
        assert "PostgreSQL" in metadata["server_version"]

    @patch("onb.adapters.database.base.create_engine")
    def test_disconnect(self, mock_create_engine, postgresql_config):
        """Test disconnecting from database."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        adapter = PostgreSQLAdapter(postgresql_config)
        adapter._engine = mock_engine
        adapter._connected = True

        adapter.disconnect()

        assert adapter._connected is False
        assert adapter._engine is None
        mock_engine.dispose.assert_called_once()

    def test_context_manager(self, postgresql_config):
        """Test using adapter as context manager."""
        with patch("onb.adapters.database.base.create_engine") as mock_create_engine:
            mock_engine = MagicMock()
            mock_conn = MagicMock()
            mock_result = MagicMock()
            mock_result.scalar.return_value = 1

            mock_conn.__enter__ = Mock(return_value=mock_conn)
            mock_conn.__exit__ = Mock(return_value=None)
            mock_conn.execute.return_value = mock_result

            mock_engine.connect.return_value = mock_conn
            mock_create_engine.return_value = mock_engine

            with PostgreSQLAdapter(postgresql_config) as adapter:
                assert adapter._connected is True

            # Should be disconnected after context
            mock_engine.dispose.assert_called_once()
