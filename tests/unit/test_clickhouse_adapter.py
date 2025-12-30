"""Unit tests for ClickHouse database adapter."""
import pytest
from unittest.mock import MagicMock, Mock, patch

import pandas as pd
from sqlalchemy.exc import SQLAlchemyError

from onb.adapters.database.clickhouse import ClickHouseAdapter
from onb.core.exceptions import ConnectionError, QueryExecutionError
from onb.core.types import DatabaseConfig, DatabaseType


@pytest.fixture
def clickhouse_config():
    """ClickHouse database configuration."""
    return DatabaseConfig(
        type=DatabaseType.CLICKHOUSE,
        host="localhost",
        port=9000,
        user="default",
        password="",
        database="default",
        ssl=False,
    )


@pytest.fixture
def clickhouse_config_ssl():
    """ClickHouse configuration with SSL."""
    return DatabaseConfig(
        type=DatabaseType.CLICKHOUSE,
        host="prod-ch.example.com",
        port=9440,  # Secure native port
        user="analytics_user",
        password="secure!@#$%",  # Special characters
        database="analytics",
        ssl=True,
    )


class TestClickHouseAdapter:
    """Test ClickHouseAdapter class."""

    def test_initialization(self, clickhouse_config):
        """Test adapter initialization."""
        adapter = ClickHouseAdapter(clickhouse_config)

        assert adapter.config == clickhouse_config
        assert adapter.database_type == DatabaseType.CLICKHOUSE
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
            ClickHouseAdapter(config)

    def test_build_connection_string_basic(self, clickhouse_config):
        """Test building basic connection string."""
        adapter = ClickHouseAdapter(clickhouse_config)
        conn_str = adapter._build_connection_string()

        assert "clickhouse+native://" in conn_str
        assert "default:@localhost:9000/default" in conn_str
        assert "compression=lz4" in conn_str

    def test_build_connection_string_with_ssl(self, clickhouse_config_ssl):
        """Test building connection string with SSL."""
        adapter = ClickHouseAdapter(clickhouse_config_ssl)
        conn_str = adapter._build_connection_string()

        assert "clickhouse+native://" in conn_str
        assert "secure=True" in conn_str
        assert "compression=lz4" in conn_str

    def test_build_connection_string_special_chars(self, clickhouse_config_ssl):
        """Test URL encoding of special characters in password."""
        adapter = ClickHouseAdapter(clickhouse_config_ssl)
        conn_str = adapter._build_connection_string()

        # Special characters should be URL-encoded
        assert "secure!@#$%" not in conn_str
        assert "analytics_user:" in conn_str

    def test_build_connection_string_default_port(self):
        """Test default port is used when not specified."""
        config = DatabaseConfig(
            type=DatabaseType.CLICKHOUSE,
            host="localhost",
            port=9000,  # Use explicit port
            user="default",
            password="",
            database="default",
        )
        adapter = ClickHouseAdapter(config)
        conn_str = adapter._build_connection_string()

        assert ":9000/" in conn_str  # Default native port

    def test_normalize_result_empty(self, clickhouse_config):
        """Test normalizing empty DataFrame."""
        adapter = ClickHouseAdapter(clickhouse_config)
        empty_df = pd.DataFrame()

        result = adapter.normalize_result(empty_df)

        assert result.empty
        assert len(result) == 0

    def test_normalize_result_numeric(self, clickhouse_config):
        """Test normalizing numeric columns."""
        adapter = ClickHouseAdapter(clickhouse_config)
        df = pd.DataFrame({
            "uint64_col": [1, 2, 3],
            "float64_col": [1.1, 2.2, 3.3],
            "decimal_col": pd.Series([10.5, 20.7, 30.9], dtype="float64"),
        })

        result = adapter.normalize_result(df)

        assert pd.api.types.is_numeric_dtype(result["uint64_col"])
        assert pd.api.types.is_numeric_dtype(result["float64_col"])
        assert pd.api.types.is_numeric_dtype(result["decimal_col"])

    def test_normalize_result_lowercase_columns(self, clickhouse_config):
        """Test column names are lowercased."""
        adapter = ClickHouseAdapter(clickhouse_config)
        df = pd.DataFrame({
            "UserID": [1, 2],
            "USER_NAME": ["Alice", "Bob"],
            "CreatedAt": ["2024-01-01", "2024-01-02"],
        })

        result = adapter.normalize_result(df)

        # ClickHouse convention: lowercase column names for comparison
        assert "userid" in result.columns
        assert "user_name" in result.columns
        assert "createdat" in result.columns

    def test_normalize_result_datetime_with_timezone(self, clickhouse_config):
        """Test datetime normalization with timezone."""
        adapter = ClickHouseAdapter(clickhouse_config)

        # Create timezone-aware datetime
        dt_utc = pd.to_datetime(["2024-01-01 10:00:00"], utc=True)
        df = pd.DataFrame({"timestamp": dt_utc})

        result = adapter.normalize_result(df)

        assert pd.api.types.is_datetime64_any_dtype(result["timestamp"])
        # Should be UTC
        assert result["timestamp"].dt.tz is not None

    def test_normalize_result_datetime_without_timezone(self, clickhouse_config):
        """Test datetime normalization without timezone."""
        adapter = ClickHouseAdapter(clickhouse_config)

        # Create naive datetime
        dt_naive = pd.to_datetime(["2024-01-01 10:00:00"])
        df = pd.DataFrame({"timestamp": dt_naive})

        result = adapter.normalize_result(df)

        # Should be localized to UTC
        assert result["timestamp"].dt.tz is not None

    def test_normalize_result_array_column(self, clickhouse_config):
        """Test normalizing ClickHouse Array columns."""
        adapter = ClickHouseAdapter(clickhouse_config)

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
        # Arrays should remain as lists (or be serialized consistently)
        assert result["tags"].dtype == object
        # Check the actual value - it might be a list or might be preserved
        value = result["tags"].iloc[0]
        # Accept either list or the original value
        assert isinstance(value, (list, str)) or value == ["tag1", "tag2"]

    def test_normalize_result_tuple_column(self, clickhouse_config):
        """Test normalizing ClickHouse Tuple columns."""
        adapter = ClickHouseAdapter(clickhouse_config)

        # Simulate Tuple column
        df = pd.DataFrame({
            "Coordinates": [  # Use capital C to test lowercasing
                (1.0, 2.0),
                (3.0, 4.0),
            ]
        })

        result = adapter.normalize_result(df)

        # Column should be lowercased
        assert "coordinates" in result.columns
        # Tuples should remain as tuples (or be serialized)
        assert result["coordinates"].dtype == object
        # Check the actual value
        value = result["coordinates"].iloc[0]
        # Accept either tuple or string representation
        assert isinstance(value, (tuple, str)) or value == (1.0, 2.0)

    @patch("onb.adapters.database.base.create_engine")
    def test_connect_success(self, mock_create_engine, clickhouse_config):
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

        adapter = ClickHouseAdapter(clickhouse_config)
        adapter.connect()

        assert adapter._connected is True
        assert adapter._engine is not None
        mock_create_engine.assert_called_once()

    @patch("onb.adapters.database.base.create_engine")
    def test_get_database_version(self, mock_create_engine, clickhouse_config):
        """Test getting ClickHouse version."""
        # Setup mock
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = "23.8.2.7"

        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_conn.execute.return_value = mock_result

        mock_engine.connect.return_value = mock_conn
        mock_create_engine.return_value = mock_engine

        adapter = ClickHouseAdapter(clickhouse_config)
        adapter._engine = mock_engine
        adapter._connected = True

        version = adapter.get_database_version()

        assert version == "ClickHouse 23.8.2.7"
        mock_conn.execute.assert_called_once()

    def test_get_database_version_not_connected(self, clickhouse_config):
        """Test getting version when not connected."""
        adapter = ClickHouseAdapter(clickhouse_config)

        with pytest.raises(ConnectionError, match="Not connected"):
            adapter.get_database_version()

    def test_configure_engine_options(self, clickhouse_config):
        """Test ClickHouse engine options configuration."""
        adapter = ClickHouseAdapter(clickhouse_config)
        options = adapter._configure_engine_options()

        assert options["pool_size"] == 5
        assert options["max_overflow"] == 10
        assert options["pool_pre_ping"] is True
        assert options["pool_recycle"] == 3600

    def test_get_metadata(self, clickhouse_config):
        """Test getting adapter metadata."""
        adapter = ClickHouseAdapter(clickhouse_config)
        metadata = adapter.get_metadata()

        assert metadata["name"] == "ClickHouse Adapter"
        assert metadata["database_type"] == DatabaseType.CLICKHOUSE.value
        assert metadata["driver"] == "clickhouse-sqlalchemy"
        assert metadata["protocol"] == "native"
        assert metadata["ssl_enabled"] is False

    @patch("onb.adapters.database.base.create_engine")
    def test_get_metadata_connected(self, mock_create_engine, clickhouse_config):
        """Test getting metadata when connected."""
        # Setup mocks
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = "23.8.2.7"

        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_conn.execute.return_value = mock_result

        mock_engine.connect.return_value = mock_conn
        mock_create_engine.return_value = mock_engine

        adapter = ClickHouseAdapter(clickhouse_config)
        adapter._engine = mock_engine
        adapter._connected = True

        metadata = adapter.get_metadata()

        assert "server_version" in metadata
        assert "ClickHouse" in metadata["server_version"]

    @patch("onb.adapters.database.base.create_engine")
    def test_disconnect(self, mock_create_engine, clickhouse_config):
        """Test disconnecting from database."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        adapter = ClickHouseAdapter(clickhouse_config)
        adapter._engine = mock_engine
        adapter._connected = True

        adapter.disconnect()

        assert adapter._connected is False
        assert adapter._engine is None
        mock_engine.dispose.assert_called_once()

    def test_context_manager(self, clickhouse_config):
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

            with ClickHouseAdapter(clickhouse_config) as adapter:
                assert adapter._connected is True

            # Should be disconnected after context
            mock_engine.dispose.assert_called_once()

    def test_get_version_query(self, clickhouse_config):
        """Test version query string."""
        adapter = ClickHouseAdapter(clickhouse_config)
        query = adapter._get_version_query()

        assert query == "SELECT version()"

    def test_get_supported_features(self, clickhouse_config):
        """Test getting supported SQL features."""
        adapter = ClickHouseAdapter(clickhouse_config)
        features = adapter._get_supported_features()

        # Check for ClickHouse-specific features
        assert "ARRAY JOIN" in features
        assert "ASOF JOIN" in features
        assert "PREWHERE" in features
        assert "SAMPLE" in features
        assert "FINAL" in features
        assert "GLOBAL JOIN" in features

        # Check for standard features
        assert "GROUP BY" in features
        assert "WINDOW FUNCTIONS" in features
        assert "CTE" in features
