"""Unit tests for test runner module."""
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

import pandas as pd

from onb.adapters.database.base import DatabaseAdapter
from onb.adapters.sut.base import SUTAdapter
from onb.core.types import (
    ColumnInfo,
    ComplexityLevel,
    ComparisonResult,
    ComparisonRules,
    DatabaseType,
    NL2SQLResponse,
    Question,
    QuestionResult,
    SchemaInfo,
    TableInfo,
    TestStatus,
    TimingBreakdown,
)
from onb.runner.test_runner import TestRunner


@pytest.fixture
def mock_database_adapter():
    """Create mock database adapter."""
    adapter = MagicMock(spec=DatabaseAdapter)
    adapter.database_type = DatabaseType.MYSQL
    adapter.get_schema_info.return_value = SchemaInfo(
        database_name="test_db",
        database_type=DatabaseType.MYSQL,
        tables=[
            TableInfo(
                name="users",
                columns=[
                    ColumnInfo(name="id", type="int", primary_key=True),
                    ColumnInfo(name="name", type="varchar"),
                    ColumnInfo(name="email", type="varchar"),
                ],
            )
        ],
    )
    adapter.execute_query.return_value = pd.DataFrame({
        "count": [42]
    })
    return adapter


@pytest.fixture
def mock_sut_adapter():
    """Create mock SUT adapter."""
    adapter = MagicMock(spec=SUTAdapter)
    adapter.name = "MockSUT"
    adapter.query.return_value = NL2SQLResponse(
        generated_sql="SELECT COUNT(*) as count FROM users",
        result_dataframe=pd.DataFrame({"count": [42]}),
        success=True,
        total_time_ms=100.0,
        timing_breakdown=TimingBreakdown(
            nl2sql_time_ms=60.0,
            sql_generation_time_ms=30.0,
            sql_execution_time_ms=10.0,
            total_time_ms=100.0,
        ),
    )
    return adapter


@pytest.fixture
def sample_question():
    """Create sample question for testing."""
    return Question(
        id="test_L1_001",
        version="1.0",
        domain="ecommerce",
        complexity=ComplexityLevel.L1,
        question_text={
            "en": "How many users are there?",
            "zh": "有多少用户？"
        },
        golden_sql="SELECT COUNT(*) as count FROM users",
        dependencies={"tables": ["users"]},
        tags=["basic", "count"],
    )


