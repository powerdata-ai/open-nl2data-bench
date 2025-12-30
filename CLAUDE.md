# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**OpenNL2SQL-Bench** is an industry-standard benchmarking framework for evaluating Natural Language to SQL (NL2SQL) systems, similar to TPC-H and TPC-DS for databases.

**Current Status**: Planning phase complete - comprehensive design documentation exists (`OpenNL2SQL-Bench策划方案.md`), but implementation has not yet started. This is a greenfield project ready for initial development.

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Language | Python 3.10+ | Core development |
| Package Manager | Poetry | Dependency management |
| Configuration | YAML + Pydantic | Config files and type-safe validation |
| Data Generation | Faker + Custom Engine | Generate reproducible test data |
| Database Abstraction | SQLAlchemy 2.0 | Unified ORM for OLTP/OLAP databases |
| Data Storage | Parquet (PyArrow) | Columnar storage for test results |
| Load Testing | Locust | Concurrent benchmarking |
| CLI Framework | Typer + Rich | Command-line interface |
| Report Generation | Jinja2 + Plotly | Interactive HTML reports |
| Testing | Pytest | Test framework |

## Project Initialization Commands

**Note**: This project does not yet have a pyproject.toml or any dependencies installed. When beginning implementation:

```bash
# Initialize Poetry project (first time)
poetry init

# Install dependencies (once pyproject.toml exists)
poetry install

# Activate virtual environment
poetry shell

# Run tests (once implemented)
poetry run pytest

# Run CLI (once implemented)
poetry run onb --help
```

## Planned Architecture

### High-Level System Design

```
CLI Console (Typer + Rich)
    ↓
Test Orchestration & Reporting
    ↓
Core Evaluation Engine
    ↓
├── Data Generation (YAML)
├── Question Bank (YAML/JSON)
└── Test Agent (REST/SDK)
```

### Planned Directory Structure

```
open-nl2sql-bench/
├── pyproject.toml              # Poetry configuration
├── onb/                        # Main package (Open NL2SQL Bench)
│   ├── cli/                    # CLI commands
│   ├── core/                   # Core abstractions
│   ├── data/                   # Data generation module
│   ├── questions/              # Question bank management
│   ├── adapters/               # DB & SUT adapters
│   ├── evaluation/             # Evaluation engine
│   ├── benchmark/              # Load testing module
│   ├── reporting/              # Report generation
│   └── utils/                  # Utilities
├── tests/                      # Test suite
├── examples/                   # Example configurations
├── data/                       # Runtime data
└── docs/                       # Documentation
```

## Core Architectural Patterns

### Data Generation
- **Quality Stratification**: Three-tier quality levels (High 80%, Medium 15%, Low 5%)
  - High: Clear naming conventions, complete documentation, proper constraints
  - Medium: Abbreviated naming, partial documentation
  - Low: Cryptic naming, minimal documentation
- **Reproducibility**: YAML-based schema definitions with fixed random seeds
- **Output**: Parquet format for efficient storage

### Evaluation Framework
- **Multi-Dimensional Assessment**:
  - Accuracy: Result set comparison against golden answers
  - Performance: Fine-grained timing (NL2SQL, SQL generation, execution)
  - Cost: Token consumption tracking
  - Robustness: Performance across data quality levels

### Plugin Architecture
- **Database Adapters**: SQLAlchemy-based abstraction layer
  - Priority 0 (Phase 1): MySQL (PyMySQL), PostgreSQL (psycopg3)
  - Priority 1 (Phase 2): ClickHouse, Apache Doris
  - Priority 2 (Phase 3): StarRocks
- **SUT Adapters**: REST API and Python SDK integrations
- **Extensibility**: Base classes for custom adapters

### Concurrency & Load Testing
- **Locust Integration**: Native Python load testing
- **Mixed Workload**: 70% simple queries (L1-L2), 30% complex (L3-L6)
- **Metrics**: QPS, P95/P99 latency, error rates

