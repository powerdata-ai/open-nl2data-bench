"""Unit tests for robustness testing module."""
import pandas as pd
import pytest

from onb.evaluation.robustness import (
    DataQualityTester,
    EdgeCaseTester,
    ErrorHandlingTester,
    RobustnessEvaluator,
    RobustnessTestCase,
    RobustnessTestResult,
    RobustnessTestType,
)


class TestRobustnessTestCase:
    """Test RobustnessTestCase dataclass."""

    def test_initialization(self):
        """Test basic initialization."""
        test_case = RobustnessTestCase(
            test_id="test_1",
            test_type=RobustnessTestType.EDGE_CASE,
            description="Test edge case",
            input_data={"query": "SELECT 1"},
            expected_behavior="return_single_row",
        )

        assert test_case.test_id == "test_1"
        assert test_case.test_type == RobustnessTestType.EDGE_CASE
        assert test_case.description == "Test edge case"
        assert test_case.input_data == {"query": "SELECT 1"}
        assert test_case.expected_behavior == "return_single_row"
        assert test_case.metadata == {}

    def test_initialization_with_metadata(self):
        """Test initialization with metadata."""
        test_case = RobustnessTestCase(
            test_id="test_2",
            test_type=RobustnessTestType.ERROR_HANDLING,
            description="Test error",
            input_data={},
            expected_behavior="raise_error",
            metadata={"category": "syntax", "severity": "high"},
        )

        assert test_case.metadata["category"] == "syntax"
        assert test_case.metadata["severity"] == "high"


class TestRobustnessTestResult:
    """Test RobustnessTestResult dataclass."""

    def test_initialization(self):
        """Test basic initialization."""
        test_case = RobustnessTestCase(
            test_id="test_1",
            test_type=RobustnessTestType.EDGE_CASE,
            description="Test",
            input_data={},
            expected_behavior="return_value",
        )

        result = RobustnessTestResult(
            test_case=test_case,
            passed=True,
            actual_behavior="return_value",
        )

        assert result.test_case == test_case
        assert result.passed is True
        assert result.actual_behavior == "return_value"
        assert result.error_message is None
        assert result.execution_time_ms is None

    def test_initialization_with_error(self):
        """Test initialization with error."""
        test_case = RobustnessTestCase(
            test_id="test_2",
            test_type=RobustnessTestType.ERROR_HANDLING,
            description="Test",
            input_data={},
            expected_behavior="raise_error",
        )

        result = RobustnessTestResult(
            test_case=test_case,
            passed=True,
            actual_behavior="raised_ValueError",
            error_message="Test error message",
            execution_time_ms=10.5,
        )

        assert result.error_message == "Test error message"
        assert result.execution_time_ms == 10.5


class TestEdgeCaseTester:
    """Test EdgeCaseTester class."""

    def test_initialization(self):
        """Test tester initialization."""
        tester = EdgeCaseTester()

        assert len(tester.test_cases) > 0
        # Should have standard edge cases
        test_ids = [tc.test_id for tc in tester.test_cases]
        assert "edge_empty_result" in test_ids
        assert "edge_single_row" in test_ids
        assert "edge_special_chars" in test_ids
        assert "edge_null_values" in test_ids

    def test_add_test_case(self):
        """Test adding custom test case."""
        tester = EdgeCaseTester()
        initial_count = len(tester.test_cases)

        custom_case = RobustnessTestCase(
            test_id="custom_edge",
            test_type=RobustnessTestType.EDGE_CASE,
            description="Custom edge case",
            input_data={},
            expected_behavior="custom_behavior",
        )

        tester.add_test_case(custom_case)

        assert len(tester.test_cases) == initial_count + 1
        assert custom_case in tester.test_cases

    def test_get_test_cases_all(self):
        """Test getting all test cases."""
        tester = EdgeCaseTester()
        cases = tester.get_test_cases()

        assert len(cases) == len(tester.test_cases)
        assert all(isinstance(tc, RobustnessTestCase) for tc in cases)

    def test_get_test_cases_filtered(self):
        """Test getting filtered test cases."""
        tester = EdgeCaseTester()

        # All edge cases should be of EDGE_CASE type
        edge_cases = tester.get_test_cases(test_type=RobustnessTestType.EDGE_CASE)

        assert len(edge_cases) > 0
        assert all(tc.test_type == RobustnessTestType.EDGE_CASE for tc in edge_cases)

        # No error handling cases
        error_cases = tester.get_test_cases(
            test_type=RobustnessTestType.ERROR_HANDLING
        )
        assert len(error_cases) == 0

    def test_standard_edge_cases_content(self):
        """Test standard edge cases have proper content."""
        tester = EdgeCaseTester()

        # Check empty result case
        empty_case = next(
            tc for tc in tester.test_cases if tc.test_id == "edge_empty_result"
        )
        assert "empty" in empty_case.description.lower()
        assert empty_case.expected_behavior == "return_empty_dataframe"

        # Check NULL values case
        null_case = next(
            tc for tc in tester.test_cases if tc.test_id == "edge_null_values"
        )
        assert "NULL" in null_case.description or "null" in null_case.description
        assert "handle" in null_case.expected_behavior.lower()


