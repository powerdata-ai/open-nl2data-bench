"""
Result comparison module for OpenNL2Data-Bench.

This module provides functionality to compare results across multiple test runs,
track performance trends, and identify regressions.
"""

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from onb.core.types import PerformanceMetrics


@dataclass
class TestRunResult:
    """Result from a single test run."""

    run_id: str
    timestamp: datetime
    system_name: str
    overall_score: float

    # Accuracy
    accuracy_rate: float
    total_questions: int
    correct_answers: int

    # Performance
    performance_metrics: Optional[PerformanceMetrics] = None

    # Cost
    total_cost: Optional[float] = None
    avg_cost_per_query: Optional[float] = None

    # Robustness
    robustness_pass_rate: Optional[float] = None

    # Metadata
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ComparisonResult:
    """Result of comparing two test runs."""

    baseline_run: TestRunResult
    current_run: TestRunResult

    # Score changes
    score_change: float
    score_change_percent: float

    # Accuracy changes
    accuracy_change: float
    accuracy_change_percent: float

    # Performance changes (positive = slower, negative = faster)
    p50_change: Optional[float] = None
    p95_change: Optional[float] = None
    p99_change: Optional[float] = None

    # Cost changes
    cost_change: Optional[float] = None
    cost_change_percent: Optional[float] = None

    # Improvement indicators
    is_regression: bool = False
    improved_dimensions: List[str] = None
    regressed_dimensions: List[str] = None

    def __post_init__(self):
        """Initialize lists if None."""
        if self.improved_dimensions is None:
            self.improved_dimensions = []
        if self.regressed_dimensions is None:
            self.regressed_dimensions = []


