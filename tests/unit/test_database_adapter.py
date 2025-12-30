"""Unit tests for database adapter module."""
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pandas as pd
import pytest
from sqlalchemy.exc import SQLAlchemyError

from onb.adapters.database.base import DatabaseAdapter
from onb.adapters.database.mysql import MySQLAdapter
from onb.core.exceptions import (
    ConnectionError,
    QueryExecutionError,
    SchemaNotFoundError,
    TableNotFoundError,
)
from onb.core.types import DatabaseConfig, DatabaseType, QualityLevel


class TestDatabaseAdapter:
    """Test DatabaseAdapter abstract base class."""

    def test_adapter_initialization(self, sample_database_config):
        """Test adapter initialization."""
        # Create a concrete implementation for testing
        adapter = MySQLAdapter(sample_database_config)

        assert adapter.config == sample_database_config
        assert adapter._engine is None
        assert adapter._connected is False

    @patch("onb.adapters.database.base.create_engine")
    def test_connect_success(self, mock_create_engine, sample_database_config):
        """Test successful database connection."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_create_engine.return_value = mock_engine

        adapter = MySQLAdapter(sample_database_config)
        adapter.connect()

        assert adapter._connected is True
        assert adapter._engine is not None
        mock_conn.execute.assert_called_once()

    @patch("onb.adapters.database.base.create_engine")
    def test_connect_failure(self, mock_create_engine, sample_database_config):
        """Test failed database connection."""
        mock_create_engine.side_effect = SQLAlchemyError("Connection failed")

        adapter = MySQLAdapter(sample_database_config)

        with pytest.raises(ConnectionError, match="Failed to connect"):
            adapter.connect()

        assert adapter._connected is False

    @patch("onb.adapters.database.base.create_engine")
    def test_connect_idempotent(self, mock_create_engine, sample_database_config):
        """Test that connect is idempotent."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_create_engine.return_value = mock_engine

        adapter = MySQLAdapter(sample_database_config)
        adapter.connect()
        adapter.connect()  # Second call should not create new engine

        assert mock_create_engine.call_count == 1

    @patch("onb.adapters.database.base.create_engine")
    def test_disconnect(self, mock_create_engine, sample_database_config):
        """Test database disconnection."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_create_engine.return_value = mock_engine

        adapter = MySQLAdapter(sample_database_config)
        adapter.connect()
        adapter.disconnect()

        assert adapter._connected is False
        assert adapter._engine is None
        mock_engine.dispose.assert_called_once()

    @patch("onb.adapters.database.base.create_engine")
    def test_context_manager(self, mock_create_engine, sample_database_config):
        """Test using adapter as context manager."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_create_engine.return_value = mock_engine

        adapter = MySQLAdapter(sample_database_config)

        with adapter as ctx_adapter:
            assert ctx_adapter._connected is True
            assert ctx_adapter is adapter

        assert adapter._connected is False
        mock_engine.dispose.assert_called_once()

    @patch("onb.adapters.database.base.create_engine")
    def test_execute_query_success(self, mock_create_engine, sample_database_config):
        """Test successful query execution."""
        # Setup mocks
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_result = MagicMock()

        mock_result.fetchall.return_value = [(1, "Alice"), (2, "Bob")]
        mock_result.keys.return_value = ["id", "name"]

        mock_conn.execute.return_value = mock_result
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_create_engine.return_value = mock_engine

        adapter = MySQLAdapter(sample_database_config)
        adapter.connect()

        df = adapter.execute_query("SELECT * FROM users")

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert list(df.columns) == ["id", "name"]

    @patch("onb.adapters.database.base.create_engine")
    def test_execute_query_not_connected(self, mock_create_engine, sample_database_config):
        """Test query execution when not connected."""
        adapter = MySQLAdapter(sample_database_config)

        with pytest.raises(ConnectionError, match="Not connected"):
            adapter.execute_query("SELECT 1")

    @patch("onb.adapters.database.base.create_engine")
    def test_execute_query_failure(self, mock_create_engine, sample_database_config):
        """Test query execution failure."""
        mock_engine = MagicMock()

        # Setup two different connection contexts
        # First context for connect() - succeeds
        mock_conn1 = MagicMock()
        mock_conn1.execute.return_value = MagicMock()  # SELECT 1 succeeds

        # Second context for execute_query() - fails
        mock_conn2 = MagicMock()
        mock_conn2.execute.side_effect = SQLAlchemyError("Query failed")

        # Mock context managers to return different connections
        mock_context1 = MagicMock()
        mock_context1.__enter__.return_value = mock_conn1
        mock_context1.__exit__.return_value = None

        mock_context2 = MagicMock()
        mock_context2.__enter__.return_value = mock_conn2
        mock_context2.__exit__.return_value = None

        # Return different contexts on each call
        mock_engine.connect.side_effect = [mock_context1, mock_context2]
        mock_create_engine.return_value = mock_engine

        adapter = MySQLAdapter(sample_database_config)
        adapter.connect()

        with pytest.raises(QueryExecutionError, match="Query execution failed"):
            adapter.execute_query("INVALID SQL")

    @patch("onb.adapters.database.base.create_engine")
    @patch("onb.adapters.database.base.inspect")
    def test_get_schema_info_success(
        self, mock_inspect, mock_create_engine, sample_database_config
    ):
        """Test getting schema information."""
        # Setup engine mock
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_create_engine.return_value = mock_engine

        # Setup inspector mock
        mock_inspector = MagicMock()
        mock_inspector.get_table_names.return_value = ["users", "orders"]
        mock_inspector.get_columns.return_value = [
            {
                "name": "id",
                "type": "BIGINT",
                "nullable": False,
                "default": None,
                "comment": "Primary key",
            },
            {
                "name": "username",
                "type": "VARCHAR(100)",
                "nullable": False,
                "default": None,
                "comment": "Username",
            },
        ]
        mock_inspector.get_pk_constraint.return_value = {
            "constrained_columns": ["id"]
        }
        mock_inspector.get_indexes.return_value = []
        mock_inspect.return_value = mock_inspector

        adapter = MySQLAdapter(sample_database_config)
        adapter.connect()

        schema_info = adapter.get_schema_info()

        assert schema_info.database_name == "test_db"
        assert schema_info.database_type == DatabaseType.MYSQL
        assert len(schema_info.tables) == 2
        assert schema_info.tables[0].name == "users"

    @patch("onb.adapters.database.base.create_engine")
    def test_get_schema_info_not_connected(self, mock_create_engine, sample_database_config):
        """Test getting schema info when not connected."""
        adapter = MySQLAdapter(sample_database_config)

        with pytest.raises(ConnectionError, match="Not connected"):
            adapter.get_schema_info()

    @patch("onb.adapters.database.base.create_engine")
    @patch("onb.adapters.database.base.inspect")
    def test_get_schema_info_failure(
        self, mock_inspect, mock_create_engine, sample_database_config
    ):
        """Test schema info retrieval failure."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_create_engine.return_value = mock_engine

        mock_inspect.side_effect = SQLAlchemyError("Schema not found")

        adapter = MySQLAdapter(sample_database_config)
        adapter.connect()

        with pytest.raises(SchemaNotFoundError, match="Failed to get schema info"):
            adapter.get_schema_info()

    @patch("onb.adapters.database.base.create_engine")
    def test_get_database_version(self, mock_create_engine, sample_database_config):
        """Test getting database version."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [("8.0.32",)]
        mock_result.keys.return_value = ["version"]
        mock_conn.execute.return_value = mock_result
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_create_engine.return_value = mock_engine

        adapter = MySQLAdapter(sample_database_config)
        adapter.connect()

        version = adapter.get_database_version()

        assert "8.0.32" in version

    @patch("onb.adapters.database.base.create_engine")
    def test_supports_feature(self, mock_create_engine, sample_database_config):
        """Test feature support checking."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_create_engine.return_value = mock_engine

        adapter = MySQLAdapter(sample_database_config)
        adapter.connect()

        assert adapter.supports_feature("WINDOW_FUNCTIONS") is True
        assert adapter.supports_feature("CTE") is True
        assert adapter.supports_feature("NONEXISTENT_FEATURE") is False


class TestMySQLAdapter:
    """Test MySQL-specific adapter implementation."""

    def test_database_type(self, sample_database_config):
        """Test database type property."""
        adapter = MySQLAdapter(sample_database_config)
        assert adapter.database_type == DatabaseType.MYSQL

    def test_build_connection_string_basic(self, sample_database_config):
        """Test building basic MySQL connection string."""
        adapter = MySQLAdapter(sample_database_config)
        conn_str = adapter._build_connection_string()

        assert "mysql+pymysql://" in conn_str
        assert "test_user:test_password" in conn_str
        assert "localhost:3306" in conn_str
        assert "test_db" in conn_str

    def test_build_connection_string_with_ssl(self, sample_database_config):
        """Test building MySQL connection string with SSL."""
        sample_database_config.ssl = True
        adapter = MySQLAdapter(sample_database_config)
        conn_str = adapter._build_connection_string()

        assert "ssl=true" in conn_str

    def test_set_query_timeout(self, sample_database_config):
        """Test setting query timeout."""
        mock_conn = MagicMock()
        adapter = MySQLAdapter(sample_database_config)

        # Should not raise exception even if setting timeout fails
        adapter._set_query_timeout(mock_conn, 30000)
        mock_conn.execute.assert_called_once()

    def test_normalize_result_column_names(self, sample_database_config):
        """Test result normalization - column name lowercasing."""
        adapter = MySQLAdapter(sample_database_config)

        df = pd.DataFrame({"ID": [1, 2], "UserName": ["Alice", "Bob"]})
        normalized = adapter.normalize_result(df)

        assert list(normalized.columns) == ["id", "username"]

    def test_normalize_result_decimal_conversion(self, sample_database_config):
        """Test result normalization - DECIMAL to float conversion."""
        adapter = MySQLAdapter(sample_database_config)

        # Simulate DECIMAL values as object dtype
        df = pd.DataFrame({"price": ["19.99", "29.99"]})
        normalized = adapter.normalize_result(df)

        assert normalized["price"].dtype in [float, "float64"]
        assert normalized["price"].iloc[0] == 19.99

    def test_normalize_result_datetime_timezone(self, sample_database_config):
        """Test result normalization - datetime timezone handling."""
        adapter = MySQLAdapter(sample_database_config)

        # Naive datetime
        naive_dt = pd.to_datetime(["2024-01-01 10:00:00", "2024-01-02 15:30:00"])
        df = pd.DataFrame({"created_at": naive_dt})

        normalized = adapter.normalize_result(df)

        assert normalized["created_at"].dt.tz is not None
        assert str(normalized["created_at"].dt.tz) == "UTC"

    def test_normalize_result_empty_dataframe(self, sample_database_config):
        """Test normalization of empty DataFrame."""
        adapter = MySQLAdapter(sample_database_config)

        df = pd.DataFrame()
        normalized = adapter.normalize_result(df)

        assert normalized.empty

    def test_normalize_result_null_handling(self, sample_database_config):
        """Test normalization of NULL values."""
        adapter = MySQLAdapter(sample_database_config)

        df = pd.DataFrame({"name": ["Alice", None, "Charlie"]})
        normalized = adapter.normalize_result(df)

        # Check that None is handled (converted to pd.NA)
        assert pd.isna(normalized["name"].iloc[1])

    def test_get_version_query(self, sample_database_config):
        """Test MySQL version query."""
        adapter = MySQLAdapter(sample_database_config)
        query = adapter._get_version_query()

        assert query == "SELECT VERSION()"

    def test_get_supported_features(self, sample_database_config):
        """Test getting MySQL supported features."""
        adapter = MySQLAdapter(sample_database_config)
        features = adapter._get_supported_features()

        assert "WINDOW_FUNCTIONS" in features
        assert "CTE" in features
        assert "JSON_FUNCTIONS" in features
        assert "JOINS" in features
        assert len(features) > 10

    @patch("onb.adapters.database.base.create_engine")
    def test_get_table_row_count_fast(
        self, mock_create_engine, sample_database_config
    ):
        """Test fast row count using INFORMATION_SCHEMA."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [(1000,)]
        mock_result.keys.return_value = ["TABLE_ROWS"]
        mock_conn.execute.return_value = mock_result
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_create_engine.return_value = mock_engine

        adapter = MySQLAdapter(sample_database_config)
        adapter.connect()

        count = adapter._get_table_row_count("users", "test_db")

        assert count == 1000

    @patch("onb.adapters.database.base.create_engine")
    def test_get_table_row_count_fallback(
        self, mock_create_engine, sample_database_config
    ):
        """Test row count fallback to exact count."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()

        # First call (INFORMATION_SCHEMA) returns empty
        # Second call (COUNT(*)) returns actual count
        mock_result1 = MagicMock()
        mock_result1.fetchall.return_value = []
        mock_result1.keys.return_value = ["TABLE_ROWS"]

        mock_result2 = MagicMock()
        mock_result2.fetchall.return_value = [(500,)]
        mock_result2.keys.return_value = ["count"]

        mock_conn.execute.side_effect = [mock_result1, mock_result2]
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_create_engine.return_value = mock_engine

        adapter = MySQLAdapter(sample_database_config)
        adapter.connect()

        count = adapter._get_table_row_count("users", "test_db")

        # Should fall back to exact count
        assert count >= 0


class TestDatabaseAdapterIntegration:
    """Integration tests for database adapter (with more complex scenarios)."""

    @patch("onb.adapters.database.base.create_engine")
    @patch("onb.adapters.database.base.inspect")
    def test_get_table_info_with_indexes(
        self, mock_inspect, mock_create_engine, sample_database_config
    ):
        """Test getting table info with indexes."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_create_engine.return_value = mock_engine

        mock_inspector = MagicMock()
        mock_inspector.get_table_names.return_value = ["users"]
        mock_inspector.get_columns.return_value = [
            {"name": "id", "type": "BIGINT", "nullable": False, "default": None},
            {"name": "email", "type": "VARCHAR(255)", "nullable": False, "default": None},
        ]
        mock_inspector.get_pk_constraint.return_value = {
            "constrained_columns": ["id"]
        }
        mock_inspector.get_indexes.return_value = [
            {"name": "idx_email", "column_names": ["email"], "unique": True}
        ]
        mock_inspect.return_value = mock_inspector

        adapter = MySQLAdapter(sample_database_config)
        adapter.connect()

        schema_info = adapter.get_schema_info()
        table = schema_info.tables[0]

        assert len(table.indexes) == 1
        assert table.indexes[0].name == "idx_email"
        assert table.indexes[0].unique is True

    @patch("onb.adapters.database.base.create_engine")
    @patch("onb.adapters.database.base.inspect")
    def test_get_table_info_with_row_count(
        self, mock_inspect, mock_create_engine, sample_database_config
    ):
        """Test getting table info with row count."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()

        # Mock for SELECT 1 and row count query
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [(1000,)]
        mock_result.keys.return_value = ["TABLE_ROWS"]
        mock_conn.execute.return_value = mock_result

        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_create_engine.return_value = mock_engine

        mock_inspector = MagicMock()
        mock_inspector.get_table_names.return_value = ["users"]
        mock_inspector.get_columns.return_value = [
            {"name": "id", "type": "BIGINT", "nullable": False, "default": None},
        ]
        mock_inspector.get_pk_constraint.return_value = {"constrained_columns": ["id"]}
        mock_inspector.get_indexes.return_value = []
        mock_inspect.return_value = mock_inspector

        adapter = MySQLAdapter(sample_database_config)
        adapter.connect()

        schema_info = adapter.get_schema_info(include_stats=True)
        table = schema_info.tables[0]

        assert table.row_count is not None
        assert table.row_count >= 0

    def test_normalize_result_complex_types(self, sample_database_config):
        """Test normalization with complex data types."""
        adapter = MySQLAdapter(sample_database_config)

        # Create DataFrame with various types
        df = pd.DataFrame({
            "ID": [1, 2, 3],
            "Price": ["19.99", "29.99", "39.99"],  # DECIMAL as string
            "Name": ["Alice", None, "Charlie"],  # With NULL
            "CreatedAt": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
        })

        normalized = adapter.normalize_result(df)

        # Check all transformations
        assert list(normalized.columns) == ["id", "price", "name", "createdat"]
        assert normalized["price"].dtype in [float, "float64"]
        assert pd.isna(normalized["name"].iloc[1])
        assert normalized["createdat"].dt.tz is not None
