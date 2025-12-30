"""
Core type definitions for OpenNL2SQL-Bench.

This module contains all the core data structures used throughout the benchmark framework,
including schema definitions, test questions, results, and metrics.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd


# ============================================================================
# Enums
# ============================================================================


class DatabaseType(str, Enum):
    """Supported database types."""

    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    CLICKHOUSE = "clickhouse"
    DORIS = "doris"
    STARROCKS = "starrocks"


class QualityLevel(str, Enum):
    """Schema quality levels."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ComplexityLevel(str, Enum):
    """Question complexity levels."""

    L1 = "L1"  # Single table, simple filter
    L2 = "L2"  # Single table, aggregation
    L3 = "L3"  # Multi-table JOIN
    L4 = "L4"  # Nested subquery
    L5 = "L5"  # Window functions
    L6 = "L6"  # Complex mixed query


class TestStatus(str, Enum):
    """Test execution status."""

    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"


# ============================================================================
# Schema Definitions
# ============================================================================


@dataclass
class ColumnInfo:
    """Column metadata."""

    name: str
    type: str
    nullable: bool = True
    primary_key: bool = False
    foreign_key: Optional[str] = None
    comment: Optional[str] = None
    default: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "type": self.type,
            "nullable": self.nullable,
            "primary_key": self.primary_key,
            "foreign_key": self.foreign_key,
            "comment": self.comment,
            "default": self.default,
        }


@dataclass
class IndexInfo:
    """Index metadata."""

    name: str
    columns: List[str]
    unique: bool = False
    index_type: Optional[str] = None


@dataclass
class TableInfo:
    """Table metadata."""

    name: str
    columns: List[ColumnInfo]
    quality: QualityLevel = QualityLevel.HIGH
    comment: Optional[str] = None
    indexes: List[IndexInfo] = field(default_factory=list)
    row_count: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "columns": [col.to_dict() for col in self.columns],
            "quality": self.quality.value,
            "comment": self.comment,
            "indexes": [
                {"name": idx.name, "columns": idx.columns, "unique": idx.unique}
                for idx in self.indexes
            ],
            "row_count": self.row_count,
        }


@dataclass
class SchemaInfo:
    """Database schema information."""

    database_name: str
    database_type: DatabaseType
    tables: List[TableInfo]
    version: str = "1.0"
    quality: QualityLevel = QualityLevel.HIGH

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "database": self.database_name,
            "database_type": self.database_type.value,
            "tables": [table.to_dict() for table in self.tables],
            "version": self.version,
            "quality": self.quality.value,
        }

    def get_table(self, table_name: str) -> Optional[TableInfo]:
        """Get table by name."""
        for table in self.tables:
            if table.name == table_name:
                return table
        return None


# ============================================================================
# Question Definitions
# ============================================================================


@dataclass
class ComparisonRules:
    """Rules for result set comparison."""

    row_order_matters: bool = True
    column_order_matters: bool = True
    float_tolerance: float = 1e-6
    float_comparison_mode: str = "relative_error"  # or "absolute_error"
    null_handling: str = "strict"  # or "lenient"
    string_normalization: str = "trim"  # "trim", "lower", or "none"
    string_case_sensitive: bool = False
    datetime_normalize_timezone: bool = True
    datetime_tolerance_ms: int = 0

    def __post_init__(self):
        """Validate comparison rules."""
        if self.float_tolerance <= 0:
            raise ValueError("float_tolerance must be greater than 0")

        valid_comparison_modes = ["relative_error", "absolute_error"]
        if self.float_comparison_mode not in valid_comparison_modes:
            raise ValueError(
                f"Invalid float_comparison_mode: {self.float_comparison_mode}. "
                f"Must be one of {valid_comparison_modes}"
            )

        valid_null_handling = ["strict", "lenient"]
        if self.null_handling not in valid_null_handling:
            raise ValueError(
                f"Invalid null_handling: {self.null_handling}. "
                f"Must be one of {valid_null_handling}"
            )

        valid_string_normalization = ["trim", "lower", "none"]
        if self.string_normalization not in valid_string_normalization:
            raise ValueError(
                f"Invalid string_normalization: {self.string_normalization}. "
                f"Must be one of {valid_string_normalization}"
            )

        if self.datetime_tolerance_ms < 0:
            raise ValueError("datetime_tolerance_ms must be non-negative")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "row_order_matters": self.row_order_matters,
            "column_order_matters": self.column_order_matters,
            "float_tolerance": self.float_tolerance,
            "float_comparison_mode": self.float_comparison_mode,
            "null_handling": self.null_handling,
            "string_normalization": self.string_normalization,
            "string_case_sensitive": self.string_case_sensitive,
            "datetime_normalize_timezone": self.datetime_normalize_timezone,
            "datetime_tolerance_ms": self.datetime_tolerance_ms,
        }