## Implementation Roadmap

### Phase 1: Core Prototype (4-6 weeks)
1. Initialize Poetry project structure
2. Implement data generation for E-commerce domain
3. Build schema quality stratification engine
4. Create MySQL database adapter
5. Develop question bank (30 questions, L1-L6 complexity)
6. Implement golden answer generation
7. Build result comparison engine
8. Create mock SUT adapter

### Phase 2: Product Maturity (6-8 weeks)
1. Add performance and cost analysis
2. Implement token counting integration
3. Build robustness analyzer
4. Add PostgreSQL and ClickHouse adapters
5. Extend to Finance and Logistics domains
6. Integrate Locust for load testing
7. Enhance CLI and reporting capabilities

### Phase 3: Ecosystem (Long-term)
1. Build official website and leaderboard
2. Enable community question contributions
3. Establish industry partnerships
4. Continue feature evolution

## Development Guidelines

### Code Quality Standards
- Use type hints for all functions (Pydantic models for data structures)
- Write comprehensive docstrings
- Maintain unit test coverage
- Make incremental, compilable changes

### Module Organization
- Clear separation of concerns (data generation, evaluation, adapters, reporting)
- Dependency injection for database and SUT adapters
- Factory pattern for database connections
- Strategy pattern for evaluation algorithms
- Observer pattern for test execution events

### Testing Strategy
- **Unit Tests**: Data generation, result comparison, metrics calculation
- **Integration Tests**: End-to-end workflows, multi-database support
- **E2E Tests**: Complete benchmark cycle from data generation to reporting
- **Load Tests**: Concurrent scenario execution with Locust

### Key Implementation Principles
1. **Reproducibility**: All data generation must be seed-based for exact replication
2. **Floating-Point Tolerance**: Result comparisons must account for floating-point precision differences
3. **Database Abstraction**: Always use SQLAlchemy to avoid vendor lock-in
4. **Configuration-Driven**: Use YAML for all test definitions and schemas
5. **Extensibility First**: Design all adapters and evaluators as plugins

## Question Bank Structure

Test questions span 6 complexity levels:
- **L1**: Single-table simple filtering (SELECT ... WHERE ...)
- **L2**: Single-table aggregation (GROUP BY, HAVING)
- **L3**: Multi-table joins (JOIN)
- **L4**: Nested subqueries
- **L5**: Window functions and advanced aggregations
- **L6**: Mixed complex queries (combining all above)

Target: 99 questions per business domain (E-commerce, Finance, Healthcare, Logistics, HR)

## Evaluation Metrics

### Primary Metrics
1. **Accuracy**: (Exact match count / Total questions) × 100%
2. **Performance**: Average, P50, P95, P99 latencies per stage
3. **Cost**: Average token consumption per question
4. **Robustness**: (Low-quality accuracy / High-quality accuracy) × 100%
5. **Complexity Coverage**: Accuracy distribution across L1-L6 (radar chart)

### Result Comparison Logic
- Exact row-by-row, column-by-column comparison against golden answers
- Column order must match
- Data types must match
- Floating-point values compared with configurable tolerance

## Strategic Context

This project addresses four critical gaps in existing NL2SQL benchmarks (Spider, BIRD):

1. **Evaluation Authenticity**: Real-world data quality variation (not just pristine academic datasets)
2. **Multi-Dimensional Assessment**: Beyond SQL accuracy to include performance, cost, and robustness
3. **Standardization**: Reproducible, comprehensive framework for fair vendor comparison
4. **SQL Equivalence**: Result-set comparison (not text matching) to handle semantically equivalent SQL

## License

Apache 2.0 (commercial-friendly for enterprise adoption)

## Documentation Reference

- **Comprehensive Strategy Document**: `OpenNL2SQL-Bench策划方案.md` (28KB, Chinese)
  - Product vision and positioning
  - Detailed technical architecture
  - Full implementation roadmap
  - Risk assessment and decision points