class ResultStore:
    """
    Store and retrieve test run results.

    Stores results as JSON files in a specified directory.
    """

    def __init__(self, storage_dir: str = ".onb_results"):
        """
        Initialize result store.

        Args:
            storage_dir: Directory to store results
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save_result(self, result: TestRunResult) -> None:
        """
        Save a test run result.

        Args:
            result: Test run result to save
        """
        # Convert to dict
        result_dict = asdict(result)

        # Convert datetime to ISO format
        result_dict["timestamp"] = result.timestamp.isoformat()

        # Convert PerformanceMetrics to dict if present
        if result.performance_metrics:
            result_dict["performance_metrics"] = asdict(result.performance_metrics)

        # Save to file
        filename = f"{result.run_id}.json"
        filepath = self.storage_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result_dict, f, indent=2)

    def load_result(self, run_id: str) -> Optional[TestRunResult]:
        """
        Load a test run result by ID.

        Args:
            run_id: Run ID to load

        Returns:
            Test run result or None if not found
        """
        filename = f"{run_id}.json"
        filepath = self.storage_dir / filename

        if not filepath.exists():
            return None

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Convert timestamp back to datetime
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])

        # Convert performance_metrics back to PerformanceMetrics
        if data.get("performance_metrics"):
            data["performance_metrics"] = PerformanceMetrics(
                **data["performance_metrics"]
            )

        return TestRunResult(**data)

    def list_runs(
        self, system_name: Optional[str] = None, limit: Optional[int] = None
    ) -> List[TestRunResult]:
        """
        List all stored test runs.

        Args:
            system_name: Optional filter by system name
            limit: Optional limit on number of results

        Returns:
            List of test run results, sorted by timestamp (newest first)
        """
        results = []

        for filepath in self.storage_dir.glob("*.json"):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Convert timestamp
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])

            # Convert performance_metrics if present
            if data.get("performance_metrics"):
                data["performance_metrics"] = PerformanceMetrics(
                    **data["performance_metrics"]
                )

            result = TestRunResult(**data)

            # Filter by system name if specified
            if system_name and result.system_name != system_name:
                continue

            results.append(result)

        # Sort by timestamp (newest first)
        results.sort(key=lambda r: r.timestamp, reverse=True)

        # Apply limit if specified
        if limit:
            results = results[:limit]

        return results

    def delete_result(self, run_id: str) -> bool:
        """
        Delete a test run result.

        Args:
            run_id: Run ID to delete

        Returns:
            True if deleted, False if not found
        """
        filename = f"{run_id}.json"
        filepath = self.storage_dir / filename

        if filepath.exists():
            filepath.unlink()
            return True

        return False


class ResultComparator:
    """
    Compare test run results to identify improvements and regressions.
    """

    # Thresholds for determining improvement/regression
    REGRESSION_THRESHOLD = -5.0  # % decrease is regression
    IMPROVEMENT_THRESHOLD = 5.0  # % increase is improvement

    def __init__(self):
        """Initialize comparator."""
        pass

    def compare(
        self, baseline: TestRunResult, current: TestRunResult
    ) -> ComparisonResult:
        """
        Compare two test runs.

        Args:
            baseline: Baseline (reference) run
            current: Current run to compare against baseline

        Returns:
            Comparison result
        """
        # Calculate score changes
        score_change = current.overall_score - baseline.overall_score
        score_change_percent = (
            (score_change / baseline.overall_score * 100)
            if baseline.overall_score > 0
            else 0
        )

        # Calculate accuracy changes
        accuracy_change = current.accuracy_rate - baseline.accuracy_rate
        accuracy_change_percent = (
            (accuracy_change / baseline.accuracy_rate * 100)
            if baseline.accuracy_rate > 0
            else 0
        )

        # Calculate performance changes
        p50_change = None
        p95_change = None
        p99_change = None

        if (
            baseline.performance_metrics
            and current.performance_metrics
        ):
            p50_change = (
                current.performance_metrics.p50 - baseline.performance_metrics.p50
            )
            p95_change = (
                current.performance_metrics.p95 - baseline.performance_metrics.p95
            )
            p99_change = (
                current.performance_metrics.p99 - baseline.performance_metrics.p99
            )

        # Calculate cost changes
        cost_change = None
        cost_change_percent = None

        if baseline.total_cost is not None and current.total_cost is not None:
            cost_change = current.total_cost - baseline.total_cost
            cost_change_percent = (
                (cost_change / baseline.total_cost * 100)
                if baseline.total_cost > 0
                else 0
            )

        # Determine improved/regressed dimensions
        improved = []
        regressed = []

        # Check each dimension
        if accuracy_change_percent >= self.IMPROVEMENT_THRESHOLD:
            improved.append("Accuracy")
        elif accuracy_change_percent <= self.REGRESSION_THRESHOLD:
            regressed.append("Accuracy")

        if p95_change is not None:
            # For performance, decrease is improvement
            perf_change_percent = (
                (p95_change / baseline.performance_metrics.p95 * 100)
                if baseline.performance_metrics.p95 > 0
                else 0
            )
            if perf_change_percent <= -self.IMPROVEMENT_THRESHOLD:
                improved.append("Performance")
            elif perf_change_percent >= self.IMPROVEMENT_THRESHOLD:
                regressed.append("Performance")

        if cost_change_percent is not None:
            # For cost, decrease is improvement
            if cost_change_percent <= -self.IMPROVEMENT_THRESHOLD:
                improved.append("Cost")
            elif cost_change_percent >= self.IMPROVEMENT_THRESHOLD:
                regressed.append("Cost")

        # Overall regression if score decreased significantly
        is_regression = score_change_percent <= self.REGRESSION_THRESHOLD

        return ComparisonResult(
            baseline_run=baseline,
            current_run=current,
            score_change=score_change,
            score_change_percent=score_change_percent,
            accuracy_change=accuracy_change,
            accuracy_change_percent=accuracy_change_percent,
            p50_change=p50_change,
            p95_change=p95_change,
            p99_change=p99_change,
            cost_change=cost_change,
            cost_change_percent=cost_change_percent,
            is_regression=is_regression,
            improved_dimensions=improved,
            regressed_dimensions=regressed,
        )

    def compare_multiple(
        self, runs: List[TestRunResult]
    ) -> List[ComparisonResult]:
        """
        Compare multiple runs sequentially.

        Args:
            runs: List of test runs (should be sorted by timestamp)

        Returns:
            List of comparison results (comparing each run to previous)
        """
        if len(runs) < 2:
            return []

        comparisons = []

        for i in range(1, len(runs)):
            baseline = runs[i - 1]
            current = runs[i]
            comparison = self.compare(baseline, current)
            comparisons.append(comparison)

        return comparisons

    def get_trend_summary(
        self, runs: List[TestRunResult]
    ) -> Dict[str, Any]:
        """
        Get trend summary across multiple runs.

        Args:
            runs: List of test runs (sorted by timestamp, oldest first)

        Returns:
            Dictionary with trend statistics
        """
        if not runs:
            return {}

        # Calculate trends
        scores = [r.overall_score for r in runs]
        accuracies = [r.accuracy_rate * 100 for r in runs]

        return {
            "total_runs": len(runs),
            "score_trend": {
                "first": scores[0],
                "last": scores[-1],
                "change": scores[-1] - scores[0],
                "change_percent": (
                    ((scores[-1] - scores[0]) / scores[0] * 100)
                    if scores[0] > 0
                    else 0
                ),
                "min": min(scores),
                "max": max(scores),
                "average": sum(scores) / len(scores),
            },
            "accuracy_trend": {
                "first": accuracies[0],
                "last": accuracies[-1],
                "change": accuracies[-1] - accuracies[0],
                "change_percent": (
                    ((accuracies[-1] - accuracies[0]) / accuracies[0] * 100)
                    if accuracies[0] > 0
                    else 0
                ),
                "min": min(accuracies),
                "max": max(accuracies),
                "average": sum(accuracies) / len(accuracies),
            },
        }
