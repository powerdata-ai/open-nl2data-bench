"""
Mock SUT adapter for testing and development.

This adapter simulates a NL2SQL system for testing purposes.
"""

import time
from typing import Any, Dict, Optional

import pandas as pd

from onb.adapters.sut.base import SUTAdapter
from onb.core.exceptions import SUTAdapterError
from onb.core.types import (
    NL2SQLResponse,
    SchemaInfo,
    SUTConfig,
    TimingBreakdown,
    TokenUsage,
)


class MockSUTAdapter(SUTAdapter):
    """Mock SUT adapter for testing."""

    def __init__(
        self,
        config: Optional[SUTConfig] = None,
        auto_generate_sql: bool = True,
        simulate_delay_ms: int = 100,
        fail_on_keywords: Optional[list] = None,
    ):
        """
        Initialize mock SUT adapter.

        Args:
            config: SUT configuration (uses default if None)
            auto_generate_sql: Whether to auto-generate simple SQL
            simulate_delay_ms: Simulated processing delay in milliseconds
            fail_on_keywords: List of keywords that trigger failures
        """
        if config is None:
            config = SUTConfig(
                name="MockSUT",
                type="mock",
                version="1.0.0",
                config={},
            )

        super().__init__(config)
        self.auto_generate_sql = auto_generate_sql
        self.simulate_delay_ms = simulate_delay_ms
        self.fail_on_keywords = fail_on_keywords or []
        self._query_count = 0

    def initialize(self) -> None:
        """Initialize the mock adapter."""
        self._initialized = True
        self._query_count = 0

    def query(
        self,
        question: str,
        schema: SchemaInfo,
        language: str = "zh",
        **kwargs: Any,
    ) -> NL2SQLResponse:
        """
        Execute mock NL2SQL query.

        Args:
            question: Natural language question
            schema: Database schema information
            language: Question language
            **kwargs: Additional parameters

        Returns:
            NL2SQLResponse with mock data
        """
        if not self._initialized:
            raise SUTAdapterError("Adapter not initialized")

        start_time = time.time()

        # Increment query count
        self._query_count += 1

        # Check for failure keywords
        for keyword in self.fail_on_keywords:
            if keyword.lower() in question.lower():
                return NL2SQLResponse(
                    generated_sql="",
                    success=False,
                    error=f"Mock failure triggered by keyword: {keyword}",
                    total_time_ms=10.0,
                )

        # Simulate processing delay
        if self.simulate_delay_ms > 0:
            time.sleep(self.simulate_delay_ms / 1000.0)

        # Generate mock SQL
        if self.auto_generate_sql:
            sql = self._generate_mock_sql(question, schema)
        else:
            sql = kwargs.get("expected_sql", "SELECT 1")

        # Generate mock result data
        result_df = self._generate_mock_result(question, schema)

        # Calculate timing
        end_time = time.time()
        total_time = (end_time - start_time) * 1000  # Convert to ms

        # Generate mock token usage
        token_usage = TokenUsage(
            input_tokens=len(question.split()) * 2,  # Rough approximation
            output_tokens=len(sql.split()) * 2,
            total_tokens=(len(question.split()) + len(sql.split())) * 2,
        )

        # Generate timing breakdown
        timing_breakdown = TimingBreakdown(
            nl2sql_time_ms=total_time * 0.6,
            sql_generation_time_ms=total_time * 0.3,
            sql_execution_time_ms=total_time * 0.1,
            total_time_ms=total_time,
        )

        return NL2SQLResponse(
            generated_sql=sql,
            result_dataframe=result_df,
            success=True,
            total_time_ms=total_time,
            timing_breakdown=timing_breakdown,
            timing_source="vendor",
            token_usage=token_usage,
            token_available=True,
            confidence=0.95,
            model_version="mock-v1.0",
        )

    def _generate_mock_sql(self, question: str, schema: SchemaInfo) -> str:
        """Generate simple mock SQL based on question."""
        # Extract table name from schema
        if schema.tables:
            table_name = schema.tables[0].name
        else:
            table_name = "mock_table"

        # Simple keyword-based SQL generation
        # Check more specific keywords first to avoid false matches
        question_lower = question.lower()

        # Average keywords (check before count to avoid "平均值是多少" matching count)
        if "average" in question_lower or "avg" in question_lower or "平均值" in question_lower or "平均" in question_lower:
            return f"SELECT AVG(value) FROM {table_name}"

        # Sum keywords (check before count)
        if "sum" in question_lower or "total" in question_lower or "总和" in question_lower or ("总" in question_lower and "和" in question_lower):
            return f"SELECT SUM(value) FROM {table_name}"

        # Max keywords (check before count)
        if "max" in question_lower or "maximum" in question_lower or "最大值" in question_lower or "最大" in question_lower:
            return f"SELECT MAX(value) FROM {table_name}"

        # Min keywords (check before count)
        if "min" in question_lower or "minimum" in question_lower or "最小值" in question_lower or "最小" in question_lower:
            return f"SELECT MIN(value) FROM {table_name}"

        # Count keywords (checked last as it's more general)
        if "count" in question_lower or "多少" in question_lower or "how many" in question_lower:
            return f"SELECT COUNT(*) FROM {table_name}"

        # Default: simple SELECT
        return f"SELECT * FROM {table_name} LIMIT 10"

    def _generate_mock_result(
        self, question: str, schema: SchemaInfo
    ) -> pd.DataFrame:
        """Generate mock result DataFrame."""
        # Simple mock data - check more specific keywords first
        question_lower = question.lower()

        # Average keywords
        if "average" in question_lower or "avg" in question_lower or "平均值" in question_lower or "平均" in question_lower:
            return pd.DataFrame({"avg": [123.45]})

        # Sum keywords
        if "sum" in question_lower or "total" in question_lower or "总和" in question_lower or ("总" in question_lower and "和" in question_lower):
            return pd.DataFrame({"sum": [1000]})

        # Max keywords
        if "max" in question_lower or "最大值" in question_lower or "最大" in question_lower:
            return pd.DataFrame({"max": [999]})

        # Min keywords
        if "min" in question_lower or "最小值" in question_lower or "最小" in question_lower:
            return pd.DataFrame({"min": [1]})

        # Count keywords (checked last)
        if "count" in question_lower or "多少" in question_lower:
            return pd.DataFrame({"count": [42]})

        # Default: mock table data
        return pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "value": [100, 200, 300],
        })

    def cleanup(self) -> None:
        """Clean up mock adapter resources."""
        self._initialized = False
        self._query_count = 0

    def get_metadata(self) -> Dict[str, Any]:
        """Get mock adapter metadata."""
        metadata = super().get_metadata()
        metadata.update({
            "query_count": self._query_count,
            "auto_generate_sql": self.auto_generate_sql,
            "simulate_delay_ms": self.simulate_delay_ms,
        })
        return metadata
