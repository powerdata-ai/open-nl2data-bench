"""Unit tests for result comparator module."""
import numpy as np
import pandas as pd
import pytest
from datetime import datetime, timezone

from onb.core.types import ComparisonRules
from onb.evaluation.comparator import ResultComparator, compare_results


class TestResultComparator:
    """Test ResultComparator class."""

    def test_exact_match(self):
        """Test exact DataFrame match."""
        df1 = pd.DataFrame({"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"]})
        df2 = pd.DataFrame({"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"]})

        comparator = ResultComparator()
        result = comparator.compare(df1, df2)

        assert result.match is True
        assert result.reason == "Results match"

    def test_shape_mismatch_rows(self):
        """Test shape mismatch - different row counts."""
        df1 = pd.DataFrame({"id": [1, 2, 3]})
        df2 = pd.DataFrame({"id": [1, 2]})

        comparator = ResultComparator()
        result = comparator.compare(df1, df2)

        assert result.match is False
        assert result.reason == "Shape mismatch"
        assert result.details["expected_rows"] == 3
        assert result.details["actual_rows"] == 2

    def test_shape_mismatch_columns(self):
        """Test shape mismatch - different column counts."""
        df1 = pd.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]})
        df2 = pd.DataFrame({"id": [1, 2]})

        comparator = ResultComparator()
        result = comparator.compare(df1, df2)

        assert result.match is False
        assert result.reason == "Shape mismatch"
        assert result.details["expected_cols"] == 2
        assert result.details["actual_cols"] == 1

    def test_column_name_mismatch(self):
        """Test column name mismatch."""
        df1 = pd.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]})
        df2 = pd.DataFrame({"id": [1, 2], "username": ["Alice", "Bob"]})

        comparator = ResultComparator()
        result = comparator.compare(df1, df2)

        assert result.match is False
        assert result.reason == "Column mismatch"
        assert "name" in result.details["missing_columns"]
        assert "username" in result.details["extra_columns"]

    def test_column_order_matters(self):
        """Test column order when it matters."""
        df1 = pd.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]})
        df2 = pd.DataFrame({"name": ["Alice", "Bob"], "id": [1, 2]})

        rules = ComparisonRules(column_order_matters=True)
        comparator = ResultComparator(rules)
        result = comparator.compare(df1, df2)

        assert result.match is False
        assert result.reason == "Column mismatch"

    def test_column_order_ignore(self):
        """Test column order when it doesn't matter."""
        df1 = pd.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]})
        df2 = pd.DataFrame({"name": ["Alice", "Bob"], "id": [1, 2]})

        rules = ComparisonRules(column_order_matters=False)
        comparator = ResultComparator(rules)
        result = comparator.compare(df1, df2)

        assert result.match is True

    def test_row_order_matters(self):
        """Test row order when it matters."""
        df1 = pd.DataFrame({"id": [1, 2, 3]})
        df2 = pd.DataFrame({"id": [3, 2, 1]})

        rules = ComparisonRules(row_order_matters=True)
        comparator = ResultComparator(rules)
        result = comparator.compare(df1, df2)

        assert result.match is False
        assert result.reason == "Value mismatch"

    def test_row_order_ignore(self):
        """Test row order when it doesn't matter."""
        df1 = pd.DataFrame({"id": [1, 2, 3]})
        df2 = pd.DataFrame({"id": [3, 2, 1]})

        rules = ComparisonRules(row_order_matters=False)
        comparator = ResultComparator(rules)
        result = comparator.compare(df1, df2)

        assert result.match is True


