# Quick Start Guide

This guide will help you get started with OpenNL2Data-Bench in 5 minutes.

## Table of Contents

- [Installation](#installation)
- [Generate Your First Report](#generate-your-first-report)
- [Add Interactive Charts](#add-interactive-charts)
- [Track Performance Over Time](#track-performance-over-time)
- [Evaluate Performance](#evaluate-performance)
- [Calculate Costs](#calculate-costs)
- [Test Robustness](#test-robustness)
- [Next Steps](#next-steps)

---

## Installation

### Prerequisites

- Python 3.10 or higher
- Poetry (recommended) or pip

### Install with Poetry (Recommended)

```bash
# Clone the repository
git clone https://github.com/powerdata-ai/open-nl2data-bench.git
cd open-nl2data-bench

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

### Install with pip

```bash
# Clone the repository
git clone https://github.com/powerdata-ai/open-nl2data-bench.git
cd open-nl2data-bench

# Install in editable mode
pip install -e .
```

### Verify Installation

```bash
# Run tests to verify installation
pytest tests/unit/test_html_generator.py -v
```

---

## Generate Your First Report

Create a simple HTML report with evaluation results:

```python
from datetime import datetime
from onb.core.types import PerformanceMetrics
from onb.reporting import HTMLReportGenerator, ReportData

# Create performance metrics
perf_metrics = PerformanceMetrics(
    median_time_ms=1234.5,
    mean_time_ms=1289.3,
    p50=1234.5,
    p95=2456.7,
    p99=3012.4,
    min_time_ms=892.1,
    max_time_ms=3521.8,
    std_dev=427.6,
    measurements=[]
)

# Create report data
report_data = ReportData(
    system_name="My NL2SQL System",
    test_date=datetime.now(),
    overall_score=85.5,
    total_questions=100,
    correct_answers=87,
    accuracy_rate=0.87,
    performance_metrics=perf_metrics,
    total_cost=0.52,
    avg_cost_per_query=0.0052,
    total_tokens=19800,
    robustness_pass_rate=0.85,
    robustness_tests_passed=24,
    robustness_tests_total=28,
    model_name="gpt-4-turbo",
    database_type="PostgreSQL",
    domain="ecommerce"
)

# Generate HTML report
generator = HTMLReportGenerator()
html = generator.generate_html(report_data)

# Save to file
with open("my_first_report.html", "w", encoding="utf-8") as f:
    f.write(html)

print("✅ Report generated: my_first_report.html")
```

**Run the example:**
```bash
PYTHONPATH=. python examples/generate_sample_report.py
open examples/reports/sample_report.html
```

---

## Add Interactive Charts

Enhance your reports with Chart.js visualizations:

```python
from onb.reporting import ChartGenerator

# Create chart generator
chart_gen = ChartGenerator()

# 1. Accuracy trend over time
chart_gen.generate_accuracy_trend_chart(
    labels=["Week 1", "Week 2", "Week 3", "Week 4"],
    accuracy_values=[75.0, 82.5, 87.3, 90.0]
)

# 2. Performance comparison
chart_gen.generate_performance_comparison_chart(
    system_names=["Our System", "Competitor A", "Competitor B"],
    p50_values=[1234, 1850, 2100],
    p95_values=[2456, 3200, 3800],
    p99_values=[3012, 4100, 4500]
)

# 3. Six-dimension radar chart
chart_gen.generate_six_dimension_radar_chart({
    "Accuracy": 90.0,
    "Performance": 85.0,
    "Cost": 82.0,
    "Robustness": 85.0,
    "UX": 88.0,
    "Concurrency": 91.0
})

# 4. Token usage breakdown
chart_gen.generate_token_usage_chart(
    labels=["Simple", "Medium", "Complex"],
    input_tokens=[800, 1500, 2500],
    output_tokens=[200, 400, 800]
)

# Generate all charts HTML and JavaScript
charts_html = chart_gen.generate_all_charts_html()
charts_script = chart_gen.generate_all_charts_script()

print("✅ Generated 4 interactive charts")
```

**Run the example:**
```bash
PYTHONPATH=. python examples/generate_enhanced_report.py
open examples/reports/enhanced_report_with_charts.html
```

---

## Track Performance Over Time

Compare results across multiple test runs:

```python
from datetime import datetime
from onb.reporting import ResultStore, ResultComparator, TestRunResult

# Initialize store and comparator
store = ResultStore(storage_dir=".my_results")
comparator = ResultComparator()

# Create test run results
run1 = TestRunResult(
    run_id="baseline_v1.0",
    timestamp=datetime(2025, 1, 1),
    system_name="My System v1.0",
    overall_score=75.0,
    accuracy_rate=0.75,
    total_questions=100,
    correct_answers=75,
    total_cost=2.5
)

run2 = TestRunResult(
    run_id="optimized_v1.1",
    timestamp=datetime(2025, 1, 15),
    system_name="My System v1.1",
    overall_score=85.0,
    accuracy_rate=0.85,
    total_questions=100,
    correct_answers=85,
    total_cost=2.0
)

# Save results
store.save_result(run1)
store.save_result(run2)

# Compare runs
comparison = comparator.compare(run1, run2)

print(f"Score change: {comparison.score_change_percent:+.2f}%")
print(f"Accuracy change: {comparison.accuracy_change_percent:+.2f}%")
print(f"Cost change: ${comparison.cost_change:+.2f} ({comparison.cost_change_percent:+.2f}%)")
print(f"Is regression: {comparison.is_regression}")
print(f"Improved dimensions: {comparison.improved_dimensions}")
print(f"Regressed dimensions: {comparison.regressed_dimensions}")

# Get trend summary for all runs
all_runs = store.list_runs()
summary = comparator.get_trend_summary(all_runs)

print(f"\nTrend Summary:")
print(f"  Score: {summary['score_trend']['first']:.1f} → {summary['score_trend']['last']:.1f}")
print(f"  Change: {summary['score_trend']['change']:+.1f}")
```

**Run the example:**
```bash
PYTHONPATH=. python examples/compare_test_runs.py
```

---

## Evaluate Performance

Measure execution time, throughput, and concurrency:

### Performance Profiling

```python
from onb.evaluation import PerformanceProfiler

def my_nl2sql_function(question):
    # Your NL2SQL implementation
    return "SELECT * FROM users WHERE age > 18"

# Create profiler with warmup
profiler = PerformanceProfiler(warmup_iterations=3)

# Measure performance
metrics = profiler.measure(
    my_nl2sql_function,
    "Show me all users over 18",
    iterations=100
)

print(f"P50 latency: {metrics.p50:.2f}ms")
print(f"P95 latency: {metrics.p95:.2f}ms")
print(f"P99 latency: {metrics.p99:.2f}ms")
print(f"Mean: {metrics.mean_time_ms:.2f}ms")
print(f"Std dev: {metrics.std_dev:.2f}ms")
```

### Throughput Measurement

```python
from onb.evaluation import ThroughputMeter
import time

meter = ThroughputMeter()
meter.start()

# Process queries
for i in range(1000):
    try:
        result = my_nl2sql_function(f"Query {i}")
        meter.record_success()
    except Exception:
        meter.record_failure()

results = meter.stop()

print(f"QPS: {results['qps']:.2f}")
print(f"Total queries: {results['total_queries']}")
print(f"Success rate: {results['success_rate']:.2%}")
print(f"Error rate: {results['error_rate']:.2%}")
```

### Concurrent Load Testing

```python
import asyncio
from onb.evaluation import ConcurrentPerformanceTester

async def async_query_func(question):
    # Your async NL2SQL implementation
    await asyncio.sleep(0.1)  # Simulate API call
    return "SELECT * FROM users"

async def run_load_test():
    tester = ConcurrentPerformanceTester(concurrency=10)

    results = await tester.run_async(
        async_query_func,
        "Sample question",
        test_duration_seconds=60
    )

    print(f"Total queries: {results['total_queries']}")
    print(f"QPS: {results['qps']:.2f}")
    print(f"Success rate: {results['success_rate']:.2%}")
    print(f"Error rate: {results['error_rate']:.2%}")
    print(f"Avg latency: {results['avg_latency_ms']:.2f}ms")

# Run the test
asyncio.run(run_load_test())
```

---

## Calculate Costs

Track token usage and calculate costs across multiple LLM providers:

### Cost Calculation

```python
from onb.evaluation import CostCalculator, TokenUsage

# Create calculator
calculator = CostCalculator()

# Calculate cost for a single query
token_usage = TokenUsage(
    input_tokens=1000,
    output_tokens=500,
    total_tokens=1500
)

cost = calculator.calculate_cost(token_usage, model_name="gpt-4-turbo")

print(f"Input cost: ${cost.input_cost:.4f}")
print(f"Output cost: ${cost.output_cost:.4f}")
print(f"Total cost: ${cost.total_cost:.4f}")
```

### Cost Tracking

```python
from onb.evaluation import CostTracker

# Create tracker
tracker = CostTracker()

# Track multiple queries
for i in range(100):
    token_usage = TokenUsage(
        input_tokens=800 + i * 10,
        output_tokens=400 + i * 5
    )
    tracker.track(token_usage, "gpt-4-turbo")

# Get summary
summary = tracker.get_summary()

print(f"Total queries: {summary['total_queries']}")
print(f"Total cost: ${summary['total_cost']:.2f}")
print(f"Average per query: ${summary['average_cost_per_query']:.4f}")
print(f"Total tokens: {summary['token_stats']['total_tokens']:,}")

# Cost breakdown by model
for model, cost in summary['cost_by_model'].items():
    print(f"  {model}: ${cost:.2f}")
```

### Custom Pricing

```python
from onb.evaluation import CostCalculator, ModelPricing, LLMProvider

# Define custom pricing
custom_pricing = ModelPricing(
    model_name="my-custom-model",
    provider=LLMProvider.CUSTOM,
    input_price_per_1k=0.005,
    output_price_per_1k=0.015
)

# Add custom pricing to calculator
calculator = CostCalculator(custom_pricing={"my-custom-model": custom_pricing})

# Calculate cost
cost = calculator.calculate_cost(token_usage, "my-custom-model")
print(f"Cost: ${cost.total_cost:.4f}")
```

---

## Test Robustness

Evaluate system behavior with edge cases and error scenarios:

```python
from onb.evaluation import RobustnessEvaluator

# Create evaluator
evaluator = RobustnessEvaluator()

# Generate test cases
edge_cases = evaluator.generate_edge_cases()
error_cases = evaluator.generate_error_cases()
quality_cases = evaluator.generate_data_quality_cases()

print(f"Generated {len(edge_cases)} edge case tests")
print(f"Generated {len(error_cases)} error handling tests")
print(f"Generated {len(quality_cases)} data quality tests")

# Define your test function
def test_function(input_data):
    query = input_data.get("query", "")
    # Your implementation here
    # Return result or raise exception
    pass

# Run edge case tests
results = []
for test_case in edge_cases:
    result = evaluator.run_test(test_case, test_function)
    results.append(result)

    if not result.passed:
        print(f"❌ FAIL: {test_case.description}")
        print(f"   Expected: {test_case.expected_behavior}")
        print(f"   Actual: {result.actual_behavior}")
    else:
        print(f"✅ PASS: {test_case.description}")

# Calculate pass rate
pass_rate = sum(1 for r in results if r.passed) / len(results)
print(f"\nPass rate: {pass_rate:.1%}")
```

---

## Next Steps

Now that you've mastered the basics, explore more advanced features:

1. **Database Adapters**: Learn how to integrate with PostgreSQL, ClickHouse, or Apache Doris
   - See `onb/adapters/database/` for implementation examples

2. **HTTP API Integration**: Connect to your NL2SQL system via REST API
   - See `examples/http_adapter_example.py`

3. **Custom Adapters**: Build your own adapter for custom databases or APIs
   - Extend `onb.adapters.database.base.DatabaseAdapter`
   - Extend `onb.adapters.sut.base.SUTAdapter`

4. **Advanced Reporting**: Combine all evaluation dimensions into comprehensive reports
   - Performance + Cost + Robustness
   - Multi-run trend analysis
   - Interactive visualizations

5. **CI/CD Integration**: Automate testing in your pipeline
   - Run tests on every commit
   - Track performance regressions
   - Generate reports automatically

## Examples Directory

Check out the `examples/` directory for complete working examples:

- `generate_sample_report.py` - Basic HTML report generation
- `generate_enhanced_report.py` - Report with interactive charts
- `compare_test_runs.py` - Multi-run comparison and trend analysis

## Getting Help

- **Documentation**: Check [README.md](README.md) and [API.md](API.md)
- **Issues**: Report bugs at [GitHub Issues](https://github.com/powerdata-ai/open-nl2data-bench/issues)
- **Discussions**: Ask questions at [GitHub Discussions](https://github.com/powerdata-ai/open-nl2data-bench/discussions)

---

Happy benchmarking! 🚀
