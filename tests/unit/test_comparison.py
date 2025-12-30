"""Unit tests for result comparison module."""
import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from onb.core.types import PerformanceMetrics
from onb.reporting.comparison import (
    ComparisonResult,
    ResultComparator,
    ResultStore,
    TestRunResult,
)


class TestTestRunResult:
    """Test TestRunResult dataclass."""

    def test_initialization_minimal(self):
        """Test minimal initialization."""
        result = TestRunResult(
            run_id="run_001",
            timestamp=datetime(2025, 1, 15, 10, 0),
            system_name="Test System",
            overall_score=85.0,
            accuracy_rate=0.85,
            total_questions=20,
            correct_answers=17,
        )

        assert result.run_id == "run_001"
        assert result.system_name == "Test System"
        assert result.overall_score == 85.0
        assert result.accuracy_rate == 0.85
        assert result.performance_metrics is None
        assert result.total_cost is None

    def test_initialization_full(self):
        """Test full initialization."""
        perf_metrics = PerformanceMetrics(
            median_time_ms=1000,
            mean_time_ms=1100,
            p50=1000,
            p95=2000,
            p99=2500,
            min_time_ms=500,
            max_time_ms=3000,
            std_dev=400,
            measurements=[],
        )

        result = TestRunResult(
            run_id="run_002",
            timestamp=datetime(2025, 1, 15, 12, 0),
            system_name="Full System",
            overall_score=90.0,
            accuracy_rate=0.90,
            total_questions=30,
            correct_answers=27,
            performance_metrics=perf_metrics,
            total_cost=1.5,
            avg_cost_per_query=0.05,
            robustness_pass_rate=0.88,
            metadata={"domain": "ecommerce"},
        )

        assert result.performance_metrics == perf_metrics
        assert result.total_cost == 1.5
        assert result.metadata["domain"] == "ecommerce"


class TestComparisonResult:
    """Test ComparisonResult dataclass."""

    def test_initialization(self):
        """Test initialization."""
        baseline = TestRunResult(
            run_id="baseline",
            timestamp=datetime.now(),
            system_name="System",
            overall_score=80.0,
            accuracy_rate=0.80,
            total_questions=10,
            correct_answers=8,
        )

        current = TestRunResult(
            run_id="current",
            timestamp=datetime.now(),
            system_name="System",
            overall_score=85.0,
            accuracy_rate=0.85,
            total_questions=10,
            correct_answers=9,
        )

        comp = ComparisonResult(
            baseline_run=baseline,
            current_run=current,
            score_change=5.0,
            score_change_percent=6.25,
            accuracy_change=0.05,
            accuracy_change_percent=6.25,
            is_regression=False,
        )

        assert comp.baseline_run == baseline
        assert comp.current_run == current
        assert comp.score_change == 5.0
        assert comp.is_regression is False
        assert comp.improved_dimensions == []
        assert comp.regressed_dimensions == []