class TestNumericComparison:
    """Test numeric value comparison."""

    def test_exact_integer_match(self):
        """Test exact integer match."""
        df1 = pd.DataFrame({"value": [1, 2, 3]})
        df2 = pd.DataFrame({"value": [1, 2, 3]})

        comparator = ResultComparator()
        result = comparator.compare(df1, df2)

        assert result.match is True

    def test_float_relative_error(self):
        """Test float comparison with relative error."""
        df1 = pd.DataFrame({"value": [1.0, 2.0, 3.0]})
        df2 = pd.DataFrame({"value": [1.0000001, 2.0000001, 3.0000001]})

        rules = ComparisonRules(
            float_tolerance=1e-6, float_comparison_mode="relative_error"
        )
        comparator = ResultComparator(rules)
        result = comparator.compare(df1, df2)

        assert result.match is True

    def test_float_absolute_error(self):
        """Test float comparison with absolute error."""
        df1 = pd.DataFrame({"value": [1.0, 2.0, 3.0]})
        df2 = pd.DataFrame({"value": [1.000001, 2.000001, 3.000001]})

        rules = ComparisonRules(
            float_tolerance=0.00001, float_comparison_mode="absolute_error"
        )
        comparator = ResultComparator(rules)
        result = comparator.compare(df1, df2)

        assert result.match is True

    def test_float_mismatch(self):
        """Test float mismatch beyond tolerance."""
        df1 = pd.DataFrame({"value": [1.0, 2.0, 3.0]})
        df2 = pd.DataFrame({"value": [1.1, 2.1, 3.1]})

        rules = ComparisonRules(float_tolerance=1e-6)
        comparator = ResultComparator(rules)
        result = comparator.compare(df1, df2)

        assert result.match is False
        assert result.reason == "Value mismatch"
        assert result.details["mismatched_cells"] > 0

    def test_nan_comparison(self):
        """Test NaN value comparison."""
        df1 = pd.DataFrame({"value": [1.0, np.nan, 3.0]})
        df2 = pd.DataFrame({"value": [1.0, np.nan, 3.0]})

        comparator = ResultComparator()
        result = comparator.compare(df1, df2)

        assert result.match is True

    def test_infinity_comparison(self):
        """Test infinity value comparison."""
        df1 = pd.DataFrame({"value": [1.0, np.inf, -np.inf]})
        df2 = pd.DataFrame({"value": [1.0, np.inf, -np.inf]})

        comparator = ResultComparator()
        result = comparator.compare(df1, df2)

        assert result.match is True

    def test_mixed_numeric_types(self):
        """Test comparison of mixed integer and float."""
        df1 = pd.DataFrame({"value": [1, 2, 3]})  # integers
        df2 = pd.DataFrame({"value": [1.0, 2.0, 3.0]})  # floats

        comparator = ResultComparator()
        result = comparator.compare(df1, df2)

        assert result.match is True


class TestStringComparison:
    """Test string value comparison."""

    def test_exact_string_match(self):
        """Test exact string match."""
        df1 = pd.DataFrame({"name": ["Alice", "Bob", "Charlie"]})
        df2 = pd.DataFrame({"name": ["Alice", "Bob", "Charlie"]})

        comparator = ResultComparator()
        result = comparator.compare(df1, df2)

        assert result.match is True

    def test_string_case_insensitive(self):
        """Test case-insensitive string comparison."""
        df1 = pd.DataFrame({"name": ["Alice", "Bob", "Charlie"]})
        df2 = pd.DataFrame({"name": ["alice", "bob", "charlie"]})

        rules = ComparisonRules(string_case_sensitive=False)
        comparator = ResultComparator(rules)
        result = comparator.compare(df1, df2)

        assert result.match is True

    def test_string_case_sensitive(self):
        """Test case-sensitive string comparison."""
        df1 = pd.DataFrame({"name": ["Alice", "Bob", "Charlie"]})
        df2 = pd.DataFrame({"name": ["alice", "bob", "charlie"]})

        rules = ComparisonRules(string_case_sensitive=True)
        comparator = ResultComparator(rules)
        result = comparator.compare(df1, df2)

        assert result.match is False

    def test_string_trim_whitespace(self):
        """Test string trimming with normalization."""
        df1 = pd.DataFrame({"name": ["Alice", "Bob", "Charlie"]})
        df2 = pd.DataFrame({"name": ["  Alice  ", "  Bob  ", "  Charlie  "]})

        rules = ComparisonRules(string_normalization="trim")
        comparator = ResultComparator(rules)
        result = comparator.compare(df1, df2)

        assert result.match is True

    def test_string_lower_normalization(self):
        """Test string lowercase normalization."""
        df1 = pd.DataFrame({"name": ["Alice", "Bob", "Charlie"]})
        df2 = pd.DataFrame({"name": ["  ALICE  ", "  BOB  ", "  CHARLIE  "]})

        rules = ComparisonRules(string_normalization="lower")
        comparator = ResultComparator(rules)
        result = comparator.compare(df1, df2)

        assert result.match is True


class TestNullComparison:
    """Test NULL value comparison."""

    def test_null_exact_match(self):
        """Test NULL values match."""
        df1 = pd.DataFrame({"value": [1, None, 3]})
        df2 = pd.DataFrame({"value": [1, None, 3]})

        comparator = ResultComparator()
        result = comparator.compare(df1, df2)

        assert result.match is True

    def test_null_mismatch(self):
        """Test NULL vs non-NULL mismatch."""
        df1 = pd.DataFrame({"value": [1, 2, 3]})
        df2 = pd.DataFrame({"value": [1, None, 3]})

        comparator = ResultComparator()
        result = comparator.compare(df1, df2)

        assert result.match is False
        assert result.reason == "Value mismatch"

    def test_nan_vs_none(self):
        """Test NaN vs None comparison."""
        df1 = pd.DataFrame({"value": [1.0, np.nan, 3.0]})
        df2 = pd.DataFrame({"value": [1.0, None, 3.0]})

        comparator = ResultComparator()
        result = comparator.compare(df1, df2)

        assert result.match is True


