"""
Test runner for OpenNL2SQL-Bench.

This module orchestrates the execution of benchmark tests.
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional

from onb.adapters.database.base import DatabaseAdapter
from onb.adapters.sut.base import SUTAdapter
from onb.core.types import (
    ComparisonResult,
    DatabaseType,
    PerformanceMetrics,
    Question,
    QuestionResult,
    QualityLevel,
    TestReport,
    TestStatus,
)
from onb.evaluation.comparator import ResultComparator


class TestRunner:
    """Orchestrates benchmark test execution."""

    def __init__(
        self,
        database_adapter: DatabaseAdapter,
        sut_adapter: SUTAdapter,
    ):
        """
        Initialize test runner.

        Args:
            database_adapter: Database adapter for executing golden SQL
            sut_adapter: SUT adapter for NL2SQL queries
        """
        self.database_adapter = database_adapter
        self.sut_adapter = sut_adapter
        self.comparator = ResultComparator()

    def run_question(
        self,
        question: Question,
        language: str = "zh",
    ) -> QuestionResult:
        """
        Execute a single test question.

        Args:
            question: Test question to execute
            language: Question language

        Returns:
            QuestionResult with test outcome
        """
        # Get schema info
        schema = self.database_adapter.get_schema_info()

        # Execute SUT query
        sut_response = self.sut_adapter.query(
            question.get_question(language),
            schema,
            language=language,
        )

        # Execute golden SQL for expected results
        expected_df = self.database_adapter.execute_query(question.golden_sql)

        # Compare results
        comparison_rules = question.comparison_rules or self.comparator.rules
        comparator = ResultComparator(comparison_rules)

        if sut_response.success and sut_response.result_dataframe is not None:
            comparison = comparator.compare(expected_df, sut_response.result_dataframe)
            status = TestStatus.PASSED if comparison.match else TestStatus.FAILED
        else:
            comparison = ComparisonResult(
                match=False,
                reason=f"SUT query failed: {sut_response.error}",
            )
            status = TestStatus.ERROR

        return QuestionResult(
            question=question,
            sut_response=sut_response,
            comparison_result=comparison,
            status=status,
            execution_time=datetime.now(),
        )

    def run_test_suite(
        self,
        questions: List[Question],
        language: str = "zh",
    ) -> TestReport:
        """
        Run a complete test suite.

        Args:
            questions: List of questions to test
            language: Question language

        Returns:
            TestReport with aggregated results
        """
        start_time = datetime.now()
        results = []

        for question in questions:
            result = self.run_question(question, language)
            results.append(result)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Calculate statistics
        correct_count = sum(1 for r in results if r.status == TestStatus.PASSED)
        accuracy = correct_count / len(results) if results else 0.0

        return TestReport(
            sut_name=self.sut_adapter.name,
            test_id=f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            domain=questions[0].domain if questions else "unknown",
            quality=QualityLevel.HIGH,
            database_type=self.database_adapter.database_type,
            question_results=results,
            total_questions=len(results),
            correct_count=correct_count,
            accuracy=accuracy,
            start_time=start_time,
            end_time=end_time,
            total_duration_seconds=duration,
        )
