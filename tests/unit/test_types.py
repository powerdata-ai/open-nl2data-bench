"""Unit tests for core types module."""
import pandas as pd
import pytest

from onb.core.types import (
    ColumnInfo,
    ComparisonRules,
    ComplexityLevel,
    DatabaseConfig,
    DatabaseType,
    NL2SQLResponse,
    PerformanceMetrics,
    QualityLevel,
    Question,
    QuestionResult,
    SchemaInfo,
    TableInfo,
    TestStatus,
    TimingBreakdown,
    TokenUsage,
)


class TestEnums:
    """Test enum types."""

    def test_database_type_values(self):
        """Test DatabaseType enum values."""
        assert DatabaseType.MYSQL.value == "mysql"
        assert DatabaseType.POSTGRESQL.value == "postgresql"
        assert DatabaseType.CLICKHOUSE.value == "clickhouse"

    def test_quality_level_values(self):
        """Test QualityLevel enum values."""
        assert QualityLevel.HIGH.value == "high"
        assert QualityLevel.MEDIUM.value == "medium"
        assert QualityLevel.LOW.value == "low"

    def test_complexity_level_values(self):
        """Test ComplexityLevel enum values."""
        assert ComplexityLevel.L1.value == "L1"
        assert ComplexityLevel.L6.value == "L6"

    def test_test_status_values(self):
        """Test TestStatus enum values."""
        assert TestStatus.PENDING.value == "pending"
        assert TestStatus.PASSED.value == "passed"
        assert TestStatus.FAILED.value == "failed"


class TestColumnInfo:
    """Test ColumnInfo dataclass."""

    def test_column_info_creation(self):
        """Test creating ColumnInfo instance."""
        col = ColumnInfo(
            name="user_id",
            type="BIGINT",
            nullable=False,
            primary_key=True,
            comment="User ID",
        )
        assert col.name == "user_id"
        assert col.type == "BIGINT"
        assert col.nullable is False
        assert col.primary_key is True
        assert col.comment == "User ID"

    def test_column_info_defaults(self):
        """Test ColumnInfo default values."""
        col = ColumnInfo(name="test_col", type="VARCHAR(50)")
        assert col.nullable is True
        assert col.primary_key is False
        assert col.foreign_key is None
        assert col.comment is None

    def test_column_info_to_dict(self):
        """Test ColumnInfo to_dict conversion."""
        col = ColumnInfo(name="user_id", type="BIGINT", nullable=False)
        col_dict = col.to_dict()

        assert isinstance(col_dict, dict)
        assert col_dict["name"] == "user_id"
        assert col_dict["type"] == "BIGINT"
        assert col_dict["nullable"] is False


class TestTableInfo:
    """Test TableInfo dataclass."""

    def test_table_info_creation(self):
        """Test creating TableInfo instance."""
        columns = [
            ColumnInfo(name="id", type="BIGINT", primary_key=True),
            ColumnInfo(name="name", type="VARCHAR(100)"),
        ]

        table = TableInfo(name="users", columns=columns, quality=QualityLevel.HIGH)

        assert table.name == "users"
        assert len(table.columns) == 2
        assert table.quality == QualityLevel.HIGH

    def test_table_info_to_dict(self):
        """Test TableInfo to_dict conversion."""
        columns = [ColumnInfo(name="id", type="BIGINT")]
        table = TableInfo(name="test_table", columns=columns)

        table_dict = table.to_dict()
        assert table_dict["name"] == "test_table"
        assert len(table_dict["columns"]) == 1
        assert table_dict["quality"] == "high"


class TestSchemaInfo:
    """Test SchemaInfo dataclass."""

    def test_schema_info_creation(self, sample_schema_info):
        """Test creating SchemaInfo instance."""
        assert sample_schema_info.database_name == "test_db"
        assert sample_schema_info.database_type == DatabaseType.MYSQL
        assert len(sample_schema_info.tables) == 1

    def test_get_table_exists(self, sample_schema_info):
        """Test getting existing table."""
        table = sample_schema_info.get_table("users")
        assert table is not None
        assert table.name == "users"

    def test_get_table_not_exists(self, sample_schema_info):
        """Test getting non-existent table."""
        table = sample_schema_info.get_table("nonexistent")
        assert table is None

    def test_schema_info_to_dict(self, sample_schema_info):
        """Test SchemaInfo to_dict conversion."""
        schema_dict = sample_schema_info.to_dict()

        assert schema_dict["database"] == "test_db"
        assert schema_dict["database_type"] == "mysql"
        assert len(schema_dict["tables"]) == 1


class TestComparisonRules:
    """Test ComparisonRules dataclass."""

    def test_comparison_rules_defaults(self):
        """Test ComparisonRules default values."""
        rules = ComparisonRules()

        assert rules.row_order_matters is True
        assert rules.column_order_matters is True
        assert rules.float_tolerance == 1e-6
        assert rules.float_comparison_mode == "relative_error"

    def test_comparison_rules_custom(self):
        """Test ComparisonRules with custom values."""
        rules = ComparisonRules(
            row_order_matters=False,
            float_tolerance=1e-2,
            string_case_sensitive=True,
        )

        assert rules.row_order_matters is False
        assert rules.float_tolerance == 1e-2
        assert rules.string_case_sensitive is True

    def test_comparison_rules_to_dict(self):
        """Test ComparisonRules to_dict conversion."""
        rules = ComparisonRules(float_tolerance=1e-3)
        rules_dict = rules.to_dict()

        assert isinstance(rules_dict, dict)
        assert rules_dict["float_tolerance"] == 1e-3


