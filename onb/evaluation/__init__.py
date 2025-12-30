"""
Evaluation module for OpenNL2Data-Bench.

This module provides result comparison, performance profiling, cost tracking,
robustness testing, and comprehensive evaluation capabilities.
"""

from onb.evaluation.comparator import ResultComparator, compare_results
from onb.evaluation.cost import (
    CostCalculator,
    CostSample,
    CostTracker,
    LLMProvider,
    ModelPricing,
    calculate_batch_cost,
)
from onb.evaluation.performance import (
    ConcurrentPerformanceTester,
    PerformanceProfiler,
    PerformanceSample,
    ThroughputMeter,
    measure_execution_time,
)
from onb.evaluation.robustness import (
    DataQualityTester,
    EdgeCaseTester,
    ErrorHandlingTester,
    RobustnessEvaluator,
    RobustnessTestCase,
    RobustnessTestResult,
    RobustnessTestType,
)

__all__ = [
    "ResultComparator",
    "compare_results",
    "PerformanceSample",
    "PerformanceProfiler",
    "ThroughputMeter",
    "ConcurrentPerformanceTester",
    "measure_execution_time",
    "CostSample",
    "CostCalculator",
    "CostTracker",
    "LLMProvider",
    "ModelPricing",
    "calculate_batch_cost",
    "RobustnessTestCase",
    "RobustnessTestResult",
    "RobustnessTestType",
    "EdgeCaseTester",
    "ErrorHandlingTester",
    "DataQualityTester",
    "RobustnessEvaluator",
]
