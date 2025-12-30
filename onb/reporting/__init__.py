"""
Reporting module for OpenNL2Data-Bench.

This module provides report generation capabilities including HTML reports,
visualizations, and result comparisons.
"""

from onb.reporting.charts import ChartData, ChartGenerator, ChartType
from onb.reporting.comparison import (
    ComparisonResult,
    ResultComparator,
    ResultStore,
    TestRunResult,
)
from onb.reporting.html_generator import (
    CertificationLevel,
    HTMLReportGenerator,
    ReportData,
)

__all__ = [
    "HTMLReportGenerator",
    "ReportData",
    "CertificationLevel",
    "ChartGenerator",
    "ChartData",
    "ChartType",
    "TestRunResult",
    "ComparisonResult",
    "ResultStore",
    "ResultComparator",
]