@dataclass
class Question:
    """Test question definition."""

    id: str
    version: str
    domain: str
    complexity: ComplexityLevel
    question_text: Dict[str, str]  # {"en": "...", "zh": "..."}
    golden_sql: str
    dependencies: Dict[str, List[str]]  # {"tables": [...], "features": [...]}
    comparison_rules: Optional[ComparisonRules] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_question(self, language: str = "zh") -> str:
        """Get question text in specified language."""
        return self.question_text.get(language, self.question_text.get("en", ""))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "version": self.version,
            "domain": self.domain,
            "complexity": self.complexity.value,
            "question": self.question_text,
            "golden_sql": self.golden_sql,
            "dependencies": self.dependencies,
            "comparison_rules": (
                self.comparison_rules.to_dict() if self.comparison_rules else None
            ),
            "tags": self.tags,
            "metadata": self.metadata,
        }


# ============================================================================
# SUT (System Under Test) Types
# ============================================================================


@dataclass
class TokenUsage:
    """Token consumption information."""

    input_tokens: int
    output_tokens: int
    total_tokens: int

    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary."""
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
        }


@dataclass
class TimingBreakdown:
    """Detailed timing breakdown."""

    nl2sql_time_ms: Optional[float] = None
    sql_generation_time_ms: Optional[float] = None
    sql_execution_time_ms: Optional[float] = None
    total_time_ms: Optional[float] = None

    def to_dict(self) -> Dict[str, Optional[float]]:
        """Convert to dictionary."""
        return {
            "nl2sql_time_ms": self.nl2sql_time_ms,
            "sql_generation_time_ms": self.sql_generation_time_ms,
            "sql_execution_time_ms": self.sql_execution_time_ms,
            "total_time_ms": self.total_time_ms,
        }


@dataclass
class NL2SQLResponse:
    """Response from SUT (System Under Test)."""

    generated_sql: str
    result_dataframe: Optional[pd.DataFrame] = None
    success: bool = True
    error: Optional[str] = None

    # Performance metrics
    total_time_ms: float = 0.0
    ttfb_ms: Optional[float] = None  # Time To First Byte
    timing_breakdown: Optional[TimingBreakdown] = None
    timing_source: str = "client"  # "client" or "vendor"

    # Cost metrics
    token_usage: Optional[TokenUsage] = None
    token_available: bool = False

    # Additional metadata
    confidence: Optional[float] = None
    model_version: Optional[str] = None
    streaming_chunks: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "generated_sql": self.generated_sql,
            "result_rows": len(self.result_dataframe) if self.result_dataframe is not None else 0,
            "success": self.success,
            "error": self.error,
            "total_time_ms": self.total_time_ms,
            "ttfb_ms": self.ttfb_ms,
            "timing_breakdown": (
                self.timing_breakdown.to_dict() if self.timing_breakdown else None
            ),
            "timing_source": self.timing_source,
            "token_usage": self.token_usage.to_dict() if self.token_usage else None,
            "token_available": self.token_available,
            "confidence": self.confidence,
            "model_version": self.model_version,
        }


# ============================================================================
# Evaluation Results
# ============================================================================


@dataclass
class ComparisonResult:
    """Result of comparing two result sets."""

    match: bool
    reason: str
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "match": self.match,
            "reason": self.reason,
            "details": self.details or {},
        }


@dataclass
class PerformanceMetrics:
    """Performance profiling metrics."""

    median_time_ms: float
    mean_time_ms: float
    p50: float
    p95: float
    p99: float
    min_time_ms: float
    max_time_ms: float
    std_dev: float
    measurements: List[float] = field(default_factory=list)

    # Detailed breakdown (optional)
    nl2sql_time_ms: Optional[float] = None
    sql_generation_time_ms: Optional[float] = None
    sql_execution_time_ms: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "median_time_ms": self.median_time_ms,
            "mean_time_ms": self.mean_time_ms,
            "p50": self.p50,
            "p95": self.p95,
            "p99": self.p99,
            "min_time_ms": self.min_time_ms,
            "max_time_ms": self.max_time_ms,
            "std_dev": self.std_dev,
            "measurements": self.measurements,
            "nl2sql_time_ms": self.nl2sql_time_ms,
            "sql_generation_time_ms": self.sql_generation_time_ms,
            "sql_execution_time_ms": self.sql_execution_time_ms,
        }


@dataclass
class QuestionResult:
    """Result for a single question."""

    question: Question
    sut_response: NL2SQLResponse
    comparison_result: ComparisonResult
    performance_metrics: Optional[PerformanceMetrics] = None
    status: TestStatus = TestStatus.PENDING
    execution_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "question_id": self.question.id,
            "question_text": self.question.get_question(),
            "complexity": self.question.complexity.value,
            "status": self.status.value,
            "correct": self.comparison_result.match,
            "generated_sql": self.sut_response.generated_sql,
            "golden_sql": self.question.golden_sql,
            "comparison_result": self.comparison_result.to_dict(),
            "sut_response": self.sut_response.to_dict(),
            "performance_metrics": (
                self.performance_metrics.to_dict() if self.performance_metrics else None
            ),
            "execution_time": (
                self.execution_time.isoformat() if self.execution_time else None
            ),
        }


@dataclass
class TestReport:
    """Complete test report."""

    sut_name: str
    test_id: str
    domain: str
    quality: QualityLevel
    database_type: DatabaseType

    # Results
    question_results: List[QuestionResult]

    # Summary metrics
    total_questions: int
    correct_count: int
    accuracy: float

    # Timing
    start_time: datetime
    end_time: Optional[datetime] = None
    total_duration_seconds: Optional[float] = None

    # Additional metrics (calculated)
    avg_response_time_ms: Optional[float] = None
    p95_response_time_ms: Optional[float] = None
    total_tokens: Optional[int] = None
    avg_cost_per_query: Optional[float] = None

    # Metadata
    framework_version: str = "0.1.0"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "sut_name": self.sut_name,
            "test_id": self.test_id,
            "domain": self.domain,
            "quality": self.quality.value,
            "database_type": self.database_type.value,
            "total_questions": self.total_questions,
            "correct_count": self.correct_count,
            "accuracy": self.accuracy,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_duration_seconds": self.total_duration_seconds,
            "avg_response_time_ms": self.avg_response_time_ms,
            "p95_response_time_ms": self.p95_response_time_ms,
            "total_tokens": self.total_tokens,
            "avg_cost_per_query": self.avg_cost_per_query,
            "framework_version": self.framework_version,
            "metadata": self.metadata,
            "question_results": [qr.to_dict() for qr in self.question_results],
        }


# ============================================================================
# Configuration Types
# ============================================================================


@dataclass
class DatabaseConfig:
    """Database connection configuration."""

    type: DatabaseType
    host: str
    port: int
    user: str
    password: str
    database: str
    ssl: bool = False
    connection_params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (without sensitive data)."""
        return {
            "type": self.type.value,
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "database": self.database,
            "ssl": self.ssl,
        }


@dataclass
class SUTConfig:
    """SUT (System Under Test) configuration."""

    name: str
    type: str  # "rest_api", "python_sdk", "http_generic"
    version: str = "1.0.0"
    config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "type": self.type,
            "version": self.version,
            "config": self.config,
        }
