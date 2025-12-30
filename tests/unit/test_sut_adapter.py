"""Unit tests for SUT adapter module."""
import pytest

from onb.adapters.sut.base import SUTAdapter
from onb.adapters.sut.mock import MockSUTAdapter
from onb.core.exceptions import SUTAdapterError
from onb.core.types import DatabaseType, SchemaInfo, SUTConfig, TableInfo


@pytest.fixture
def mock_schema():
    """Create mock schema for testing."""
    return SchemaInfo(
        database_name="test_db",
        database_type=DatabaseType.MYSQL,
        tables=[
            TableInfo(name="users", columns=[]),
            TableInfo(name="orders", columns=[]),
        ],
    )


class TestSUTAdapter:
    """Test SUTAdapter base class."""

    def test_adapter_initialization(self):
        """Test adapter initialization."""
        config = SUTConfig(name="TestSUT", type="mock", version="1.0.0")
        adapter = MockSUTAdapter(config)

        assert adapter.name == "TestSUT"
        assert adapter.version == "1.0.0"
        assert adapter._initialized is False

    def test_adapter_context_manager(self, mock_schema):
        """Test using adapter as context manager."""
        config = SUTConfig(name="TestSUT", type="mock")
        adapter = MockSUTAdapter(config)

        assert adapter._initialized is False

        with adapter:
            assert adapter._initialized is True
            result = adapter.query("Count users", mock_schema)
            assert result.success is True

        assert adapter._initialized is False

    def test_adapter_metadata(self):
        """Test getting adapter metadata."""
        config = SUTConfig(name="TestSUT", type="mock", version="2.0.0")
        adapter = MockSUTAdapter(config)

        metadata = adapter.get_metadata()

        assert metadata["name"] == "TestSUT"
        assert metadata["version"] == "2.0.0"
        assert metadata["type"] == "mock"
        assert metadata["initialized"] is False


