"""Example demonstrating HTML report generation."""
from datetime import datetime

from onb.core.types import PerformanceMetrics
from onb.reporting import HTMLReportGenerator, ReportData


def generate_sample_report():
    """Generate a sample HTML report."""
    # Create sample performance metrics
    perf_metrics = PerformanceMetrics(
        median_time_ms=1234.5,
        mean_time_ms=1289.3,
        p50=1234.5,
        p95=2456.7,
        p99=3012.4,
        min_time_ms=892.1,
        max_time_ms=3521.8,
        std_dev=427.6,
        measurements=[1000, 1200, 1300, 1500, 2000],
    )

    # Create report data
    report_data = ReportData(
        system_name="MyNL2SQL System",
        test_date=datetime(2025, 1, 15, 14, 30, 0),
        overall_score=87.3,
        # Accuracy
        total_questions=30,
        correct_answers=26,
        accuracy_rate=0.867,
        # Performance
        performance_metrics=perf_metrics,
        # Cost
        total_cost=0.45,
        avg_cost_per_query=0.015,
        total_tokens=18500,
        # Robustness
        robustness_pass_rate=0.82,
        robustness_tests_passed=23,
        robustness_tests_total=28,
        # Metadata
        model_name="gpt-4-turbo",
        database_type="PostgreSQL",
        domain="ecommerce",
    )

    # Generate report
    generator = HTMLReportGenerator()
    generator.generate(report_data, "examples/reports/sample_report.html")
    print("✅ Sample report generated: examples/reports/sample_report.html")


if __name__ == "__main__":
    generate_sample_report()
