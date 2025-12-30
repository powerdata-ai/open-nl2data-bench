# OpenNL2Data-Bench

<div align="center">

**OpenNL2Data-Bench: A Production-Grade Benchmark Framework for NL2Data Systems (NL2SQL, NL2API, NL2Python, etc.)**

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PowerData](https://img.shields.io/badge/PowerData-Community-orange.svg)](https://powerdata.org)

[English](README.md) | [中文](README_zh.md)

</div>

## 📖 Overview

OpenNL2Data-Bench is the world's first **production-oriented** benchmark framework for evaluating NL2Data systems, including NL2SQL (Natural Language to SQL), NL2API, NL2Python, and other natural language-driven data access solutions. Unlike academic benchmarks (Spider, BIRD) that focus solely on SQL generation accuracy, OpenNL2Data-Bench provides **comprehensive, six-dimensional evaluation** covering accuracy, performance, cost, robustness, user experience, and concurrency stability.

**Key Features:**

- 🎯 **Six-Dimensional Evaluation**: Accuracy, performance, cost, robustness, UX, concurrency
- 🔄 **Dynamic Data Generation**: Versioned, reproducible datasets with quality tiers (high/medium/low)
- 🧪 **Result-Set Comparison**: Execute queries and compare actual results, not text matching
- 🚀 **Zero-Code Integration**: JMeter-inspired vendor integration (5-10 minutes setup)
- 🛡️ **Anti-Fraud System**: Multi-layer validation to ensure data integrity
- 📊 **Production Scenarios**: Load testing, mixed workloads, long-term stability
- 🏆 **Certification System**: Bronze/Silver/Gold/Platinum vendor certification
- 🌐 **Multi-Interface Support**: SQL databases, REST APIs, Python code generation, and more

**Community:**

- **Organization**: [PowerData数据之力社区](https://powerdata.org)
- **License**: Apache 2.0
- **Vision**: Become the **TPC-H/TPC-DS** equivalent for NL2Data industry

---

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/powerdata-ai/open-nl2data-bench.git
cd open-nl2data-bench

# Install dependencies using Poetry (recommended for development)
poetry install

# Or install using pip
pip install -e .
```

### Run Your First Test

```python
from datetime import datetime
from onb.core.types import PerformanceMetrics
from onb.reporting import HTMLReportGenerator, ReportData

# Create report data
report_data = ReportData(
    system_name="My NL2SQL System",
    test_date=datetime.now(),
    overall_score=85.5,
    total_questions=100,
    correct_answers=87,
    accuracy_rate=0.87,
    performance_metrics=PerformanceMetrics(
        median_time_ms=1234.5,
        mean_time_ms=1289.3,
        p50=1234.5,
        p95=2456.7,
        p99=3012.4,
        min_time_ms=892.1,
        max_time_ms=3521.8,
        std_dev=427.6,
        measurements=[]
    ),
    total_cost=0.52,
    avg_cost_per_query=0.0052,
    model_name="gpt-4-turbo"
)

# Generate HTML report
generator = HTMLReportGenerator()
html = generator.generate_html(report_data)

# Save report
with open("my_report.html", "w") as f:
    f.write(html)
```

### Run Example Scripts

```bash
# Generate sample HTML report
PYTHONPATH=. python examples/generate_sample_report.py

# Generate enhanced report with charts
PYTHONPATH=. python examples/generate_enhanced_report.py

# Compare multiple test runs
PYTHONPATH=. python examples/compare_test_runs.py
```

---

## 📦 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│          Reporting & Visualization Layer                    │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │ HTML Reports │  │ Chart.js     │  │ Result          │  │
│  │ Generator    │  │ Visualizer   │  │ Comparison      │  │
│  └──────────────┘  └──────────────┘  └─────────────────┘  │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│              Core Evaluation Engine                          │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │ Performance │  │ Cost         │  │ Robustness      │   │
│  │ Profiler    │  │ Calculator   │  │ Evaluator       │   │
│  └─────────────┘  └──────────────┘  └─────────────────┘   │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │ Result      │  │ Throughput   │  │ Concurrent      │   │
│  │ Comparator  │  │ Meter        │  │ Tester          │   │
│  └─────────────┘  └──────────────┘  └─────────────────┘   │
└────────────────────────────┬────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
┌────────▼────────┐   ┌──────▼────────┐   ┌─────▼────────┐
│ Database        │   │ SUT Adapters  │   │ Question     │
│ Adapters        │   │               │   │ Bank         │
│ - PostgreSQL    │   │ - HTTP/REST   │   │              │
│ - ClickHouse    │   │ - Mock        │   │              │
│ - Apache Doris  │   │ - Custom      │   │              │
│ - MySQL         │   │               │   │              │
└─────────────────┘   └───────────────┘   └──────────────┘
```

**Key Components:**

- **Reporting Layer**: HTML report generation with Chart.js visualizations and multi-run comparison
- **Evaluation Engine**: Performance profiling, cost calculation, robustness testing
- **Database Adapters**: Support for PostgreSQL, ClickHouse, Apache Doris, MySQL
- **SUT Adapters**: HTTP/REST API integration, mock implementations, custom adapters
- **Question Bank**: Structured question library with golden answers

---

## ✨ Implemented Features

### 📊 Reporting & Visualization

#### HTML Report Generator
Professional HTML reports with embedded CSS and responsive design:
- **Certification Levels**: Platinum (90+), Gold (80-89), Silver (70-79), Bronze (60-69)
- **Six-Dimensional Display**: Visual representation of all evaluation dimensions
- **Color-Coded Metrics**: Intuitive good/warning/bad indicators
- **Responsive Design**: Mobile-friendly layout

Example:
```python
from onb.reporting import HTMLReportGenerator, ReportData

generator = HTMLReportGenerator()
html = generator.generate_html(report_data)
generator.save_report(html, "my_report.html")
```

#### Interactive Charts (Chart.js)
Five types of interactive visualizations:
- **Line Charts**: Accuracy trends over time
- **Bar Charts**: Performance comparison (P50/P95/P99), token usage
- **Radar Charts**: Six-dimensional evaluation
- **Pie Charts**: Cost distribution by model

Example:
```python
from onb.reporting import ChartGenerator

chart_gen = ChartGenerator()
chart_gen.generate_accuracy_trend_chart(
    labels=["Week 1", "Week 2", "Week 3"],
    accuracy_values=[75.0, 82.5, 90.0]
)
chart_gen.generate_six_dimension_radar_chart({
    "Accuracy": 90.0,
    "Performance": 85.0,
    "Cost": 82.0,
    "Robustness": 85.0,
    "UX": 88.0,
    "Concurrency": 91.0
})
```

#### Multi-Run Result Comparison
Track performance across multiple test runs:
- **JSON Storage**: Persistent storage in `.onb_results/` directory
- **Regression Detection**: Automatic detection of 5%+ performance drops
- **Trend Analysis**: Score/accuracy/performance trends over time
- **Dimension Tracking**: Identify improved/regressed dimensions

Example:
```python
from onb.reporting import ResultStore, ResultComparator

store = ResultStore()
comparator = ResultComparator()

# Save results
store.save_result(test_run_result)

# Compare runs
comparison = comparator.compare(baseline, current)
print(f"Score change: {comparison.score_change_percent:+.2f}%")
print(f"Improved: {comparison.improved_dimensions}")
print(f"Regressed: {comparison.regressed_dimensions}")

# Get trend summary
summary = comparator.get_trend_summary(runs)
```

### ⚡ Performance Evaluation

#### Performance Profiler
Comprehensive timing measurements with statistical analysis:
- **Warmup Support**: Configurable warmup iterations
- **Percentile Metrics**: P50/P95/P99 latency measurements
- **Component Breakdown**: SQL generation vs. execution time
- **Statistical Analysis**: Mean, median, std dev using numpy

Example:
```python
from onb.evaluation import PerformanceProfiler

profiler = PerformanceProfiler(warmup_iterations=3)
metrics = profiler.measure(my_function, iterations=100)

print(f"P50: {metrics.p50:.2f}ms")
print(f"P95: {metrics.p95:.2f}ms")
print(f"P99: {metrics.p99:.2f}ms")
```

#### Throughput Meter
Real-time QPS and success rate tracking:
```python
from onb.evaluation import ThroughputMeter

meter = ThroughputMeter()
meter.start()

# ... process queries ...

results = meter.stop()
print(f"QPS: {results['qps']:.2f}")
print(f"Success rate: {results['success_rate']:.2%}")
```

#### Concurrent Performance Tester
Async concurrent load testing:
```python
from onb.evaluation import ConcurrentPerformanceTester

tester = ConcurrentPerformanceTester(concurrency=10)
results = await tester.run_async(async_query_func, test_duration_seconds=60)

print(f"Total queries: {results['total_queries']}")
print(f"QPS: {results['qps']:.2f}")
print(f"Error rate: {results['error_rate']:.2%}")
```

### 💰 Cost Evaluation

#### Multi-Provider Cost Calculator
Support for major LLM providers with January 2025 pricing:
- **Providers**: OpenAI, Anthropic, Google, Azure, Cohere, Custom
- **Token Tracking**: Input/output token consumption
- **Cost Aggregation**: Per-query and batch cost analysis
- **Model Support**: GPT-4 Turbo, Claude 3, Gemini Pro, and more

Example:
```python
from onb.evaluation import CostCalculator, TokenUsage

calculator = CostCalculator()
cost = calculator.calculate_cost(
    token_usage=TokenUsage(input_tokens=1000, output_tokens=500),
    model_name="gpt-4-turbo"
)

print(f"Total cost: ${cost.total_cost:.4f}")
print(f"Input cost: ${cost.input_cost:.4f}")
print(f"Output cost: ${cost.output_cost:.4f}")
```

#### Cost Tracker
Batch tracking and summary statistics:
```python
from onb.evaluation import CostTracker

tracker = CostTracker()

for query in queries:
    tracker.track(token_usage, model_name)

summary = tracker.get_summary()
print(f"Total cost: ${summary['total_cost']:.2f}")
print(f"Average per query: ${summary['average_cost_per_query']:.4f}")
print(f"Cost by model: {summary['cost_by_model']}")
```

### 🛡️ Robustness Testing

#### Edge Case Testing
15+ pre-generated test cases:
- Empty result sets
- NULL values
- Special characters (quotes, backslashes)
- Unicode and emoji
- Very large numbers
- Whitespace variations

#### Error Handling Testing
- Malformed SQL syntax
- Invalid table/column names
- Division by zero
- Type mismatches
- Permission errors

#### Data Quality Testing
- Duplicate records
- Whitespace handling
- Case sensitivity
- NULL vs empty strings

Example:
```python
from onb.evaluation import RobustnessEvaluator

evaluator = RobustnessEvaluator()

# Generate test cases
edge_cases = evaluator.generate_edge_cases()
error_cases = evaluator.generate_error_cases()

# Run tests
for test_case in edge_cases:
    result = evaluator.run_test(test_case, my_test_function)
    print(f"{test_case.test_id}: {'PASS' if result.passed else 'FAIL'}")
```

### 🔌 Database & SUT Adapters

#### Database Adapters
- **PostgreSQL**: Full support with advanced features
- **ClickHouse**: Optimized for OLAP workloads
- **Apache Doris**: MPP database support
- **MySQL**: Traditional RDBMS support

#### SUT Adapters
- **HTTP/REST API**: Generic HTTP adapter with JSONPath response mapping
- **Mock Adapter**: Testing and development support
- **Custom Adapters**: Extensible base class for custom implementations

Example HTTP Adapter:
```python
from onb.adapters.sut import HTTPAdapter

adapter = HTTPAdapter(
    endpoint_url="https://api.example.com/nl2sql",
    response_mapping={
        "generated_sql": "$.data.sql",
        "result_data": "$.data.result",
        "token_usage.total_tokens": "$.usage.total"
    }
)

response = await adapter.query(question, schema_info)
```

---

## 🎯 Core Concepts

### 1. Six-Dimensional Evaluation

| Dimension | Metrics | Business Value |
|-----------|---------|----------------|
| **Accuracy** | Exact match rate | Does the system truly understand the question? |
| **Performance** | P50/P95/P99 latency | User satisfaction |
| **Cost** | Token consumption, $/query | Economic viability at scale |
| **Robustness** | Performance on dirty data | Adaptability to real-world scenarios |
| **User Experience** | TTFB, error clarity | Real user perception |
| **Concurrency** | QPS, error rate under load | Production readiness |

### 2. Quality-Tiered Testing

Test your system against **three quality levels** of table schemas:

- **High (80%)**: Clean naming, complete comments, proper design
- **Medium (15%)**: Reasonable abbreviations, partial comments
- **Low (5%)**: Cryptic names, no comments, poor design

**Robustness Score** = (Low Quality Accuracy / High Quality Accuracy) × 100%

### 3. Result-Set Comparison

Unlike text-based SQL matching, we **execute the generated SQL** and compare actual results:

- ✅ Handles SQL equivalence (different syntax, same result)
- ✅ Smart float comparison (configurable tolerance)
- ✅ Type-aware comparison (NULL, datetime, strings)
- ✅ Database-specific normalization

---

## 🔌 Vendor Integration (JMeter-Inspired)

### Level 1: Zero-Code Integration (5-10 minutes)

Just provide your API endpoint and field mappings in YAML:

```yaml
sut_adapter:
  type: http_generic
  endpoint:
    url: "https://your-api.com/nl2sql"
  response_mapping:
    generated_sql: "$.data.sql"
    result_data: "$.data.result"
    token_usage.total_tokens: "$.usage.total"
```

No code changes needed! Run the interactive configurator:

```bash
onb adapter create
```

### Level 2: Standard Format (15-30 minutes)

Adjust your API to return our standard format for full metrics:

```json
{
  "success": true,
  "generated_sql": "SELECT ...",
  "result": {"columns": [...], "rows": [...]},
  "execution_time_ms": {
    "nl2sql_conversion": 234,
    "sql_generation": 123,
    "sql_execution": 567
  },
  "token_usage": {
    "input_tokens": 456,
    "output_tokens": 123
  }
}
```

### Level 3: Python SDK (1-2 hours)

Implement our Python adapter interface for maximum flexibility:

```python
from onb.adapters.sut.base import SUTAdapter

class MyNL2SQLAdapter(SUTAdapter):
    async def query(self, question: str, schema_info: SchemaInfo) -> NL2SQLResponse:
        # Your implementation
        pass
```

---

## 🛡️ Anti-Fraud System

To ensure data integrity, we implement a **5-layer defense system**:

1. **Technical Validation**: Client-side timing cross-check, token estimation
2. **Statistical Detection**: Historical data comparison, anomaly detection
3. **Blind Test Bank**: 20% unpublished questions, quarterly refresh
4. **Community Supervision**: Anonymous reporting, whistleblower rewards
5. **Legal Constraints**: Integrity pledge, technical committee arbitration

---

## 📊 Example Report

Generated HTML reports include:

```
┌──────────────────────────────────────────────────────────┐
│  OpenNL2Data-Bench Evaluation Report                     │
│  My NL2SQL System                                         │
│                                                           │
│  🏆 Certification: Gold                                  │
│  Overall Score: 85.5 / 100                               │
│                                                           │
│  ╔════════════════════════════════════════════════════╗  │
│  ║ Six-Dimensional Evaluation                         ║  │
│  ╠════════════════════════════════════════════════════╣  │
│  ║  Accuracy        ████████░░  87.0%                 ║  │
│  ║  Performance     ███████░░░  82.3%                 ║  │
│  ║  Cost            ████████░░  85.0%                 ║  │
│  ║  Robustness      ███████░░░  78.5%                 ║  │
│  ║  UX              ████████░░  88.0%                 ║  │
│  ║  Concurrency     ████████░░  91.0%                 ║  │
│  ╚════════════════════════════════════════════════════╝  │
│                                                           │
│  📈 Performance Metrics                                   │
│    P50: 1,234 ms                                         │
│    P95: 2,457 ms                                         │
│    P99: 3,012 ms                                         │
│                                                           │
│  💰 Cost Analysis                                         │
│    Total Cost: $0.52                                     │
│    Avg per Query: $0.0052                                │
│    Total Tokens: 19,800                                  │
│                                                           │
│  ✅ Test Results                                          │
│    Total Questions: 100                                  │
│    Correct: 87                                           │
│    Accuracy: 87.0%                                       │
└──────────────────────────────────────────────────────────┘
```

View example reports:
- [Sample Report](examples/reports/sample_report.html)
- [Enhanced Report with Charts](examples/reports/enhanced_report_with_charts.html)

---

## 🧪 Testing

The project has comprehensive test coverage:

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=onb --cov-report=html

# Run specific test module
pytest tests/unit/test_performance.py -v
```

**Test Statistics:**
- **Total Tests**: 436 passing
- **Coverage**: 89% overall
- **Test Files**: 17 test modules
- **Test Classes**: 60+ test classes

**Module Coverage:**
- Performance Evaluation: 98%
- Cost Evaluation: 100%
- Robustness Testing: 98%
- HTML Report Generator: 100%
- Chart Generation: 100%
- Result Comparison: 96%
- Database Adapters: 83-95%
- SUT Adapters: 91-99%

---

## 🗓️ Roadmap

- **MVP-0 (Week 1-2)**: Core validation - result-set comparison
- **MVP-1 (Week 3-5)**: Data generation + extended question bank
- **MVP-2 (Week 6-10)**: Quality tiers + full evaluation → **Alpha Release**
- **Phase 2 (Week 11-18)**: Multi-database + load testing → **Beta Release**
- **Phase 3 (Week 19+)**: Certification system + multi-language → **v1.0 Release**

---

## 🤝 Contributing

We welcome contributions from the community! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Ways to contribute:**

- 📝 Submit questions to our question bank
- 🐛 Report bugs and suggest features
- 💻 Implement new database adapters
- 📖 Improve documentation
- 🌍 Translate to other languages

---

## 📄 License

This project is licensed under the **Apache License 2.0** - see the [LICENSE](LICENSE) file for details.

---

## 🌟 Community

- **GitHub**: [powerdata-ai/open-nl2data-bench](https://github.com/powerdata-ai/open-nl2data-bench)
- **Website**: [https://opennl2data-bench.powerdata.org](https://opennl2data-bench.powerdata.org)
- **Email**: team@powerdata.org
- **Discussions**: [GitHub Discussions](https://github.com/powerdata-ai/open-nl2data-bench/discussions)

**Maintainers:**

- PowerData Community Team

---

## 🙏 Acknowledgments

Inspired by:
- **TPC-H/TPC-DS**: Database benchmarking standards
- **JMeter**: Zero-code API testing approach
- **Spider/BIRD**: Academic NL2SQL benchmarks

Special thanks to all contributors and the PowerData community!

---

<div align="center">

**⭐ If you find this project useful, please give us a star! ⭐**

Made with ❤️ by the PowerData Community

</div>
