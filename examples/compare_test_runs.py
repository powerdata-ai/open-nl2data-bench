"""Example demonstrating result comparison across multiple test runs."""
from datetime import datetime, timedelta

from onb.core.types import PerformanceMetrics
from onb.reporting import ResultComparator, ResultStore, TestRunResult


def create_sample_runs():
    """Create sample test run results simulating performance improvements."""
    runs = []

    # Run 1: Initial baseline
    perf1 = PerformanceMetrics(
        median_time_ms=2000,
        mean_time_ms=2100,
        p50=2000,
        p95=3500,
        p99=4200,
        min_time_ms=1500,
        max_time_ms=5000,
        std_dev=600,
        measurements=[],
    )
    runs.append(
        TestRunResult(
            run_id="run_001",
            timestamp=datetime(2025, 1, 1, 10, 0, 0),
            system_name="NL2SQL System v1.0",
            overall_score=75.0,
            accuracy_rate=0.75,
            total_questions=100,
            correct_answers=75,
            performance_metrics=perf1,
            total_cost=2.5,
            avg_cost_per_query=0.025,
            robustness_pass_rate=0.70,
            metadata={
                "model": "gpt-4-turbo",
                "database": "PostgreSQL",
                "version": "1.0.0",
            },
        )
    )

    # Run 2: After prompt optimization
    perf2 = PerformanceMetrics(
        median_time_ms=1800,
        mean_time_ms=1900,
        p50=1800,
        p95=3200,
        p99=3800,
        min_time_ms=1300,
        max_time_ms=4500,
        std_dev=550,
        measurements=[],
    )
    runs.append(
        TestRunResult(
            run_id="run_002",
            timestamp=datetime(2025, 1, 8, 10, 0, 0),
            system_name="NL2SQL System v1.1",
            overall_score=82.0,
            accuracy_rate=0.82,
            total_questions=100,
            correct_answers=82,
            performance_metrics=perf2,
            total_cost=2.3,
            avg_cost_per_query=0.023,
            robustness_pass_rate=0.78,
            metadata={
                "model": "gpt-4-turbo",
                "database": "PostgreSQL",
                "version": "1.1.0",
                "changes": "Optimized prompts",
            },
        )
    )

    # Run 3: After adding context examples
    perf3 = PerformanceMetrics(
        median_time_ms=1600,
        mean_time_ms=1700,
        p50=1600,
        p95=2800,
        p99=3400,
        min_time_ms=1100,
        max_time_ms=4000,
        std_dev=500,
        measurements=[],
    )
    runs.append(
        TestRunResult(
            run_id="run_003",
            timestamp=datetime(2025, 1, 15, 10, 0, 0),
            system_name="NL2SQL System v1.2",
            overall_score=88.0,
            accuracy_rate=0.88,
            total_questions=100,
            correct_answers=88,
            performance_metrics=perf3,
            total_cost=2.0,
            avg_cost_per_query=0.020,
            robustness_pass_rate=0.85,
            metadata={
                "model": "gpt-4-turbo",
                "database": "PostgreSQL",
                "version": "1.2.0",
                "changes": "Added few-shot examples",
            },
        )
    )

    # Run 4: Latest version
    perf4 = PerformanceMetrics(
        median_time_ms=1500,
        mean_time_ms=1600,
        p50=1500,
        p95=2600,
        p99=3200,
        min_time_ms=1000,
        max_time_ms=3800,
        std_dev=480,
        measurements=[],
    )
    runs.append(
        TestRunResult(
            run_id="run_004",
            timestamp=datetime(2025, 1, 22, 10, 0, 0),
            system_name="NL2SQL System v1.3",
            overall_score=92.0,
            accuracy_rate=0.92,
            total_questions=100,
            correct_answers=92,
            performance_metrics=perf4,
            total_cost=1.8,
            avg_cost_per_query=0.018,
            robustness_pass_rate=0.90,
            metadata={
                "model": "gpt-4-turbo",
                "database": "PostgreSQL",
                "version": "1.3.0",
                "changes": "Schema normalization + caching",
            },
        )
    )

    return runs