class TestQuestion:
    """Test Question dataclass."""

    def test_question_creation(self, sample_question):
        """Test creating Question instance."""
        assert sample_question.id == "test_L1_001"
        assert sample_question.complexity == ComplexityLevel.L1
        assert sample_question.domain == "test"

    def test_get_question_text(self, sample_question):
        """Test getting question text in different languages."""
        assert sample_question.get_question("zh") == "查询所有用户"
        assert sample_question.get_question("en") == "Select all users"

    def test_get_question_text_fallback(self, sample_question):
        """Test question text fallback to English."""
        text = sample_question.get_question("fr")  # Non-existent language
        assert text == "Select all users"  # Should fallback to English

    def test_question_to_dict(self, sample_question):
        """Test Question to_dict conversion."""
        q_dict = sample_question.to_dict()

        assert q_dict["id"] == "test_L1_001"
        assert q_dict["complexity"] == "L1"
        assert q_dict["domain"] == "test"
        assert "tables" in q_dict["dependencies"]


class TestTokenUsage:
    """Test TokenUsage dataclass."""

    def test_token_usage_creation(self):
        """Test creating TokenUsage instance."""
        usage = TokenUsage(input_tokens=100, output_tokens=50, total_tokens=150)

        assert usage.input_tokens == 100
        assert usage.output_tokens == 50
        assert usage.total_tokens == 150

    def test_token_usage_to_dict(self):
        """Test TokenUsage to_dict conversion."""
        usage = TokenUsage(input_tokens=100, output_tokens=50, total_tokens=150)
        usage_dict = usage.to_dict()

        assert usage_dict["input_tokens"] == 100
        assert usage_dict["total_tokens"] == 150


class TestTimingBreakdown:
    """Test TimingBreakdown dataclass."""

    def test_timing_breakdown_creation(self):
        """Test creating TimingBreakdown instance."""
        timing = TimingBreakdown(
            nl2sql_time_ms=100.0,
            sql_generation_time_ms=50.0,
            sql_execution_time_ms=200.0,
            total_time_ms=350.0,
        )

        assert timing.nl2sql_time_ms == 100.0
        assert timing.total_time_ms == 350.0

    def test_timing_breakdown_optional_fields(self):
        """Test TimingBreakdown with optional fields."""
        timing = TimingBreakdown(total_time_ms=500.0)

        assert timing.total_time_ms == 500.0
        assert timing.nl2sql_time_ms is None


class TestNL2SQLResponse:
    """Test NL2SQLResponse dataclass."""

    def test_nl2sql_response_success(self):
        """Test successful NL2SQL response."""
        df = pd.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]})

        response = NL2SQLResponse(
            generated_sql="SELECT * FROM users",
            result_dataframe=df,
            success=True,
            total_time_ms=500.0,
        )

        assert response.success is True
        assert response.generated_sql == "SELECT * FROM users"
        assert len(response.result_dataframe) == 2

    def test_nl2sql_response_with_tokens(self):
        """Test NL2SQL response with token usage."""
        token_usage = TokenUsage(input_tokens=100, output_tokens=50, total_tokens=150)

        response = NL2SQLResponse(
            generated_sql="SELECT * FROM users",
            token_usage=token_usage,
            token_available=True,
        )

        assert response.token_available is True
        assert response.token_usage.total_tokens == 150

    def test_nl2sql_response_error(self):
        """Test failed NL2SQL response."""
        response = NL2SQLResponse(
            generated_sql="",
            success=False,
            error="Table not found",
        )

        assert response.success is False
        assert response.error == "Table not found"

    def test_nl2sql_response_to_dict(self):
        """Test NL2SQLResponse to_dict conversion."""
        df = pd.DataFrame({"id": [1]})
        response = NL2SQLResponse(generated_sql="SELECT 1", result_dataframe=df)

        response_dict = response.to_dict()
        assert response_dict["generated_sql"] == "SELECT 1"
        assert response_dict["result_rows"] == 1


class TestPerformanceMetrics:
    """Test PerformanceMetrics dataclass."""

    def test_performance_metrics_creation(self):
        """Test creating PerformanceMetrics instance."""
        metrics = PerformanceMetrics(
            median_time_ms=500.0,
            mean_time_ms=520.0,
            p50=500.0,
            p95=800.0,
            p99=950.0,
            min_time_ms=400.0,
            max_time_ms=1000.0,
            std_dev=150.0,
            measurements=[400, 500, 600, 800, 1000],
        )

        assert metrics.median_time_ms == 500.0
        assert metrics.p95 == 800.0
        assert len(metrics.measurements) == 5

    def test_performance_metrics_to_dict(self):
        """Test PerformanceMetrics to_dict conversion."""
        metrics = PerformanceMetrics(
            median_time_ms=500.0,
            mean_time_ms=500.0,
            p50=500.0,
            p95=800.0,
            p99=900.0,
            min_time_ms=400.0,
            max_time_ms=1000.0,
            std_dev=100.0,
        )

        metrics_dict = metrics.to_dict()
        assert metrics_dict["median_time_ms"] == 500.0
        assert metrics_dict["p95"] == 800.0


class TestDatabaseConfig:
    """Test DatabaseConfig dataclass."""

    def test_database_config_creation(self, sample_database_config):
        """Test creating DatabaseConfig instance."""
        assert sample_database_config.type == DatabaseType.MYSQL
        assert sample_database_config.host == "localhost"
        assert sample_database_config.port == 3306

    def test_database_config_to_dict(self, sample_database_config):
        """Test DatabaseConfig to_dict (without password)."""
        config_dict = sample_database_config.to_dict()

        assert config_dict["type"] == "mysql"
        assert config_dict["host"] == "localhost"
        assert "password" not in config_dict  # Sensitive data excluded
