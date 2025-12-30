# API Reference

Complete API reference for Open NL2Data-Bench modules.

## Table of Contents

- [Reporting Module](#reporting-module)
- [Evaluation Module](#evaluation-module)
- [Database Adapters](#database-adapters)
- [SUT Adapters](#sut-adapters)
- [Core Types](#core-types)

---

## Reporting Module

### HTMLReportGenerator

Generate professional HTML reports with six-dimensional evaluation.

```python
from onb.reporting import HTMLReportGenerator, ReportData, CertificationLevel

generator = HTMLReport Generator()
html = generator.generate_html(report_data: ReportData) -> str
generator.save_report(html: str, filepath: str) -> None
```

**ReportData Fields:**
- `system_name: str` - Name of the system being evaluated
- `test_date: datetime` - Date of the test
- `overall_score: float` - Overall score (0-100)
- `accuracy_rate: float` - Accuracy rate (0-1)
- `total_questions: int` - Total questions tested
- `correct_answers: int` - Number of correct answers
- `performance_metrics: Optional[PerformanceMetrics]` - Performance data
- `total_cost: Optional[float]` - Total cost in USD
- `robustness_pass_rate: Optional[float]` - Robustness pass rate (0-1)
- `model_name: Optional[str]` - LLM model used
- `database_type: Optional[str]` - Database type

**Certification Levels:**
- `PLATINUM`: 90-100 points
- `GOLD`: 80-89 points
- `SILVER`: 70-79 points
- `BRONZE`: 60-69 points

### ChartGenerator

Generate interactive Chart.js visualizations.

```python
from onb.reporting import ChartGenerator, ChartType

generator = ChartGenerator()

# Accuracy trend chart
generator.generate_accuracy_trend_chart(
    labels: List[str],
    accuracy_values: List[float],
    chart_id: str = "accuracyTrend"
) -> ChartData

# Performance comparison
generator.generate_performance_comparison_chart(
    system_names: List[str],
    p50_values: List[float],
    p95_values: List[float],
    p99_values: List[float],
    chart_id: str = "performanceComparison"
) -> ChartData

# Six-dimension radar chart
generator.generate_six_dimension_radar_chart(
    scores: Dict[str, float],
    chart_id: str = "sixDimensionRadar"
) -> ChartData

# Cost distribution pie chart
generator.generate_cost_distribution_chart(
    model_names: List[str],
    costs: List[float],
    chart_id: str = "costDistribution"
) -> ChartData

# Token usage stacked bar chart
generator.generate_token_usage_chart(
    labels: List[str],
    input_tokens: List[int],
    output_tokens: List[int],
    chart_id: str = "tokenUsage"
) -> ChartData

# Generate HTML/JavaScript
generator.generate_all_charts_html() -> str
generator.generate_all_charts_script() -> str
generator.reset() -> None
```

### Result Comparison

Track and compare results across multiple test runs.

```python
from onb.reporting import ResultStore, ResultComparator, TestRunResult, ComparisonResult

# Store results
store = ResultStore(storage_dir: str = ".onb_results")
store.save_result(result: TestRunResult) -> None
store.load_result(run_id: str) -> Optional[TestRunResult]
store.list_runs(
    system_name: Optional[str] = None,
    limit: Optional[int] = None
) -> List[TestRunResult]
store.delete_result(run_id: str) -> bool

# Compare results
comparator = ResultComparator()
comparison = comparator.compare(
    baseline: TestRunResult,
    current: TestRunResult
) -> ComparisonResult

comparisons = comparator.compare_multiple(
    runs: List[TestRunResult]
) -> List[ComparisonResult]

summary = comparator.get_trend_summary(
    runs: List[TestRunResult]
) -> Dict[str, Any]
```

**ComparisonResult Fields:**
- `score_change: float` - Score change (absolute)
- `score_change_percent: float` - Score change (percentage)
- `accuracy_change: float` - Accuracy change
- `p50_change: Optional[float]` - P50 latency change (ms)
- `p95_change: Optional[float]` - P95 latency change (ms)
- `p99_change: Optional[float]` - P99 latency change (ms)
- `cost_change: Optional[float]` - Cost change (USD)
- `cost_change_percent: Optional[float]` - Cost change (percentage)
- `is_regression: bool` - Whether this is a regression
- `improved_dimensions: List[str]` - List of improved dimensions
- `regressed_dimensions: List[str]` - List of regressed dimensions

---

## Evaluation Module

### Performance Profiler

Measure execution time with statistical analysis.

```python
from onb.evaluation import PerformanceProfiler, PerformanceSample

profiler = PerformanceProfiler(warmup_iterations: int = 5)

# Measure function performance
metrics = profiler.measure(
    func: Callable,
    *args,
    iterations: int = 1,
    **kwargs
) -> PerformanceMetrics

# Add manual samples
profiler.add_sample(sample: PerformanceSample) -> None

# Compute metrics
metrics = profiler.compute_metrics() -> PerformanceMetrics
profiler.reset() -> None
```

**PerformanceMetrics Fields:**
- `median_time_ms: float` - Median execution time
- `mean_time_ms: float` - Mean execution time
- `p50: float` - 50th percentile (same as median)
- `p95: float` - 95th percentile
- `p99: float` - 99th percentile
- `min_time_ms: float` - Minimum execution time
- `max_time_ms: float` - Maximum execution time
- `std_dev: float` - Standard deviation
- `measurements: List[float]` - All measurements

### Throughput Meter

Track queries per second and success rate.

```python
from onb.evaluation import ThroughputMeter

meter = ThroughputMeter()
meter.start() -> None
meter.record_success() -> None
meter.record_failure() -> None
results = meter.stop() -> Dict[str, Any]

# Results include:
# - qps: float
# - total_queries: int
# - successful_queries: int
# - failed_queries: int
# - success_rate: float
# - error_rate: float
# - duration_seconds: float
```

### Concurrent Performance Tester

Async concurrent load testing.

```python
from onb.evaluation import ConcurrentPerformanceTester

tester = ConcurrentPerformanceTester(concurrency: int = 10)

results = await tester.run_async(
    async_func: Callable,
    *args,
    test_duration_seconds: int = 60,
    **kwargs
) -> Dict[str, Any]

# Results include:
# - total_queries: int
# - successful_queries: int
# - failed_queries: int
# - qps: float
# - success_rate: float
# - error_rate: float
# - avg_latency_ms: float
# - duration_seconds: float
```

### Cost Calculator

Calculate LLM API costs across providers.

```python
from onb.evaluation import CostCalculator, TokenUsage, ModelPricing, LLMProvider

calculator = CostCalculator(custom_pricing: Optional[Dict[str, ModelPricing]] = None)

cost = calculator.calculate_cost(
    token_usage: TokenUsage,
    model_name: str
) -> CostSample

pricing = calculator.get_pricing(model_name: str) -> ModelPricing
calculator.add_custom_pricing(model_name: str, pricing: ModelPricing) -> None
```

**Supported Providers:**
- OpenAI (gpt-4-turbo, gpt-4o, gpt-3.5-turbo)
- Anthropic (claude-3-opus, claude-3-sonnet, claude-3-haiku)
- Google (gemini-pro, gemini-1.5-pro)
- Azure OpenAI
- Cohere (command, command-light)
- Custom providers

### Cost Tracker

Batch cost tracking and aggregation.

```python
from onb.evaluation import CostTracker

tracker = CostTracker(calculator: Optional[CostCalculator] = None)

sample = tracker.track(
    token_usage: TokenUsage,
    model_name: str
) -> CostSample

summary = tracker.get_summary() -> Dict[str, Any]

# Summary includes:
# - total_queries: int
# - total_cost: float
# - average_cost_per_query: float
# - cost_breakdown: Dict (input/output)
# - cost_by_model: Dict[str, float]
# - token_stats: Dict
```

### Robustness Evaluator

Test system behavior with edge cases and errors.

```python
from onb.evaluation import RobustnessEvaluator, RobustnessTestCase, RobustnessTestResult

evaluator = RobustnessEvaluator()

# Generate test cases
edge_cases = evaluator.generate_edge_cases() -> List[RobustnessTestCase]
error_cases = evaluator.generate_error_cases() -> List[RobustnessTestCase]
quality_cases = evaluator.generate_data_quality_cases() -> List[RobustnessTestCase]

# Run test
result = evaluator.run_test(
    test_case: RobustnessTestCase,
    test_func: Callable
) -> RobustnessTestResult

# Batch evaluation
results = evaluator.evaluate_batch(
    test_cases: List[RobustnessTestCase],
    test_func: Callable
) -> List[RobustnessTestResult]
```

**Test Types:**
- `EDGE_CASE`: Empty results, NULL values, special characters, Unicode, large numbers
- `ERROR_HANDLING`: Malformed SQL, invalid tables/columns, division by zero
- `DATA_QUALITY`: Duplicates, whitespace, case sensitivity, NULL vs empty

---

## Database Adapters

### PostgreSQL Adapter

```python
from onb.adapters.database import PostgreSQLAdapter

adapter = PostgreSQLAdapter(
    host: str = "localhost",
    port: int = 5432,
    database: str,
    user: str,
    password: str,
    **kwargs
)

await adapter.connect() -> None
result = await adapter.execute_query(sql: str, params: Optional[Dict] = None) -> pd.DataFrame
version = await adapter.get_database_version() -> str
await adapter.close() -> None
```

### ClickHouse Adapter

```python
from onb.adapters.database import ClickHouseAdapter

adapter = ClickHouseAdapter(
    host: str = "localhost",
    port: int = 9000,
    database: str = "default",
    user: str = "default",
    password: str = "",
    **kwargs
)
```

### Apache Doris Adapter

```python
from onb.adapters.database import DorisAdapter

adapter = DorisAdapter(
    host: str = "localhost",
    port: int = 9030,
    database: str,
    user: str = "root",
    password: str = "",
    **kwargs
)
```

---

## SUT Adapters

### HTTP Adapter

Generic HTTP/REST API adapter with JSONPath response mapping.

```python
from onb.adapters.sut import HTTPAdapter

adapter = HTTPAdapter(
    endpoint_url: str,
    method: str = "POST",
    headers: Optional[Dict[str, str]] = None,
    request_mapping: Optional[Dict[str, str]] = None,
    response_mapping: Optional[Dict[str, str]] = None,
    timeout: int = 30
)

response = await adapter.query(
    question: str,
    schema_info: SchemaInfo
) -> NL2SQLResponse
```

**Response Mapping:**
- `generated_sql`: JSONPath to SQL (e.g., `"$.data.sql"`)
- `result_data`: JSONPath to result data (e.g., `"$.data.result"`)
- `token_usage.total_tokens`: JSONPath to token count
- `execution_time_ms`: JSONPath to timing data

---

## Core Types

### PerformanceMetrics

```python
@dataclass
class PerformanceMetrics:
    median_time_ms: float
    mean_time_ms: float
    p50: float
    p95: float
    p99: float
    min_time_ms: float
    max_time_ms: float
    std_dev: float
    measurements: List[float]
```

### TokenUsage

```python
@dataclass
class TokenUsage:
    input_tokens: int
    output_tokens: int
    total_tokens: int
```

### CostSample

```python
@dataclass
class CostSample:
    model_name: str
    input_tokens: int
    output_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float
    timestamp: float
```

### TestRunResult

```python
@dataclass
class TestRunResult:
    run_id: str
    timestamp: datetime
    system_name: str
    overall_score: float
    accuracy_rate: float
    total_questions: int
    correct_answers: int
    performance_metrics: Optional[PerformanceMetrics] = None
    total_cost: Optional[float] = None
    avg_cost_per_query: Optional[float] = None
    robustness_pass_rate: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
```

---

## Error Handling

All modules use standard Python exceptions:

- `ValueError`: Invalid parameters
- `TypeError`: Wrong type passed
- `ConnectionError`: Database/API connection issues
- `TimeoutError`: Operation timeout
- `RuntimeError`: General runtime errors

Example:

```python
try:
    metrics = profiler.measure(my_function, iterations=100)
except ValueError as e:
    print(f"Invalid parameters: {e}")
except RuntimeError as e:
    print(f"Measurement failed: {e}")
```

---

## Best Practices

1. **Always use context managers** for database connections
2. **Validate inputs** before passing to APIs
3. **Handle timeouts** for long-running operations
4. **Reset profilers/meters** between test runs
5. **Store results** for long-term tracking
6. **Use async** for concurrent operations
7. **Check coverage** with `pytest --cov`

---

For more examples, see the `examples/` directory and [QUICKSTART.md](QUICKSTART.md).
