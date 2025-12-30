"""
Result set comparator for OpenNL2SQL-Bench.

This module provides comprehensive DataFrame comparison capabilities
with configurable rules for different data types.
"""

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from onb.core.types import ComparisonResult, ComparisonRules


class ResultComparator:
    """Compares expected and actual result DataFrames."""

    def __init__(self, rules: Optional[ComparisonRules] = None):
        """
        Initialize comparator with comparison rules.

        Args:
            rules: Comparison rules (defaults to standard rules)
        """
        self.rules = rules or ComparisonRules()

    def compare(
        self, expected: pd.DataFrame, actual: pd.DataFrame
    ) -> ComparisonResult:
        """
        Compare two DataFrames according to comparison rules.

        Args:
            expected: Expected result DataFrame (from golden SQL)
            actual: Actual result DataFrame (from SUT)

        Returns:
            ComparisonResult with match status and details
        """
        details: Dict[str, Any] = {}

        # Step 1: Shape comparison
        if expected.shape != actual.shape:
            return ComparisonResult(
                match=False,
                reason="Shape mismatch",
                details={
                    "expected_shape": expected.shape,
                    "actual_shape": actual.shape,
                    "expected_rows": len(expected),
                    "actual_rows": len(actual),
                    "expected_cols": len(expected.columns),
                    "actual_cols": len(actual.columns),
                },
            )

        # Step 2: Column comparison
        col_result = self._compare_columns(expected, actual)
        if not col_result[0]:
            return ComparisonResult(
                match=False, reason="Column mismatch", details=col_result[1]
            )
        details.update(col_result[1])

        # Step 3: Sort DataFrames if order doesn't matter
        expected_sorted, actual_sorted = self._prepare_dataframes(expected, actual)

        # Step 4: Value comparison
        value_result = self._compare_values(expected_sorted, actual_sorted)
        if not value_result[0]:
            return ComparisonResult(
                match=False, reason="Value mismatch", details=value_result[1]
            )
        details.update(value_result[1])

        # All checks passed
        return ComparisonResult(
            match=True,
            reason="Results match",
            details={
                "rows_compared": len(expected),
                "columns_compared": len(expected.columns),
                **details,
            },
        )

    def _compare_columns(
        self, expected: pd.DataFrame, actual: pd.DataFrame
    ) -> Tuple[bool, Dict[str, Any]]:
        """Compare column names and order."""
        expected_cols = list(expected.columns)
        actual_cols = list(actual.columns)

        details = {
            "expected_columns": expected_cols,
            "actual_columns": actual_cols,
        }

        # Check column names (ignoring order for now)
        expected_set = set(expected_cols)
        actual_set = set(actual_cols)

        if expected_set != actual_set:
            missing = expected_set - actual_set
            extra = actual_set - expected_set
            details["missing_columns"] = list(missing)
            details["extra_columns"] = list(extra)
            return False, details

        # Check column order if it matters
        if self.rules.column_order_matters and expected_cols != actual_cols:
            details["column_order_mismatch"] = True
            return False, details

        return True, details

    def _prepare_dataframes(
        self, expected: pd.DataFrame, actual: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Prepare DataFrames for comparison (sorting, alignment)."""
        # Make copies to avoid modifying originals
        expected_df = expected.copy()
        actual_df = actual.copy()

        # Align columns if order doesn't matter
        if not self.rules.column_order_matters:
            # Sort columns alphabetically for consistent comparison
            sorted_cols = sorted(expected_df.columns)
            expected_df = expected_df[sorted_cols]
            actual_df = actual_df[sorted_cols]

        # Sort rows if order doesn't matter
        if not self.rules.row_order_matters:
            # Sort by all columns for deterministic ordering
            try:
                expected_df = expected_df.sort_values(
                    by=list(expected_df.columns)
                ).reset_index(drop=True)
                actual_df = actual_df.sort_values(
                    by=list(actual_df.columns)
                ).reset_index(drop=True)
            except Exception:
                # If sorting fails (e.g., mixed types), try converting to string
                for col in expected_df.columns:
                    expected_df[col] = expected_df[col].astype(str)
                    actual_df[col] = actual_df[col].astype(str)
                expected_df = expected_df.sort_values(
                    by=list(expected_df.columns)
                ).reset_index(drop=True)
                actual_df = actual_df.sort_values(
                    by=list(actual_df.columns)
                ).reset_index(drop=True)

        return expected_df, actual_df

    def _compare_values(
        self, expected: pd.DataFrame, actual: pd.DataFrame
    ) -> Tuple[bool, Dict[str, Any]]:
        """Compare values cell by cell."""
        mismatches = []
        details: Dict[str, Any] = {"total_cells": expected.size, "mismatched_cells": 0}

        for col in expected.columns:
            col_mismatches = self._compare_column_values(
                expected[col], actual[col], col
            )
            if col_mismatches:
                mismatches.extend(col_mismatches)

        if mismatches:
            details["mismatched_cells"] = len(mismatches)
            details["mismatches"] = mismatches[:100]  # Limit to first 100 for readability
            details["total_mismatches"] = len(mismatches)
            return False, details

        return True, details

    def _compare_column_values(
        self, expected_col: pd.Series, actual_col: pd.Series, col_name: str
    ) -> List[Dict[str, Any]]:
        """Compare values in a single column."""
        mismatches = []

        for idx in range(len(expected_col)):
            expected_val = expected_col.iloc[idx]
            actual_val = actual_col.iloc[idx]

            if not self._compare_single_value(expected_val, actual_val):
                mismatches.append(
                    {
                        "row": idx,
                        "column": col_name,
                        "expected": self._format_value(expected_val),
                        "actual": self._format_value(actual_val),
                    }
                )

        return mismatches

    def _compare_single_value(self, expected: Any, actual: Any) -> bool:
        """Compare two individual values according to rules."""
        # Handle NULL/None values
        if pd.isna(expected) and pd.isna(actual):
            return True
        if pd.isna(expected) or pd.isna(actual):
            # NULL handling based on rules
            if self.rules.null_handling == "lenient":
                # Treat NULL and empty string as equivalent if configured
                return False  # For now, strict NULL comparison
            return False

        # Numeric comparison
        if isinstance(expected, (int, float, np.number)) and isinstance(
            actual, (int, float, np.number)
        ):
            return self._compare_numeric(float(expected), float(actual))

        # String comparison
        if isinstance(expected, str) and isinstance(actual, str):
            return self._compare_string(expected, actual)

        # Datetime comparison
        if pd.api.types.is_datetime64_any_dtype(type(expected)) or isinstance(
            expected, pd.Timestamp
        ):
            return self._compare_datetime(expected, actual)

        # Boolean comparison
        if isinstance(expected, (bool, np.bool_)):
            return bool(expected) == bool(actual)

        # Default: exact match
        return expected == actual

    def _compare_numeric(self, expected: float, actual: float) -> bool:
        """Compare numeric values with tolerance."""
        # Handle infinity
        if np.isinf(expected) and np.isinf(actual):
            return np.sign(expected) == np.sign(actual)
        if np.isinf(expected) or np.isinf(actual):
            return False

        # Handle NaN
        if np.isnan(expected) and np.isnan(actual):
            return True
        if np.isnan(expected) or np.isnan(actual):
            return False

        # Exact match check first
        if expected == actual:
            return True

        # Tolerance-based comparison
        if self.rules.float_comparison_mode == "absolute_error":
            return abs(expected - actual) <= self.rules.float_tolerance
        else:  # relative_error
            # Avoid division by zero
            if expected == 0:
                return abs(actual) <= self.rules.float_tolerance
            relative_error = abs((expected - actual) / expected)
            return relative_error <= self.rules.float_tolerance

    def _compare_string(self, expected: str, actual: str) -> bool:
        """Compare string values according to rules."""
        # Apply normalization
        expected_norm = expected
        actual_norm = actual

        if self.rules.string_normalization == "trim":
            expected_norm = expected_norm.strip()
            actual_norm = actual_norm.strip()
        elif self.rules.string_normalization == "lower":
            expected_norm = expected_norm.lower().strip()
            actual_norm = actual_norm.lower().strip()

        # Case sensitivity
        if not self.rules.string_case_sensitive:
            expected_norm = expected_norm.lower()
            actual_norm = actual_norm.lower()

        return expected_norm == actual_norm

    def _compare_datetime(self, expected: Any, actual: Any) -> bool:
        """Compare datetime values with tolerance."""
        try:
            # Convert to pandas Timestamp for consistent comparison
            expected_ts = pd.Timestamp(expected)
            actual_ts = pd.Timestamp(actual)

            # Normalize timezone if configured
            if self.rules.datetime_normalize_timezone:
                if expected_ts.tz is not None:
                    expected_ts = expected_ts.tz_convert("UTC")
                if actual_ts.tz is not None:
                    actual_ts = actual_ts.tz_convert("UTC")

            # Compare with tolerance
            diff_ms = abs((expected_ts - actual_ts).total_seconds() * 1000)
            return diff_ms <= self.rules.datetime_tolerance_ms

        except Exception:
            # If conversion fails, fall back to string comparison
            return str(expected) == str(actual)

    def _format_value(self, value: Any) -> str:
        """Format value for display in error messages."""
        if pd.isna(value):
            return "NULL"
        if isinstance(value, float):
            return f"{value:.6f}"
        if isinstance(value, pd.Timestamp):
            return value.isoformat()
        return str(value)


# Convenience function
def compare_results(
    expected: pd.DataFrame,
    actual: pd.DataFrame,
    rules: Optional[ComparisonRules] = None,
) -> ComparisonResult:
    """
    Compare two result DataFrames.

    Args:
        expected: Expected result DataFrame
        actual: Actual result DataFrame
        rules: Optional comparison rules

    Returns:
        ComparisonResult with match status and details
    """
    comparator = ResultComparator(rules)
    return comparator.compare(expected, actual)