def main():
    """Demonstrate result comparison workflow."""
    print("=" * 80)
    print("Result Comparison Example")
    print("=" * 80)
    print()

    # Initialize store
    store = ResultStore(storage_dir=".example_results")
    comparator = ResultComparator()

    # Create and save sample runs
    print("📝 Creating sample test runs...")
    runs = create_sample_runs()
    for run in runs:
        store.save_result(run)
        print(f"  ✓ Saved {run.run_id}: {run.system_name} (Score: {run.overall_score:.1f})")
    print()

    # List all runs
    print("📋 Listing all test runs:")
    all_runs = store.list_runs()
    print(f"  Found {len(all_runs)} runs")
    for run in all_runs:
        print(
            f"  - {run.run_id}: {run.system_name} "
            f"({run.timestamp.strftime('%Y-%m-%d')}) - Score: {run.overall_score:.1f}"
        )
    print()

    # Compare consecutive runs
    print("🔍 Comparing consecutive runs:")
    comparisons = comparator.compare_multiple(runs)
    for i, comp in enumerate(comparisons):
        baseline = comp.baseline_run
        current = comp.current_run
        print(f"\n  Run {i+1} → Run {i+2}:")
        print(f"    Baseline: {baseline.run_id} (Score: {baseline.overall_score:.1f})")
        print(f"    Current:  {current.run_id} (Score: {current.overall_score:.1f})")
        print(f"    Score Change: {comp.score_change:+.1f} ({comp.score_change_percent:+.2f}%)")
        print(f"    Accuracy Change: {comp.accuracy_change:+.2f} ({comp.accuracy_change_percent:+.2f}%)")
        if comp.p95_change is not None:
            print(f"    P95 Latency Change: {comp.p95_change:+.0f} ms")
        if comp.cost_change is not None:
            print(f"    Cost Change: ${comp.cost_change:+.2f} ({comp.cost_change_percent:+.2f}%)")
        print(f"    Regression: {'❌ Yes' if comp.is_regression else '✅ No'}")
        if comp.improved_dimensions:
            print(f"    Improvements: {', '.join(comp.improved_dimensions)}")
        if comp.regressed_dimensions:
            print(f"    Regressions: {', '.join(comp.regressed_dimensions)}")
    print()

    # Compare first and last runs
    print("📊 Overall Progress (First vs Last):")
    first_run = runs[0]
    last_run = runs[-1]
    overall_comp = comparator.compare(first_run, last_run)
    print(f"  Baseline: {first_run.run_id} ({first_run.timestamp.strftime('%Y-%m-%d')})")
    print(f"    Score: {first_run.overall_score:.1f}")
    print(f"    Accuracy: {first_run.accuracy_rate * 100:.1f}%")
    print(f"    P95 Latency: {first_run.performance_metrics.p95:.0f} ms")
    print(f"    Total Cost: ${first_run.total_cost:.2f}")
    print()
    print(f"  Current: {last_run.run_id} ({last_run.timestamp.strftime('%Y-%m-%d')})")
    print(f"    Score: {last_run.overall_score:.1f}")
    print(f"    Accuracy: {last_run.accuracy_rate * 100:.1f}%")
    print(f"    P95 Latency: {last_run.performance_metrics.p95:.0f} ms")
    print(f"    Total Cost: ${last_run.total_cost:.2f}")
    print()
    print(f"  Changes:")
    print(f"    Score: {overall_comp.score_change:+.1f} ({overall_comp.score_change_percent:+.2f}%)")
    print(
        f"    Accuracy: {overall_comp.accuracy_change * 100:+.1f}% "
        f"({overall_comp.accuracy_change_percent:+.2f}%)"
    )
    print(f"    P95 Latency: {overall_comp.p95_change:+.0f} ms")
    print(f"    Total Cost: ${overall_comp.cost_change:+.2f} ({overall_comp.cost_change_percent:+.2f}%)")
    print()

    # Get trend summary
    print("📈 Trend Summary:")
    summary = comparator.get_trend_summary(runs)
    print(f"  Total Runs: {summary['total_runs']}")
    print()
    print("  Score Trend:")
    print(f"    First: {summary['score_trend']['first']:.1f}")
    print(f"    Last: {summary['score_trend']['last']:.1f}")
    print(f"    Change: {summary['score_trend']['change']:+.1f}")
    print(f"    Min: {summary['score_trend']['min']:.1f}")
    print(f"    Max: {summary['score_trend']['max']:.1f}")
    print(f"    Average: {summary['score_trend']['average']:.1f}")
    print()
    print("  Accuracy Trend:")
    print(f"    First: {summary['accuracy_trend']['first']:.1f}%")
    print(f"    Last: {summary['accuracy_trend']['last']:.1f}%")
    print(f"    Change: {summary['accuracy_trend']['change']:+.1f}%")
    print(f"    Min: {summary['accuracy_trend']['min']:.1f}%")
    print(f"    Max: {summary['accuracy_trend']['max']:.1f}%")
    print(f"    Average: {summary['accuracy_trend']['average']:.1f}%")
    print()

    print("✅ Example completed successfully!")
    print(f"   Results saved to: {store.storage_dir}")


if __name__ == "__main__":
    main()