class TestResultStore:
    """Test ResultStore class."""

    def test_initialization(self):
        """Test store initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ResultStore(storage_dir=tmpdir)
            assert store.storage_dir.exists()
            assert store.storage_dir.is_dir()

    def test_save_and_load_result(self):
        """Test saving and loading result."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ResultStore(storage_dir=tmpdir)

            result = TestRunResult(
                run_id="test_save_load",
                timestamp=datetime(2025, 1, 15, 10, 30),
                system_name="Test System",
                overall_score=82.5,
                accuracy_rate=0.825,
                total_questions=20,
                correct_answers=17,
            )

            # Save
            store.save_result(result)

            # Load
            loaded = store.load_result("test_save_load")

            assert loaded is not None
            assert loaded.run_id == result.run_id
            assert loaded.timestamp == result.timestamp
            assert loaded.system_name == result.system_name
            assert loaded.overall_score == result.overall_score
            assert loaded.accuracy_rate == result.accuracy_rate

    def test_save_result_with_performance_metrics(self):
        """Test saving result with performance metrics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ResultStore(storage_dir=tmpdir)

            perf_metrics = PerformanceMetrics(
                median_time_ms=1200,
                mean_time_ms=1300,
                p50=1200,
                p95=2400,
                p99=2800,
                min_time_ms=900,
                max_time_ms=3200,
                std_dev=380,
                measurements=[1000, 1200, 1500],
            )

            result = TestRunResult(
                run_id="test_perf",
                timestamp=datetime.now(),
                system_name="System",
                overall_score=85.0,
                accuracy_rate=0.85,
                total_questions=10,
                correct_answers=9,
                performance_metrics=perf_metrics,
            )

            store.save_result(result)
            loaded = store.load_result("test_perf")

            assert loaded.performance_metrics is not None
            assert loaded.performance_metrics.p50 == perf_metrics.p50
            assert loaded.performance_metrics.p95 == perf_metrics.p95

    def test_load_nonexistent_result(self):
        """Test loading non-existent result."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ResultStore(storage_dir=tmpdir)
            loaded = store.load_result("does_not_exist")
            assert loaded is None

    def test_list_runs_empty(self):
        """Test listing runs when empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ResultStore(storage_dir=tmpdir)
            runs = store.list_runs()
            assert runs == []

    def test_list_runs_multiple(self):
        """Test listing multiple runs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ResultStore(storage_dir=tmpdir)

            # Save multiple results
            for i in range(5):
                result = TestRunResult(
                    run_id=f"run_{i}",
                    timestamp=datetime(2025, 1, i + 1, 10, 0),
                    system_name="System",
                    overall_score=80.0 + i,
                    accuracy_rate=0.80,
                    total_questions=10,
                    correct_answers=8,
                )
                store.save_result(result)

            runs = store.list_runs()

            assert len(runs) == 5
            # Should be sorted by timestamp (newest first)
            assert runs[0].run_id == "run_4"
            assert runs[-1].run_id == "run_0"

    def test_list_runs_with_filter(self):
        """Test listing runs filtered by system name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ResultStore(storage_dir=tmpdir)

            # Save results for different systems
            for i in range(3):
                result = TestRunResult(
                    run_id=f"sys_a_{i}",
                    timestamp=datetime(2025, 1, i + 1, 10, 0),
                    system_name="System A",
                    overall_score=80.0,
                    accuracy_rate=0.80,
                    total_questions=10,
                    correct_answers=8,
                )
                store.save_result(result)

            for i in range(2):
                result = TestRunResult(
                    run_id=f"sys_b_{i}",
                    timestamp=datetime(2025, 1, i + 10, 10, 0),
                    system_name="System B",
                    overall_score=85.0,
                    accuracy_rate=0.85,
                    total_questions=10,
                    correct_answers=9,
                )
                store.save_result(result)

            runs_a = store.list_runs(system_name="System A")
            runs_b = store.list_runs(system_name="System B")

            assert len(runs_a) == 3
            assert len(runs_b) == 2
            assert all(r.system_name == "System A" for r in runs_a)
            assert all(r.system_name == "System B" for r in runs_b)

    def test_list_runs_with_limit(self):
        """Test listing runs with limit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ResultStore(storage_dir=tmpdir)

            # Save 10 results
            for i in range(10):
                result = TestRunResult(
                    run_id=f"run_{i}",
                    timestamp=datetime(2025, 1, i + 1, 10, 0),
                    system_name="System",
                    overall_score=80.0,
                    accuracy_rate=0.80,
                    total_questions=10,
                    correct_answers=8,
                )
                store.save_result(result)

            runs = store.list_runs(limit=3)

            assert len(runs) == 3

    def test_delete_result(self):
        """Test deleting result."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ResultStore(storage_dir=tmpdir)

            result = TestRunResult(
                run_id="to_delete",
                timestamp=datetime.now(),
                system_name="System",
                overall_score=80.0,
                accuracy_rate=0.80,
                total_questions=10,
                correct_answers=8,
            )

            store.save_result(result)
            assert store.load_result("to_delete") is not None

            deleted = store.delete_result("to_delete")
            assert deleted is True
            assert store.load_result("to_delete") is None

    def test_delete_nonexistent_result(self):
        """Test deleting non-existent result."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ResultStore(storage_dir=tmpdir)
            deleted = store.delete_result("does_not_exist")
            assert deleted is False