class TestTestRunner:
    """Test TestRunner class."""

    def test_runner_initialization(self, mock_database_adapter, mock_sut_adapter):
        """Test runner initialization."""
        runner = TestRunner(mock_database_adapter, mock_sut_adapter)

        assert runner.database_adapter is mock_database_adapter
        assert runner.sut_adapter is mock_sut_adapter
        assert runner.comparator is not None

    def test_run_question_success(
        self, mock_database_adapter, mock_sut_adapter, sample_question
    ):
        """Test running a single question successfully."""
        runner = TestRunner(mock_database_adapter, mock_sut_adapter)

        result = runner.run_question(sample_question, language="en")

        assert isinstance(result, QuestionResult)
        assert result.question == sample_question
        assert result.status == TestStatus.PASSED
        assert result.comparison_result.match is True
        assert result.sut_response.success is True

        # Verify adapters were called correctly
        mock_database_adapter.get_schema_info.assert_called_once()
        mock_sut_adapter.query.assert_called_once()
        mock_database_adapter.execute_query.assert_called_once_with(
            sample_question.golden_sql
        )

    def test_run_question_chinese_language(
        self, mock_database_adapter, mock_sut_adapter, sample_question
    ):
        """Test running question with Chinese language."""
        runner = TestRunner(mock_database_adapter, mock_sut_adapter)

        result = runner.run_question(sample_question, language="zh")

        # Verify SUT was called with Chinese question
        call_args = mock_sut_adapter.query.call_args
        assert call_args[0][0] == "有多少用户？"
        assert call_args[1]["language"] == "zh"

    def test_run_question_sut_failure(
        self, mock_database_adapter, mock_sut_adapter, sample_question
    ):
        """Test handling SUT query failure."""
        # Configure SUT to fail
        mock_sut_adapter.query.return_value = NL2SQLResponse(
            generated_sql="",
            success=False,
            error="Connection timeout",
            total_time_ms=5000.0,
        )

        runner = TestRunner(mock_database_adapter, mock_sut_adapter)
        result = runner.run_question(sample_question)

        assert result.status == TestStatus.ERROR
        assert result.comparison_result.match is False
        assert "Connection timeout" in result.comparison_result.reason

    def test_run_question_result_mismatch(
        self, mock_database_adapter, mock_sut_adapter, sample_question
    ):
        """Test handling result mismatch."""
        # Configure SUT to return wrong result
        mock_sut_adapter.query.return_value = NL2SQLResponse(
            generated_sql="SELECT COUNT(*) as count FROM users",
            result_dataframe=pd.DataFrame({"count": [99]}),  # Wrong count
            success=True,
            total_time_ms=100.0,
        )

        runner = TestRunner(mock_database_adapter, mock_sut_adapter)
        result = runner.run_question(sample_question)

        assert result.status == TestStatus.FAILED
        assert result.comparison_result.match is False

    def test_run_question_with_custom_comparison_rules(
        self, mock_database_adapter, mock_sut_adapter
    ):
        """Test running question with custom comparison rules."""
        # Create question with custom comparison rules
        question = Question(
            id="test_L2_001",
            version="1.0",
            domain="finance",
            complexity=ComplexityLevel.L2,
            question_text={"en": "Average balance?"},
            golden_sql="SELECT AVG(balance) as avg FROM accounts",
            dependencies={"tables": ["accounts"]},
            comparison_rules=ComparisonRules(
                float_tolerance=0.01,
                float_comparison_mode="absolute_error",
            ),
        )

        # Configure adapters to return float results
        mock_database_adapter.execute_query.return_value = pd.DataFrame({
            "avg": [1000.005]
        })
        mock_sut_adapter.query.return_value = NL2SQLResponse(
            generated_sql="SELECT AVG(balance) as avg FROM accounts",
            result_dataframe=pd.DataFrame({"avg": [1000.01]}),  # Within tolerance
            success=True,
            total_time_ms=100.0,
        )

        runner = TestRunner(mock_database_adapter, mock_sut_adapter)
        result = runner.run_question(question)

        # Should pass because difference is within 0.01 tolerance
        assert result.status == TestStatus.PASSED

    def test_run_test_suite_success(
        self, mock_database_adapter, mock_sut_adapter, sample_question
    ):
        """Test running a complete test suite."""
        runner = TestRunner(mock_database_adapter, mock_sut_adapter)

        questions = [sample_question, sample_question, sample_question]
        report = runner.run_test_suite(questions, language="en")

        assert report.sut_name == "MockSUT"
        assert report.database_type == DatabaseType.MYSQL
        assert report.total_questions == 3
        assert report.correct_count == 3
        assert report.accuracy == 1.0
        assert report.domain == "ecommerce"
        assert len(report.question_results) == 3

        # Verify timing information
        assert report.start_time is not None
        assert report.end_time is not None
        assert report.total_duration_seconds >= 0

    def test_run_test_suite_mixed_results(
        self, mock_database_adapter, mock_sut_adapter, sample_question
    ):
        """Test suite with mixed pass/fail results."""
        runner = TestRunner(mock_database_adapter, mock_sut_adapter)

        # Configure SUT to alternate success/failure
        responses = [
            NL2SQLResponse(
                generated_sql="SELECT COUNT(*) FROM users",
                result_dataframe=pd.DataFrame({"count": [42]}),
                success=True,
                total_time_ms=100.0,
            ),
            NL2SQLResponse(
                generated_sql="SELECT COUNT(*) FROM users",
                result_dataframe=pd.DataFrame({"count": [99]}),  # Wrong
                success=True,
                total_time_ms=100.0,
            ),
            NL2SQLResponse(
                generated_sql="",
                success=False,
                error="Query failed",
                total_time_ms=100.0,
            ),
        ]
        mock_sut_adapter.query.side_effect = responses

        questions = [sample_question, sample_question, sample_question]
        report = runner.run_test_suite(questions)

        assert report.total_questions == 3
        assert report.correct_count == 1
        assert report.accuracy == pytest.approx(0.333, rel=0.01)

        # Check individual result statuses
        assert report.question_results[0].status == TestStatus.PASSED
        assert report.question_results[1].status == TestStatus.FAILED
        assert report.question_results[2].status == TestStatus.ERROR

    def test_run_test_suite_empty_list(self, mock_database_adapter, mock_sut_adapter):
        """Test running suite with empty question list."""
        runner = TestRunner(mock_database_adapter, mock_sut_adapter)

        report = runner.run_test_suite([])

        assert report.total_questions == 0
        assert report.correct_count == 0
        assert report.accuracy == 0.0
        assert report.domain == "unknown"
        assert len(report.question_results) == 0

    def test_run_test_suite_test_id_format(
        self, mock_database_adapter, mock_sut_adapter, sample_question
    ):
        """Test that test_id has correct format."""
        runner = TestRunner(mock_database_adapter, mock_sut_adapter)

        with patch('onb.runner.test_runner.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 15, 10, 30, 45)
            mock_datetime.strftime = datetime.strftime

            report = runner.run_test_suite([sample_question])

            # Test ID should be in format: test_YYYYMMDD_HHMMSS
            assert report.test_id == "test_20240115_103045"

    def test_run_question_null_result_dataframe(
        self, mock_database_adapter, mock_sut_adapter, sample_question
    ):
        """Test handling when SUT returns success but null dataframe."""
        # Configure SUT to return success with null dataframe
        mock_sut_adapter.query.return_value = NL2SQLResponse(
            generated_sql="SELECT COUNT(*) FROM users",
            result_dataframe=None,  # Null dataframe
            success=True,
            total_time_ms=100.0,
        )

        runner = TestRunner(mock_database_adapter, mock_sut_adapter)
        result = runner.run_question(sample_question)

        # Should be treated as error
        assert result.status == TestStatus.ERROR
        assert result.comparison_result.match is False

    def test_run_question_schema_retrieval(
        self, mock_database_adapter, mock_sut_adapter, sample_question
    ):
        """Test that schema is retrieved and passed to SUT."""
        runner = TestRunner(mock_database_adapter, mock_sut_adapter)

        runner.run_question(sample_question)

        # Verify schema was retrieved
        mock_database_adapter.get_schema_info.assert_called_once()

        # Verify schema was passed to SUT
        call_args = mock_sut_adapter.query.call_args
        schema_arg = call_args[0][1]  # Second positional argument
        assert isinstance(schema_arg, SchemaInfo)
        assert schema_arg.database_name == "test_db"

    def test_run_test_suite_quality_level(
        self, mock_database_adapter, mock_sut_adapter, sample_question
    ):
        """Test that quality level is set correctly."""
        runner = TestRunner(mock_database_adapter, mock_sut_adapter)

        report = runner.run_test_suite([sample_question])

        # Currently hardcoded to HIGH
        assert hasattr(report, 'quality')

    def test_multiple_domains_in_suite(
        self, mock_database_adapter, mock_sut_adapter
    ):
        """Test suite with questions from different domains."""
        question1 = Question(
            id="ecommerce_L1_001",
            version="1.0",
            domain="ecommerce",
            complexity=ComplexityLevel.L1,
            question_text={"en": "Q1"},
            golden_sql="SELECT 1",
            dependencies={},
        )

        question2 = Question(
            id="finance_L1_001",
            version="1.0",
            domain="finance",
            complexity=ComplexityLevel.L1,
            question_text={"en": "Q2"},
            golden_sql="SELECT 2",
            dependencies={},
        )

        runner = TestRunner(mock_database_adapter, mock_sut_adapter)
        report = runner.run_test_suite([question1, question2])

        # Should use first question's domain
        assert report.domain == "ecommerce"

    def test_run_question_execution_time_recorded(
        self, mock_database_adapter, mock_sut_adapter, sample_question
    ):
        """Test that execution time is recorded."""
        runner = TestRunner(mock_database_adapter, mock_sut_adapter)

        result = runner.run_question(sample_question)

        assert result.execution_time is not None
        assert isinstance(result.execution_time, datetime)

    def test_comparator_reuse(
        self, mock_database_adapter, mock_sut_adapter, sample_question
    ):
        """Test that default comparator is reused when no custom rules."""
        runner = TestRunner(mock_database_adapter, mock_sut_adapter)

        # Run multiple questions
        result1 = runner.run_question(sample_question)
        result2 = runner.run_question(sample_question)

        # Both should succeed
        assert result1.status == TestStatus.PASSED
        assert result2.status == TestStatus.PASSED