class TestMockSUTAdapter:
    """Test MockSUTAdapter implementation."""

    def test_initialization(self):
        """Test mock adapter initialization."""
        adapter = MockSUTAdapter()
        adapter.initialize()

        assert adapter._initialized is True
        assert adapter._query_count == 0

        adapter.cleanup()
        assert adapter._initialized is False

    def test_default_config(self):
        """Test mock adapter with default config."""
        adapter = MockSUTAdapter()

        assert adapter.name == "MockSUT"
        assert adapter.version == "1.0.0"
        assert adapter.auto_generate_sql is True

    def test_custom_config(self):
        """Test mock adapter with custom config."""
        config = SUTConfig(
            name="CustomMock",
            type="mock",
            version="0.5.0",
        )
        adapter = MockSUTAdapter(
            config=config,
            auto_generate_sql=False,
            simulate_delay_ms=50,
        )

        assert adapter.name == "CustomMock"
        assert adapter.version == "0.5.0"
        assert adapter.auto_generate_sql is False
        assert adapter.simulate_delay_ms == 50

    def test_query_not_initialized(self, mock_schema):
        """Test query before initialization raises error."""
        adapter = MockSUTAdapter()

        with pytest.raises(SUTAdapterError, match="not initialized"):
            adapter.query("Test question", mock_schema)

    def test_query_success(self, mock_schema):
        """Test successful query execution."""
        adapter = MockSUTAdapter(simulate_delay_ms=0)
        adapter.initialize()

        result = adapter.query("Count all users", mock_schema)

        assert result.success is True
        assert result.generated_sql is not None
        assert len(result.generated_sql) > 0
        assert result.result_dataframe is not None
        assert result.total_time_ms >= 0
        assert result.token_usage is not None
        assert result.timing_breakdown is not None

    def test_query_count_keyword(self, mock_schema):
        """Test query with COUNT keyword."""
        adapter = MockSUTAdapter(simulate_delay_ms=0)
        adapter.initialize()

        result = adapter.query("Count all users", mock_schema)

        assert result.success is True
        assert "COUNT" in result.generated_sql.upper()
        assert "count" in result.result_dataframe.columns

    def test_query_average_keyword(self, mock_schema):
        """Test query with average keyword."""
        adapter = MockSUTAdapter(simulate_delay_ms=0)
        adapter.initialize()

        result = adapter.query("What is the average value?", mock_schema)

        assert result.success is True
        assert "AVG" in result.generated_sql.upper()
        assert "avg" in result.result_dataframe.columns

    def test_query_sum_keyword(self, mock_schema):
        """Test query with sum keyword."""
        adapter = MockSUTAdapter(simulate_delay_ms=0)
        adapter.initialize()

        result = adapter.query("What is the total sum?", mock_schema)

        assert result.success is True
        assert "SUM" in result.generated_sql.upper()
        assert "sum" in result.result_dataframe.columns

    def test_query_max_keyword(self, mock_schema):
        """Test query with maximum keyword."""
        adapter = MockSUTAdapter(simulate_delay_ms=0)
        adapter.initialize()

        result = adapter.query("What is the maximum value?", mock_schema)

        assert result.success is True
        assert "MAX" in result.generated_sql.upper()
        assert "max" in result.result_dataframe.columns

    def test_query_min_keyword(self, mock_schema):
        """Test query with minimum keyword."""
        adapter = MockSUTAdapter(simulate_delay_ms=0)
        adapter.initialize()

        result = adapter.query("What is the minimum value?", mock_schema)

        assert result.success is True
        assert "MIN" in result.generated_sql.upper()
        assert "min" in result.result_dataframe.columns

    def test_query_default_select(self, mock_schema):
        """Test query with default SELECT."""
        adapter = MockSUTAdapter(simulate_delay_ms=0)
        adapter.initialize()

        result = adapter.query("Show me the data", mock_schema)

        assert result.success is True
        assert "SELECT" in result.generated_sql.upper()
        assert len(result.result_dataframe) > 0
        assert "id" in result.result_dataframe.columns

    def test_query_chinese_keywords(self, mock_schema):
        """Test query with Chinese keywords."""
        adapter = MockSUTAdapter(simulate_delay_ms=0)
        adapter.initialize()

        # Test count in Chinese
        result = adapter.query("有多少用户？", mock_schema)
        assert "COUNT" in result.generated_sql.upper()

        # Test average in Chinese
        result = adapter.query("平均值是多少？", mock_schema)
        assert "AVG" in result.generated_sql.upper()

        # Test sum in Chinese
        result = adapter.query("总和是多少？", mock_schema)
        assert "SUM" in result.generated_sql.upper()

        # Test max in Chinese
        result = adapter.query("最大值是多少？", mock_schema)
        assert "MAX" in result.generated_sql.upper()

        # Test min in Chinese
        result = adapter.query("最小值是多少？", mock_schema)
        assert "MIN" in result.generated_sql.upper()

    def test_query_with_failure_keyword(self, mock_schema):
        """Test query failure triggered by keyword."""
        adapter = MockSUTAdapter(
            simulate_delay_ms=0,
            fail_on_keywords=["ERROR", "INVALID"],
        )
        adapter.initialize()

        result = adapter.query("This contains ERROR keyword", mock_schema)

        assert result.success is False
        assert result.error is not None
        assert "ERROR" in result.error

    def test_query_counter_increments(self, mock_schema):
        """Test query counter increments."""
        adapter = MockSUTAdapter(simulate_delay_ms=0)
        adapter.initialize()

        assert adapter._query_count == 0

        adapter.query("Query 1", mock_schema)
        assert adapter._query_count == 1

        adapter.query("Query 2", mock_schema)
        assert adapter._query_count == 2

        adapter.query("Query 3", mock_schema)
        assert adapter._query_count == 3

    def test_token_usage_generation(self, mock_schema):
        """Test token usage is generated."""
        adapter = MockSUTAdapter(simulate_delay_ms=0)
        adapter.initialize()

        result = adapter.query("Show me all users", mock_schema)

        assert result.token_usage is not None
        assert result.token_usage.input_tokens > 0
        assert result.token_usage.output_tokens > 0
        assert result.token_usage.total_tokens > 0
        assert result.token_available is True

    def test_timing_breakdown_generation(self, mock_schema):
        """Test timing breakdown is generated."""
        adapter = MockSUTAdapter(simulate_delay_ms=0)
        adapter.initialize()

        result = adapter.query("Show me all users", mock_schema)

        assert result.timing_breakdown is not None
        assert result.timing_breakdown.nl2sql_time_ms is not None
        assert result.timing_breakdown.sql_generation_time_ms is not None
        assert result.timing_breakdown.sql_execution_time_ms is not None
        assert result.timing_breakdown.total_time_ms is not None
        assert result.timing_source == "vendor"

    def test_simulate_delay(self, mock_schema):
        """Test simulated processing delay."""
        import time

        adapter = MockSUTAdapter(simulate_delay_ms=100)
        adapter.initialize()

        start = time.time()
        result = adapter.query("Test query", mock_schema)
        elapsed = (time.time() - start) * 1000  # Convert to ms

        assert result.success is True
        assert elapsed >= 100  # Should be at least 100ms
        assert result.total_time_ms >= 100

    def test_metadata_includes_query_count(self, mock_schema):
        """Test metadata includes query count."""
        adapter = MockSUTAdapter(simulate_delay_ms=0)
        adapter.initialize()

        adapter.query("Query 1", mock_schema)
        adapter.query("Query 2", mock_schema)

        metadata = adapter.get_metadata()

        assert metadata["query_count"] == 2
        assert metadata["auto_generate_sql"] is True
        assert metadata["simulate_delay_ms"] == 0

    def test_custom_expected_sql(self, mock_schema):
        """Test providing custom expected SQL."""
        adapter = MockSUTAdapter(auto_generate_sql=False, simulate_delay_ms=0)
        adapter.initialize()

        custom_sql = "SELECT id, name FROM users WHERE active = 1"
        result = adapter.query(
            "Show active users",
            mock_schema,
            expected_sql=custom_sql,
        )

        assert result.success is True
        assert result.generated_sql == custom_sql

    def test_cleanup_resets_state(self, mock_schema):
        """Test cleanup resets adapter state."""
        adapter = MockSUTAdapter(simulate_delay_ms=0)
        adapter.initialize()

        adapter.query("Query 1", mock_schema)
        adapter.query("Query 2", mock_schema)

        assert adapter._initialized is True
        assert adapter._query_count == 2

        adapter.cleanup()

        assert adapter._initialized is False
        assert adapter._query_count == 0

    def test_multiple_schemas(self):
        """Test adapter with different schemas."""
        adapter = MockSUTAdapter(simulate_delay_ms=0)
        adapter.initialize()

        # Schema with users table
        schema1 = SchemaInfo(
            database_name="db1",
            database_type=DatabaseType.MYSQL,
            tables=[TableInfo(name="users", columns=[])],
        )

        # Schema with orders table
        schema2 = SchemaInfo(
            database_name="db2",
            database_type=DatabaseType.POSTGRESQL,
            tables=[TableInfo(name="orders", columns=[])],
        )

        result1 = adapter.query("Count users", schema1)
        result2 = adapter.query("Count orders", schema2)

        assert "users" in result1.generated_sql
        assert "orders" in result2.generated_sql