class TestResultComparator:
    """Test ResultComparator class."""

    def test_initialization(self):
        """Test comparator initialization."""
        comparator = ResultComparator()
        assert comparator is not None

    def test_compare_basic(self):
        """Test basic comparison."""
        comparator = ResultComparator()

        baseline = TestRunResult(
            run_id="baseline",
            timestamp=datetime(2025, 1, 1, 10, 0),
            system_name="System",
            overall_score=80.0,
            accuracy_rate=0.80,
            total_questions=10,
            correct_answers=8,
        )

        current = TestRunResult(
            run_id="current",
            timestamp=datetime(2025, 1, 2, 10, 0),
            system_name="System",
            overall_score=85.0,
            accuracy_rate=0.85,
            total_questions=10,
            correct_answers=9,
        )

        result = comparator.compare(baseline, current)

        assert result.score_change == 5.0
        assert result.score_change_percent == pytest.approx(6.25)
        assert result.accuracy_change == pytest.approx(0.05)
        assert result.accuracy_change_percent == pytest.approx(6.25)
        assert result.is_regression is False
        assert "Accuracy" in result.improved_dimensions

    def test_compare_regression(self):
        """Test detecting regression."""
        comparator = ResultComparator()

        baseline = TestRunResult(
            run_id="baseline",
            timestamp=datetime.now(),
            system_name="System",
            overall_score=90.0,
            accuracy_rate=0.90,
            total_questions=10,
            correct_answers=9,
        )

        current = TestRunResult(
            run_id="current",
            timestamp=datetime.now(),
            system_name="System",
            overall_score=80.0,
            accuracy_rate=0.80,
            total_questions=10,
            correct_answers=8,
        )

        result = comparator.compare(baseline, current)

        assert result.score_change < 0
        assert result.is_regression is True
        assert "Accuracy" in result.regressed_dimensions

    def test_compare_with_performance(self):
        """Test comparison with performance metrics."""
        comparator = ResultComparator()

        perf_baseline = PerformanceMetrics(
            median_time_ms=1000,
            mean_time_ms=1100,
            p50=1000,
            p95=2000,
            p99=2500,
            min_time_ms=500,
            max_time_ms=3000,
            std_dev=400,
            measurements=[],
        )

        perf_current = PerformanceMetrics(
            median_time_ms=800,
            mean_time_ms=900,
            p50=800,
            p95=1600,
            p99=2000,
            min_time_ms=400,
            max_time_ms=2500,
            std_dev=350,
            measurements=[],
        )

        baseline = TestRunResult(
            run_id="baseline",
            timestamp=datetime.now(),
            system_name="System",
            overall_score=80.0,
            accuracy_rate=0.80,
            total_questions=10,
            correct_answers=8,
            performance_metrics=perf_baseline,
        )

        current = TestRunResult(
            run_id="current",
            timestamp=datetime.now(),
            system_name="System",
            overall_score=82.0,
            accuracy_rate=0.80,
            total_questions=10,
            correct_answers=8,
            performance_metrics=perf_current,
        )

        result = comparator.compare(baseline, current)

        assert result.p50_change == -200  # Improvement (faster)
        assert result.p95_change == -400
        assert result.p99_change == -500
        assert "Performance" in result.improved_dimensions

    def test_compare_with_cost(self):
        """Test comparison with cost metrics."""
        comparator = ResultComparator()

        baseline = TestRunResult(
            run_id="baseline",
            timestamp=datetime.now(),
            system_name="System",
            overall_score=80.0,
            accuracy_rate=0.80,
            total_questions=10,
            correct_answers=8,
            total_cost=1.0,
        )

        current = TestRunResult(
            run_id="current",
            timestamp=datetime.now(),
            system_name="System",
            overall_score=80.0,
            accuracy_rate=0.80,
            total_questions=10,
            correct_answers=8,
            total_cost=0.8,
        )

        result = comparator.compare(baseline, current)

        assert result.cost_change == pytest.approx(-0.2)
        assert result.cost_change_percent == pytest.approx(-20.0)
        assert "Cost" in result.improved_dimensions

    def test_compare_multiple(self):
        """Test comparing multiple runs."""
        comparator = ResultComparator()

        runs = [
            TestRunResult(
                run_id=f"run_{i}",
                timestamp=datetime(2025, 1, i + 1, 10, 0),
                system_name="System",
                overall_score=80.0 + i * 2,
                accuracy_rate=0.80 + i * 0.02,
                total_questions=10,
                correct_answers=8 + i,
            )
            for i in range(5)
        ]

        comparisons = comparator.compare_multiple(runs)

        assert len(comparisons) == 4
        # Each comparison should show improvement
        assert all(c.score_change > 0 for c in comparisons)

    def test_get_trend_summary(self):
        """Test getting trend summary."""
        comparator = ResultComparator()

        runs = [
            TestRunResult(
                run_id=f"run_{i}",
                timestamp=datetime(2025, 1, i + 1, 10, 0),
                system_name="System",
                overall_score=75.0 + i * 2.5,
                accuracy_rate=0.75 + i * 0.025,
                total_questions=10,
                correct_answers=8,
            )
            for i in range(5)
        ]

        summary = comparator.get_trend_summary(runs)

        assert summary["total_runs"] == 5
        assert summary["score_trend"]["first"] == 75.0
        assert summary["score_trend"]["last"] == 85.0
        assert summary["score_trend"]["change"] == 10.0
        assert summary["accuracy_trend"]["first"] == 75.0
        assert summary["accuracy_trend"]["last"] == 85.0

    def test_get_trend_summary_empty(self):
        """Test trend summary with empty list."""
        comparator = ResultComparator()
        summary = comparator.get_trend_summary([])
        assert summary == {}
