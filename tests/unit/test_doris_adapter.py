"""Unit tests for Apache Doris database adapter."""
import pytest
from unittest.mock import MagicMock, Mock, patch

import pandas as pd
from sqlalchemy.exc import SQLAlchemyError

from onb.adapters.database.doris import DorisAdapter
from onb.core.exceptions import ConnectionError, QueryExecutionError
from onb.core.types import DatabaseConfig, DatabaseType


@pytest.fixture
def doris_config():
    """Doris database configuration."""
    return DatabaseConfig(
        type=DatabaseType.DORIS,
        host="localhost",
        port=9030,
        user="root",
        password="",
        database="test_db",
        ssl=False,
    )


@pytest.fixture
def doris_config_ssl():
    """Doris configuration with SSL."""
    return DatabaseConfig(
        type=DatabaseType.DORIS,
        host="prod-doris.example.com",
        port=9030,
        user="analytics",
        password="secure!@#$%",  # Special characters
        database="analytics_db",
        ssl=True,
    )


class TestDorisAdapter:
    """Test DorisAdapter class."""

    def test_initialization(self, doris_config):
        """Test adapter initialization."""
        adapter = DorisAdapter(doris_config)

        assert adapter.config == doris_config
        assert adapter.database_type == DatabaseType.DORIS
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
            DorisAdapter(config)

    def test_build_connection_string_basic(self, doris_config):
        """Test building basic connection string."""
        adapter = DorisAdapter(doris_config)
        conn_str = adapter._build_connection_string()

        assert "mysql+pymysql://" in conn_str
        assert "root:@localhost:9030/test_db" in conn_str
        assert "charset=utf8mb4" in conn_str
        assert "ssl_disabled=true" in conn_str

    def test_build_connection_string_with_ssl(self, doris_config_ssl):
        """Test building connection string with SSL."""
        adapter = DorisAdapter(doris_config_ssl)
        conn_str = adapter._build_connection_string()

        assert "mysql+pymysql://" in conn_str
        assert "ssl_disabled=false" in conn_str
        assert "charset=utf8mb4" in conn_str

    def test_build_connection_string_special_chars(self, doris_config_ssl):
        """Test URL encoding of special characters in password."""
        adapter = DorisAdapter(doris_config_ssl)
        conn_str = adapter._build_connection_string()

        # Special characters should be URL-encoded
        assert "secure!@#$%" not in conn_str
        assert "analytics:" in conn_str

    def test_build_connection_string_default_port(self):
        """Test default port is used when not specified."""
        config = DatabaseConfig(
            type=DatabaseType.DORIS,
            host="localhost",
            port=9030,
            user="root",
            password="",
            database="test",
        )
        adapter = DorisAdapter(config)
        conn_str = adapter._build_connection_string()

        assert ":9030/" in conn_str  # Default MySQL protocol port

    def test_normalize_result_empty(self, doris_config):
        """Test normalizing empty DataFrame."""
        adapter = DorisAdapter(doris_config)
        empty_df = pd.DataFrame()

        result = adapter.normalize_result(empty_df)

        assert result.empty
        assert len(result) == 0

    def test_normalize_result_numeric(self, doris_config):
        """Test normalizing numeric columns."""
        adapter = DorisAdapter(doris_config)
        df = pd.DataFrame({
            "int_col": [1, 2, 3],
            "bigint_col": [100000000, 200000000, 300000000],
            "decimal_col": pd.Series([10.5, 20.7, 30.9], dtype="float64"),
        })

        result = adapter.normalize_result(df)

        assert pd.api.types.is_numeric_dtype(result["int_col"])
        assert pd.api.types.is_numeric_dtype(result["bigint_col"])
        assert pd.api.types.is_numeric_dtype(result["decimal_col"])

    def test_normalize_result_lowercase_columns(self, doris_config):
        """Test column names are lowercased."""
        adapter = DorisAdapter(doris_config)
        df = pd.DataFrame({
            "UserID": [1, 2],
            "USER_NAME": ["Alice", "Bob"],
            "CreatedAt": ["2024-01-01", "2024-01-02"],
        })

        result = adapter.normalize_result(df)

        # Lowercase column names for consistency
        assert "userid" in result.columns
        assert "user_name" in result.columns
        assert "createdat" in result.columns

    def test_normalize_result_datetime_with_timezone(self, doris_config):
        """Test datetime normalization with timezone."""
        adapter = DorisAdapter(doris_config)

        # Create timezone-aware datetime
        dt_utc = pd.to_datetime(["2024-01-01 10:00:00"], utc=True)
        df = pd.DataFrame({"timestamp": dt_utc})

        result = adapter.normalize_result(df)

        assert pd.api.types.is_datetime64_any_dtype(result["timestamp"])
        # Should be UTC
        assert result["timestamp"].dt.tz is not None

    def test_normalize_result_datetime_without_timezone(self, doris_config):
        """Test datetime normalization without timezone."""
        adapter = DorisAdapter(doris_config)

        # Create naive datetime
        dt_naive = pd.to_datetime(["2024-01-01 10:00:00"])
        df = pd.DataFrame({"timestamp": dt_naive})

        result = adapter.normalize_result(df)

        # Should be localized to UTC
        assert result["timestamp"].dt.tz is not None

    def test_normalize_result_json_column(self, doris_config):
        """Test normalizing JSON columns."""
        adapter = DorisAdapter(doris_config)

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

    def test_normalize_result_array_column(self, doris_config):
        """Test normalizing Array columns (Doris 2.0+)."""
        adapter = DorisAdapter(doris_config)

        # Simulate Array column (list objects)
        df = pd.DataFrame({
            "Tags": [  # Use capital T to test lowercasing
                ["tag1", "tag2"],
                ["tag3", "tag4", "tag5"],
            ]
        })

        result = adapter.normalize_result(df)

        # Column should be lowercased
        assert "tags" in result.columns
        # Arrays should remain as lists
        assert result["tags"].dtype == object

    def test_normalize_result_binary_column(self, doris_config):
        """Test normalizing binary columns (BITMAP, HLL)."""
        adapter = DorisAdapter(doris_config)

        # Simulate binary column
        df = pd.DataFrame({
            "bitmap_col": [
                b"\x01\x02\x03",
                b"\x04\x05\x06",
            ]
        })

        result = adapter.normalize_result(df)

        # Binary should be converted to hex string
        assert result["bitmap_col"].dtype == object
        assert result["bitmap_col"].iloc[0] == "010203"

    @patch("onb.adapters.database.base.create_engine")
    def test_connect_success(self, mock_create_engine, doris_config):
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

        adapter = DorisAdapter(doris_config)
        adapter.connect()

        assert adapter._connected is True
        assert adapter._engine is not None
        mock_create_engine.assert_called_once()

    @patch("onb.adapters.database.base.create_engine")
    def test_get_database_version(self, mock_create_engine, doris_config):
        """Test getting Doris version."""
        # Setup mock
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = "5.7.99 Doris version 2.0.3-rc01"

        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_conn.execute.return_value = mock_result

        mock_engine.connect.return_value = mock_conn
        mock_create_engine.return_value = mock_engine

        adapter = DorisAdapter(doris_config)
        adapter._engine = mock_engine
        adapter._connected = True

        version = adapter.get_database_version()

        assert "Doris" in version
        mock_conn.execute.assert_called_once()

    def test_get_database_version_not_connected(self, doris_config):
        """Test getting version when not connected."""
        adapter = DorisAdapter(doris_config)

        with pytest.raises(ConnectionError, match="Not connected"):
            adapter.get_database_version()

    def test_configure_engine_options(self, doris_config):
        """Test Doris engine options configuration."""
        adapter = DorisAdapter(doris_config)
        options = adapter._configure_engine_options()

        assert options["pool_size"] == 5
        assert options["max_overflow"] == 10
        assert options["pool_pre_ping"] is True
        assert options["pool_recycle"] == 3600

    def test_get_metadata(self, doris_config):
        """Test getting adapter metadata."""
        adapter = DorisAdapter(doris_config)
        metadata = adapter.get_metadata()

        assert metadata["name"] == "Apache Doris Adapter"
        assert metadata["database_type"] == DatabaseType.DORIS.value
        assert metadata["driver"] == "pymysql"
        assert metadata["protocol"] == "mysql"
        assert metadata["ssl_enabled"] is False

    @patch("onb.adapters.database.base.create_engine")
    def test_get_metadata_connected(self, mock_create_engine, doris_config):
        """Test getting metadata when connected."""
        # Setup mocks
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = "5.7.99 Doris version 2.0.3"

        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_conn.execute.return_value = mock_result

        mock_engine.connect.return_value = mock_conn
        mock_create_engine.return_value = mock_engine

        adapter = DorisAdapter(doris_config)
        adapter._engine = mock_engine
        adapter._connected = True

        metadata = adapter.get_metadata()

        assert "server_version" in metadata
        assert "Doris" in metadata["server_version"]

    @patch("onb.adapters.database.base.create_engine")
    def test_disconnect(self, mock_create_engine, doris_config):
        """Test disconnecting from database."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        adapter = DorisAdapter(doris_config)
        adapter._engine = mock_engine
        adapter._connected = True

        adapter.disconnect()

        assert adapter._connected is False
        assert adapter._engine is None
        mock_engine.dispose.assert_called_once()

    def test_context_manager(self, doris_config):
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

            with DorisAdapter(doris_config) as adapter:
                assert adapter._connected is True

            # Should be disconnected after context
            mock_engine.dispose.assert_called_once()

    def test_get_version_query(self, doris_config):
        """Test version query string."""
        adapter = DorisAdapter(doris_config)
        query = adapter._get_version_query()

        assert query == "SELECT VERSION()"

    def test_get_supported_features(self, doris_config):
        """Test getting supported SQL features."""
        adapter = DorisAdapter(doris_config)
        features = adapter._get_supported_features()

        # Check for Doris-specific features
        assert "BITMAP" in features
        assert "HLL" in features
        assert "ROLLUP" in features
        assert "COLOCATE JOIN" in features
        assert "SEMI JOIN" in features
        assert "ANTI JOIN" in features

        # Check for standard features
        assert "GROUP BY" in features
        assert "WINDOW FUNCTIONS" in features
        assert "CTE" in features
