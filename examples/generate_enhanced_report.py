"""Example demonstrating chart generation with HTML reports."""
from datetime import datetime

from onb.core.types import PerformanceMetrics
from onb.reporting import ChartGenerator, HTMLReportGenerator, ReportData


def generate_report_with_charts():
    """Generate HTML report with interactive charts."""
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
        system_name="Advanced NL2SQL System",
        test_date=datetime(2025, 1, 15, 16, 0, 0),
        overall_score=88.7,
        total_questions=30,
        correct_answers=27,
        accuracy_rate=0.90,
        performance_metrics=perf_metrics,
        total_cost=0.52,
        avg_cost_per_query=0.017,
        total_tokens=19800,
        robustness_pass_rate=0.85,
        robustness_tests_passed=24,
        robustness_tests_total=28,
        model_name="gpt-4-turbo",
        database_type="PostgreSQL",
        domain="ecommerce",
    )

    # Create charts
    chart_gen = ChartGenerator()

    # 1. Accuracy trend chart
    chart_gen.generate_accuracy_trend_chart(
        labels=["Week 1", "Week 2", "Week 3", "Week 4"],
        accuracy_values=[75.0, 82.5, 87.3, 90.0],
    )

    # 2. Performance comparison chart
    chart_gen.generate_performance_comparison_chart(
        system_names=["Our System", "Competitor A", "Competitor B"],
        p50_values=[1234, 1850, 2100],
        p95_values=[2456, 3200, 3800],
        p99_values=[3012, 4100, 4500],
    )

    # 3. Six-dimension radar chart
    chart_gen.generate_six_dimension_radar_chart(
        scores={
            "Accuracy": 90.0,
            "Performance": 85.0,
            "Cost": 82.0,
            "Robustness": 85.0,
            "UX": 88.0,
            "Concurrency": 91.0,
        }
    )

    # 4. Token usage chart
    chart_gen.generate_token_usage_chart(
        labels=["Simple", "Medium", "Complex"],
        input_tokens=[800, 1500, 2500],
        output_tokens=[200, 400, 800],
    )

    # Generate base HTML report
    generator = HTMLReportGenerator()
    base_html = generator.generate_html(report_data)

    # Insert charts before closing body tag
    charts_html = f"""
    <div class="content">
        <div class="section">
            <h2>📈 Performance Visualizations</h2>
            {chart_gen.generate_all_charts_html()}
        </div>
    </div>
    """

    # Insert chart script before closing body tag
    charts_script = chart_gen.generate_all_charts_script()

    # Combine everything
    enhanced_html = base_html.replace(
        "</div>\n\n        <footer>",
        f"{charts_html}\n        </div>\n\n        <footer>",
    )
    enhanced_html = enhanced_html.replace(
        "</body>", f"{charts_script}\n</body>"
    )

    # Save report
    output_path = "examples/reports/enhanced_report_with_charts.html"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(enhanced_html)

    print(f"✅ Enhanced report with charts generated: {output_path}")


if __name__ == "__main__":
    generate_report_with_charts()