class TestErrorHandlingTester:
    """Test ErrorHandlingTester class."""

    def test_initialization(self):
        """Test tester initialization."""
        tester = ErrorHandlingTester()

        assert len(tester.test_cases) > 0
        # Should have standard error cases
        test_ids = [tc.test_id for tc in tester.test_cases]
        assert "error_malformed_sql" in test_ids
        assert "error_invalid_table" in test_ids
        assert "error_division_zero" in test_ids

    def test_add_test_case(self):
        """Test adding custom test case."""
        tester = ErrorHandlingTester()
        initial_count = len(tester.test_cases)

        custom_case = RobustnessTestCase(
            test_id="custom_error",
            test_type=RobustnessTestType.ERROR_HANDLING,
            description="Custom error case",
            input_data={},
            expected_behavior="raise_error",
        )

        tester.add_test_case(custom_case)

        assert len(tester.test_cases) == initial_count + 1

    def test_get_test_cases(self):
        """Test getting all test cases."""
        tester = ErrorHandlingTester()
        cases = tester.get_test_cases()

        assert len(cases) > 0
        assert all(tc.test_type == RobustnessTestType.ERROR_HANDLING for tc in cases)

    def test_standard_error_cases_content(self):
        """Test standard error cases have proper content."""
        tester = ErrorHandlingTester()

        # Check malformed SQL case
        malformed_case = next(
            tc for tc in tester.test_cases if tc.test_id == "error_malformed_sql"
        )
        assert "malformed" in malformed_case.description.lower() or "syntax" in malformed_case.description.lower()
        assert "error" in malformed_case.expected_behavior.lower()


class TestDataQualityTester:
    """Test DataQualityTester class."""

    def test_initialization(self):
        """Test tester initialization."""
        tester = DataQualityTester()

        assert len(tester.test_cases) > 0
        # Should have standard quality cases
        test_ids = [tc.test_id for tc in tester.test_cases]
        assert "quality_duplicates" in test_ids
        assert "quality_whitespace" in test_ids

    def test_add_test_case(self):
        """Test adding custom test case."""
        tester = DataQualityTester()
        initial_count = len(tester.test_cases)

        custom_case = RobustnessTestCase(
            test_id="custom_quality",
            test_type=RobustnessTestType.DATA_QUALITY,
            description="Custom quality case",
            input_data={},
            expected_behavior="preserve_data",
        )

        tester.add_test_case(custom_case)

        assert len(tester.test_cases) == initial_count + 1

    def test_get_test_cases(self):
        """Test getting all test cases."""
        tester = DataQualityTester()
        cases = tester.get_test_cases()

        assert len(cases) > 0
        assert all(tc.test_type == RobustnessTestType.DATA_QUALITY for tc in cases)