class TestDatetimeComparison:
    """Test datetime value comparison."""

    def test_datetime_exact_match(self):
        """Test exact datetime match."""
        dt1 = pd.to_datetime(["2024-01-01 10:00:00", "2024-01-02 15:30:00"])
        dt2 = pd.to_datetime(["2024-01-01 10:00:00", "2024-01-02 15:30:00"])

        df1 = pd.DataFrame({"timestamp": dt1})
        df2 = pd.DataFrame({"timestamp": dt2})

        comparator = ResultComparator()
        result = comparator.compare(df1, df2)

        assert result.match is True

    def test_datetime_with_tolerance(self):
        """Test datetime comparison with tolerance."""
        dt1 = pd.to_datetime(["2024-01-01 10:00:00.000"])
        dt2 = pd.to_datetime(["2024-01-01 10:00:00.050"])  # 50ms difference

        df1 = pd.DataFrame({"timestamp": dt1})
        df2 = pd.DataFrame({"timestamp": dt2})

        rules = ComparisonRules(datetime_tolerance_ms=100)  # 100ms tolerance
        comparator = ResultComparator(rules)
        result = comparator.compare(df1, df2)

        assert result.match is True

    def test_datetime_timezone_normalization(self):
        """Test datetime timezone normalization."""
        # Create datetime with different timezones (same instant)
        dt1 = pd.to_datetime(["2024-01-01 10:00:00"]).tz_localize("UTC")
        dt2 = pd.to_datetime(["2024-01-01 18:00:00"]).tz_localize("Asia/Shanghai")

        df1 = pd.DataFrame({"timestamp": dt1})
        df2 = pd.DataFrame({"timestamp": dt2})

        rules = ComparisonRules(datetime_normalize_timezone=True)
        comparator = ResultComparator(rules)
        result = comparator.compare(df1, df2)

        assert result.match is True


class TestBooleanComparison:
    """Test boolean value comparison."""

    def test_boolean_exact_match(self):
        """Test boolean value match."""
        df1 = pd.DataFrame({"active": [True, False, True]})
        df2 = pd.DataFrame({"active": [True, False, True]})

        comparator = ResultComparator()
        result = comparator.compare(df1, df2)

        assert result.match is True

    def test_boolean_mismatch(self):
        """Test boolean value mismatch."""
        df1 = pd.DataFrame({"active": [True, False, True]})
        df2 = pd.DataFrame({"active": [True, True, True]})

        comparator = ResultComparator()
        result = comparator.compare(df1, df2)

        assert result.match is False


class TestComplexScenarios:
    """Test complex comparison scenarios."""

    def test_mixed_data_types(self):
        """Test DataFrame with mixed data types."""
        df1 = pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "score": [95.5, 87.3, 92.1],
            "active": [True, False, True],
            "created_at": pd.to_datetime([
                "2024-01-01", "2024-01-02", "2024-01-03"
            ]),
        })

        df2 = pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "score": [95.5, 87.3, 92.1],
            "active": [True, False, True],
            "created_at": pd.to_datetime([
                "2024-01-01", "2024-01-02", "2024-01-03"
            ]),
        })

        comparator = ResultComparator()
        result = comparator.compare(df1, df2)

        assert result.match is True

    def test_empty_dataframes(self):
        """Test empty DataFrame comparison."""
        df1 = pd.DataFrame(columns=["id", "name"])
        df2 = pd.DataFrame(columns=["id", "name"])

        comparator = ResultComparator()
        result = comparator.compare(df1, df2)

        assert result.match is True

    def test_unordered_with_duplicates(self):
        """Test unordered comparison with duplicate rows."""
        df1 = pd.DataFrame({"value": [1, 2, 2, 3]})
        df2 = pd.DataFrame({"value": [2, 1, 3, 2]})

        rules = ComparisonRules(row_order_matters=False)
        comparator = ResultComparator(rules)
        result = comparator.compare(df1, df2)

        assert result.match is True

    def test_multiple_mismatches(self):
        """Test DataFrame with multiple mismatches."""
        df1 = pd.DataFrame({
            "id": [1, 2, 3],
            "value": [10.0, 20.0, 30.0],
        })
        df2 = pd.DataFrame({
            "id": [1, 2, 3],
            "value": [11.0, 21.0, 31.0],  # All values different
        })

        comparator = ResultComparator()
        result = comparator.compare(df1, df2)

        assert result.match is False
        assert result.details["mismatched_cells"] == 3


class TestConvenienceFunction:
    """Test convenience function."""

    def test_compare_results_function(self):
        """Test compare_results convenience function."""
        df1 = pd.DataFrame({"id": [1, 2, 3]})
        df2 = pd.DataFrame({"id": [1, 2, 3]})

        result = compare_results(df1, df2)

        assert result.match is True

    def test_compare_results_with_rules(self):
        """Test compare_results with custom rules."""
        df1 = pd.DataFrame({"name": ["Alice", "Bob"]})
        df2 = pd.DataFrame({"name": ["alice", "bob"]})

        rules = ComparisonRules(string_case_sensitive=False)
        result = compare_results(df1, df2, rules)

        assert result.match is True
