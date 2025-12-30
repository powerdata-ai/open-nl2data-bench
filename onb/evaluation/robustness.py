"""
Robustness testing module for OpenNL2Data-Bench.

This module provides comprehensive robustness evaluation including:
- Edge case testing (empty results, special characters, NULL values)
- Error handling validation (malformed queries, timeouts, connection errors)
- Boundary condition testing (max/min values, overflow)
- Data quality testing (duplicates, inconsistent types)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import pandas as pd


class RobustnessTestType(str, Enum):
    """Types of robustness tests."""

    EDGE_CASE = "edge_case"
    ERROR_HANDLING = "error_handling"
    BOUNDARY_CONDITION = "boundary_condition"
    DATA_QUALITY = "data_quality"
    MALFORMED_INPUT = "malformed_input"
    TIMEOUT = "timeout"
    CONCURRENT_STRESS = "concurrent_stress"


@dataclass
class RobustnessTestCase:
    """A single robustness test case."""

    test_id: str
    test_type: RobustnessTestType
    description: str
    input_data: Any
    expected_behavior: str  # What should happen (e.g., "return_empty", "raise_error", "handle_gracefully")
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RobustnessTestResult:
    """Result of a robustness test."""

    test_case: RobustnessTestCase
    passed: bool
    actual_behavior: str
    error_message: Optional[str] = None
    execution_time_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class EdgeCaseTester:
    """
    Test edge cases and boundary conditions.

    Tests include:
    - Empty results
    - Single row/column results
    - Very large results
    - Special characters in strings
    - NULL values
    - Unicode and emoji handling
    """

    def __init__(self):
        """Initialize edge case tester."""
        self.test_cases: List[RobustnessTestCase] = []
        self._generate_edge_cases()

    def _generate_edge_cases(self) -> None:
        """Generate standard edge case test scenarios."""
        # Empty result set
        self.test_cases.append(
            RobustnessTestCase(
                test_id="edge_empty_result",
                test_type=RobustnessTestType.EDGE_CASE,
                description="Query returns empty result set",
                input_data={"query": "SELECT * FROM table WHERE 1=0"},
                expected_behavior="return_empty_dataframe",
            )
        )

        # Single row
        self.test_cases.append(
            RobustnessTestCase(
                test_id="edge_single_row",
                test_type=RobustnessTestType.EDGE_CASE,
                description="Query returns single row",
                input_data={"query": "SELECT 1 as value LIMIT 1"},
                expected_behavior="return_single_row",
            )
        )

        # Special characters
        self.test_cases.append(
            RobustnessTestCase(
                test_id="edge_special_chars",
                test_type=RobustnessTestType.EDGE_CASE,
                description="String with special characters (quotes, backslash, newline)",
                input_data={
                    "query": "SELECT 'test\\'s \"value\" with\\nnewline' as text"
                },
                expected_behavior="handle_special_chars",
            )
        )

        # NULL values
        self.test_cases.append(
            RobustnessTestCase(
                test_id="edge_null_values",
                test_type=RobustnessTestType.EDGE_CASE,
                description="Result contains NULL values",
                input_data={"query": "SELECT NULL as col1, 'value' as col2"},
                expected_behavior="handle_nulls",
            )
        )

        # Unicode and emoji
        self.test_cases.append(
            RobustnessTestCase(
                test_id="edge_unicode_emoji",
                test_type=RobustnessTestType.EDGE_CASE,
                description="Unicode characters and emoji in strings",
                input_data={"query": "SELECT '你好🌍' as greeting"},
                expected_behavior="handle_unicode",
            )
        )

        # Very large numbers
        self.test_cases.append(
            RobustnessTestCase(
                test_id="edge_large_numbers",
                test_type=RobustnessTestType.EDGE_CASE,
                description="Very large integer and float values",
                input_data={
                    "query": "SELECT 9223372036854775807 as max_bigint, 1.7976931348623157e+308 as max_float"
                },
                expected_behavior="handle_large_numbers",
            )
        )

    def add_test_case(self, test_case: RobustnessTestCase) -> None:
        """
        Add a custom test case.

        Args:
            test_case: Test case to add
        """
        self.test_cases.append(test_case)

    def get_test_cases(
        self, test_type: Optional[RobustnessTestType] = None
    ) -> List[RobustnessTestCase]:
        """
        Get test cases, optionally filtered by type.

        Args:
            test_type: Optional filter by test type

        Returns:
            List of test cases
        """
        if test_type:
            return [tc for tc in self.test_cases if tc.test_type == test_type]
        return self.test_cases


class ErrorHandlingTester:
    """
    Test error handling and recovery.

    Tests include:
    - Malformed SQL
    - Invalid table/column names
    - Type mismatches
    - Division by zero
    - Connection errors
    - Query timeouts
    """

    def __init__(self):
        """Initialize error handling tester."""
        self.test_cases: List[RobustnessTestCase] = []
        self._generate_error_cases()

    def _generate_error_cases(self) -> None:
        """Generate standard error test scenarios."""
        # Malformed SQL
        self.test_cases.append(
            RobustnessTestCase(
                test_id="error_malformed_sql",
                test_type=RobustnessTestType.ERROR_HANDLING,
                description="Malformed SQL query",
                input_data={"query": "SELCT * FORM table WHRE 1=1"},
                expected_behavior="raise_syntax_error",
            )
        )

        # Invalid table
        self.test_cases.append(
            RobustnessTestCase(
                test_id="error_invalid_table",
                test_type=RobustnessTestType.ERROR_HANDLING,
                description="Query references non-existent table",
                input_data={"query": "SELECT * FROM nonexistent_table"},
                expected_behavior="raise_table_not_found_error",
            )
        )

        # Invalid column
        self.test_cases.append(
            RobustnessTestCase(
                test_id="error_invalid_column",
                test_type=RobustnessTestType.ERROR_HANDLING,
                description="Query references non-existent column",
                input_data={"query": "SELECT nonexistent_column FROM table"},
                expected_behavior="raise_column_not_found_error",
            )
        )

        # Division by zero
        self.test_cases.append(
            RobustnessTestCase(
                test_id="error_division_zero",
                test_type=RobustnessTestType.ERROR_HANDLING,
                description="Division by zero in query",
                input_data={"query": "SELECT 1 / 0 as result"},
                expected_behavior="raise_division_error_or_return_null",
            )
        )

        # Type mismatch
        self.test_cases.append(
            RobustnessTestCase(
                test_id="error_type_mismatch",
                test_type=RobustnessTestType.ERROR_HANDLING,
                description="Type mismatch in comparison",
                input_data={"query": "SELECT * FROM table WHERE number_column = 'text'"},
                expected_behavior="handle_type_coercion_or_error",
            )
        )

    def add_test_case(self, test_case: RobustnessTestCase) -> None:
        """
        Add a custom test case.

        Args:
            test_case: Test case to add
        """
        self.test_cases.append(test_case)

    def get_test_cases(self) -> List[RobustnessTestCase]:
        """
        Get all error handling test cases.

        Returns:
            List of test cases
        """
        return self.test_cases


class DataQualityTester:
    """
    Test data quality issues.

    Tests include:
    - Duplicate rows
    - Mixed data types in columns
    - Inconsistent NULL handling
    - Whitespace handling
    - Case sensitivity
    """

    def __init__(self):
        """Initialize data quality tester."""
        self.test_cases: List[RobustnessTestCase] = []
        self._generate_quality_cases()

    def _generate_quality_cases(self) -> None:
        """Generate standard data quality test scenarios."""
        # Duplicate rows
        self.test_cases.append(
            RobustnessTestCase(
                test_id="quality_duplicates",
                test_type=RobustnessTestType.DATA_QUALITY,
                description="Result contains duplicate rows",
                input_data={
                    "query": "SELECT 'A' as val UNION ALL SELECT 'A' as val"
                },
                expected_behavior="preserve_duplicates",
            )
        )

        # Whitespace variations
        self.test_cases.append(
            RobustnessTestCase(
                test_id="quality_whitespace",
                test_type=RobustnessTestType.DATA_QUALITY,
                description="Strings with leading/trailing whitespace",
                input_data={"query": "SELECT '  value  ' as text"},
                expected_behavior="preserve_whitespace",
            )
        )

        # Case sensitivity
        self.test_cases.append(
            RobustnessTestCase(
                test_id="quality_case_sensitivity",
                test_type=RobustnessTestType.DATA_QUALITY,
                description="Column names with different cases",
                input_data={
                    "query": "SELECT 'Value' as MixedCase, 'value' as lowercase"
                },
                expected_behavior="handle_case_consistently",
            )
        )

        # Mixed NULL and empty string
        self.test_cases.append(
            RobustnessTestCase(
                test_id="quality_null_vs_empty",
                test_type=RobustnessTestType.DATA_QUALITY,
                description="Distinguish NULL from empty string",
                input_data={"query": "SELECT NULL as col1, '' as col2"},
                expected_behavior="distinguish_null_empty",
            )
        )

    def add_test_case(self, test_case: RobustnessTestCase) -> None:
        """
        Add a custom test case.

        Args:
            test_case: Test case to add
        """
        self.test_cases.append(test_case)

    def get_test_cases(self) -> List[RobustnessTestCase]:
        """
        Get all data quality test cases.

        Returns:
            List of test cases
        """
        return self.test_cases


class RobustnessEvaluator:
    """
    Main robustness evaluator that runs all robustness tests.

    Aggregates results and provides comprehensive robustness score.
    """

    def __init__(self):
        """Initialize robustness evaluator."""
        self.edge_tester = EdgeCaseTester()
        self.error_tester = ErrorHandlingTester()
        self.quality_tester = DataQualityTester()
        self.results: List[RobustnessTestResult] = []

    def run_test(
        self, test_case: RobustnessTestCase, test_func: Callable
    ) -> RobustnessTestResult:
        """
        Run a single robustness test.

        Args:
            test_case: Test case to run
            test_func: Function to execute the test (takes input_data, returns result)

        Returns:
            Test result
        """
        import time

        start_time = time.perf_counter()
        actual_behavior = ""
        error_message = None
        passed = False

        try:
            result = test_func(test_case.input_data)
            actual_behavior = self._classify_behavior(result, test_case)

            # Check if actual matches expected
            passed = self._behavior_matches(
                actual_behavior, test_case.expected_behavior
            )

        except Exception as e:
            actual_behavior = f"raised_{type(e).__name__}"
            error_message = str(e)
            passed = self._behavior_matches(
                actual_behavior, test_case.expected_behavior
            )

        end_time = time.perf_counter()
        execution_time_ms = (end_time - start_time) * 1000

        result_obj = RobustnessTestResult(
            test_case=test_case,
            passed=passed,
            actual_behavior=actual_behavior,
            error_message=error_message,
            execution_time_ms=execution_time_ms,
        )

        self.results.append(result_obj)
        return result_obj

    def _classify_behavior(self, result: Any, test_case: RobustnessTestCase) -> str:
        """Classify the actual behavior based on the result."""
        if isinstance(result, pd.DataFrame):
            if result.empty:
                return "return_empty_dataframe"
            elif len(result) == 1:
                return "return_single_row"
            else:
                return "return_dataframe"
        elif result is None:
            return "return_none"
        else:
            return "return_value"

    def _behavior_matches(self, actual: str, expected: str) -> bool:
        """Check if actual behavior matches expected."""
        # Exact match
        if actual == expected:
            return True

        # Partial matches for flexible expectations
        if "error" in expected.lower() and "raised" in actual:
            return True

        if "handle" in expected.lower():
            # If we expect handling, not raising an error is a pass
            return "raised" not in actual

        return False

    def get_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive robustness summary.

        Returns:
            Dictionary with robustness metrics
        """
        if not self.results:
            return {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "pass_rate": 0.0,
                "by_type": {},
            }

        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)

        # Group by test type
        by_type: Dict[str, Dict[str, int]] = {}
        for result in self.results:
            test_type = result.test_case.test_type.value
            if test_type not in by_type:
                by_type[test_type] = {"total": 0, "passed": 0, "failed": 0}

            by_type[test_type]["total"] += 1
            if result.passed:
                by_type[test_type]["passed"] += 1
            else:
                by_type[test_type]["failed"] += 1

        return {
            "total_tests": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": passed / total if total > 0 else 0.0,
            "by_type": by_type,
        }

    def reset(self) -> None:
        """Reset all test results."""
        self.results.clear()