class TestRobustnessEvaluator:
    """Test RobustnessEvaluator class."""

    def test_initialization(self):
        """Test evaluator initialization."""
        evaluator = RobustnessEvaluator()

        assert evaluator.edge_tester is not None
        assert evaluator.error_tester is not None
        assert evaluator.quality_tester is not None
        assert evaluator.results == []

    def test_run_test_success(self):
        """Test running a successful test."""
        evaluator = RobustnessEvaluator()

        test_case = RobustnessTestCase(
            test_id="test_success",
            test_type=RobustnessTestType.EDGE_CASE,
            description="Test success",
            input_data={"value": 42},
            expected_behavior="return_value",
        )

        def test_func(input_data):
            return input_data["value"]

        result = evaluator.run_test(test_case, test_func)

        assert result.passed is True
        assert result.actual_behavior == "return_value"
        assert result.error_message is None
        assert result.execution_time_ms is not None
        assert result.execution_time_ms > 0

    def test_run_test_dataframe_empty(self):
        """Test running a test that returns empty DataFrame."""
        evaluator = RobustnessEvaluator()

        test_case = RobustnessTestCase(
            test_id="test_empty_df",
            test_type=RobustnessTestType.EDGE_CASE,
            description="Empty DataFrame",
            input_data={},
            expected_behavior="return_empty_dataframe",
        )

        def test_func(input_data):
            return pd.DataFrame()

        result = evaluator.run_test(test_case, test_func)

        assert result.passed is True
        assert result.actual_behavior == "return_empty_dataframe"

    def test_run_test_dataframe_single_row(self):
        """Test running a test that returns single-row DataFrame."""
        evaluator = RobustnessEvaluator()

        test_case = RobustnessTestCase(
            test_id="test_single_row",
            test_type=RobustnessTestType.EDGE_CASE,
            description="Single row",
            input_data={},
            expected_behavior="return_single_row",
        )

        def test_func(input_data):
            return pd.DataFrame({"col": [1]})

        result = evaluator.run_test(test_case, test_func)

        assert result.passed is True
        assert result.actual_behavior == "return_single_row"

    def test_run_test_error_handling(self):
        """Test running a test that expects an error."""
        evaluator = RobustnessEvaluator()

        test_case = RobustnessTestCase(
            test_id="test_error",
            test_type=RobustnessTestType.ERROR_HANDLING,
            description="Should raise error",
            input_data={},
            expected_behavior="raise_error",
        )

        def test_func(input_data):
            raise ValueError("Expected error")

        result = evaluator.run_test(test_case, test_func)

        assert result.passed is True  # Because we expected an error
        assert "raised_ValueError" in result.actual_behavior
        assert result.error_message == "Expected error"

    def test_run_test_unexpected_error(self):
        """Test running a test that raises unexpected error."""
        evaluator = RobustnessEvaluator()

        test_case = RobustnessTestCase(
            test_id="test_unexpected_error",
            test_type=RobustnessTestType.EDGE_CASE,
            description="Should not error",
            input_data={},
            expected_behavior="return_value",
        )

        def test_func(input_data):
            raise RuntimeError("Unexpected error")

        result = evaluator.run_test(test_case, test_func)

        assert result.passed is False  # Unexpected error
        assert "raised_RuntimeError" in result.actual_behavior

    def test_run_multiple_tests(self):
        """Test running multiple tests."""
        evaluator = RobustnessEvaluator()

        test_cases = [
            RobustnessTestCase(
                test_id=f"test_{i}",
                test_type=RobustnessTestType.EDGE_CASE,
                description=f"Test {i}",
                input_data={"value": i},
                expected_behavior="return_value",
            )
            for i in range(5)
        ]

        def test_func(input_data):
            return input_data["value"]

        for test_case in test_cases:
            evaluator.run_test(test_case, test_func)

        assert len(evaluator.results) == 5
        assert all(r.passed for r in evaluator.results)

    def test_get_summary_empty(self):
        """Test getting summary with no results."""
        evaluator = RobustnessEvaluator()
        summary = evaluator.get_summary()

        assert summary["total_tests"] == 0
        assert summary["passed"] == 0
        assert summary["failed"] == 0
        assert summary["pass_rate"] == 0.0

    def test_get_summary_with_results(self):
        """Test getting summary with results."""
        evaluator = RobustnessEvaluator()

        # Run some tests
        test_cases = [
            RobustnessTestCase(
                test_id="pass_1",
                test_type=RobustnessTestType.EDGE_CASE,
                description="Pass",
                input_data={},
                expected_behavior="return_value",
            ),
            RobustnessTestCase(
                test_id="pass_2",
                test_type=RobustnessTestType.ERROR_HANDLING,
                description="Pass",
                input_data={},
                expected_behavior="return_value",
            ),
            RobustnessTestCase(
                test_id="fail_1",
                test_type=RobustnessTestType.EDGE_CASE,
                description="Fail",
                input_data={},
                expected_behavior="return_different",
            ),
        ]

        def test_func(input_data):
            return 42

        for test_case in test_cases:
            evaluator.run_test(test_case, test_func)

        summary = evaluator.get_summary()

        assert summary["total_tests"] == 3
        assert summary["passed"] == 2
        assert summary["failed"] == 1
        assert summary["pass_rate"] == pytest.approx(2 / 3)
        assert "by_type" in summary
        assert "edge_case" in summary["by_type"]
        assert "error_handling" in summary["by_type"]

    def test_reset(self):
        """Test resetting evaluator."""
        evaluator = RobustnessEvaluator()

        # Run some tests
        test_case = RobustnessTestCase(
            test_id="test",
            test_type=RobustnessTestType.EDGE_CASE,
            description="Test",
            input_data={},
            expected_behavior="return_value",
        )

        evaluator.run_test(test_case, lambda x: 42)
        assert len(evaluator.results) == 1

        evaluator.reset()
        assert len(evaluator.results) == 0

    def test_behavior_matches_exact(self):
        """Test exact behavior matching."""
        evaluator = RobustnessEvaluator()

        assert evaluator._behavior_matches("return_value", "return_value")
        assert not evaluator._behavior_matches("return_value", "return_different")

    def test_behavior_matches_error(self):
        """Test error behavior matching."""
        evaluator = RobustnessEvaluator()

        # Should match if we expect error and get raised_SomeError
        assert evaluator._behavior_matches("raised_ValueError", "raise_error")
        assert evaluator._behavior_matches(
            "raised_RuntimeError", "raise_syntax_error"
        )

    def test_behavior_matches_handle(self):
        """Test handle behavior matching."""
        evaluator = RobustnessEvaluator()

        # If we expect handling, not raising an error is OK
        assert evaluator._behavior_matches("return_value", "handle_gracefully")
        assert not evaluator._behavior_matches("raised_Error", "handle_gracefully")


class TestRobustnessTestType:
    """Test RobustnessTestType enum."""

    def test_enum_values(self):
        """Test all enum values."""
        assert RobustnessTestType.EDGE_CASE == "edge_case"
        assert RobustnessTestType.ERROR_HANDLING == "error_handling"
        assert RobustnessTestType.BOUNDARY_CONDITION == "boundary_condition"
        assert RobustnessTestType.DATA_QUALITY == "data_quality"
        assert RobustnessTestType.MALFORMED_INPUT == "malformed_input"
        assert RobustnessTestType.TIMEOUT == "timeout"
        assert RobustnessTestType.CONCURRENT_STRESS == "concurrent_stress"
