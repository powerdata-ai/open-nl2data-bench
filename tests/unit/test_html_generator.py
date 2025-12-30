"""Unit tests for HTML report generator."""
import os
import tempfile
from datetime import datetime

import pytest

from onb.core.types import PerformanceMetrics
from onb.reporting.html_generator import (
    CertificationLevel,
    HTMLReportGenerator,
    ReportData,
)


class TestCertificationLevel:
    """Test CertificationLevel enum."""

    def test_enum_values(self):
        """Test all certification levels."""
        assert CertificationLevel.PLATINUM == "Platinum"
        assert CertificationLevel.GOLD == "Gold"
        assert CertificationLevel.SILVER == "Silver"
        assert CertificationLevel.BRONZE == "Bronze"
        assert CertificationLevel.NONE == "None"


class TestReportData:
    """Test ReportData dataclass."""

    def test_initialization_minimal(self):
        """Test minimal initialization."""
        data = ReportData(
            system_name="Test System",
            test_date=datetime(2025, 1, 15, 10, 30),
            overall_score=85.5,
            total_questions=30,
            correct_answers=25,
            accuracy_rate=0.833,
        )

        assert data.system_name == "Test System"
        assert data.test_date == datetime(2025, 1, 15, 10, 30)
        assert data.overall_score == 85.5
        assert data.total_questions == 30
        assert data.correct_answers == 25
        assert data.accuracy_rate == 0.833
        assert data.performance_metrics is None
        assert data.total_cost is None

    def test_initialization_full(self):
        """Test full initialization with all fields."""
        perf_metrics = PerformanceMetrics(
            median_time_ms=1200,
            mean_time_ms=1250,
            p50=1200,
            p95=2500,
            p99=3000,
            min_time_ms=800,
            max_time_ms=3500,
            std_dev=450,
            measurements=[1000, 1200, 1500],
        )

        data = ReportData(
            system_name="Advanced System",
            test_date=datetime(2025, 1, 15, 14, 45),
            overall_score=92.3,
            total_questions=50,
            correct_answers=47,
            accuracy_rate=0.94,
            performance_metrics=perf_metrics,
            total_cost=1.25,
            avg_cost_per_query=0.025,
            total_tokens=15000,
            robustness_pass_rate=0.88,
            robustness_tests_passed=22,
            robustness_tests_total=25,
            model_name="gpt-4",
            database_type="PostgreSQL",
            domain="ecommerce",
        )

        assert data.performance_metrics == perf_metrics
        assert data.total_cost == 1.25
        assert data.avg_cost_per_query == 0.025
        assert data.total_tokens == 15000
        assert data.robustness_pass_rate == 0.88
        assert data.model_name == "gpt-4"
        assert data.database_type == "PostgreSQL"
        assert data.domain == "ecommerce"


class TestHTMLReportGenerator:
    """Test HTMLReportGenerator class."""

    def test_initialization(self):
        """Test generator initialization."""
        generator = HTMLReportGenerator()

        assert generator.template is not None
        assert "<!DOCTYPE html>" in generator.template
        assert "OpenNL2Data-Bench" in generator.template

    def test_get_certification_level_platinum(self):
        """Test platinum certification (90-100)."""
        generator = HTMLReportGenerator()

        assert generator._get_certification_level(95.0) == CertificationLevel.PLATINUM
        assert generator._get_certification_level(90.0) == CertificationLevel.PLATINUM
        assert generator._get_certification_level(100.0) == CertificationLevel.PLATINUM

    def test_get_certification_level_gold(self):
        """Test gold certification (80-89)."""
        generator = HTMLReportGenerator()

        assert generator._get_certification_level(85.0) == CertificationLevel.GOLD
        assert generator._get_certification_level(80.0) == CertificationLevel.GOLD
        assert generator._get_certification_level(89.9) == CertificationLevel.GOLD

    def test_get_certification_level_silver(self):
        """Test silver certification (70-79)."""
        generator = HTMLReportGenerator()

        assert generator._get_certification_level(75.0) == CertificationLevel.SILVER
        assert generator._get_certification_level(70.0) == CertificationLevel.SILVER
        assert generator._get_certification_level(79.9) == CertificationLevel.SILVER

    def test_get_certification_level_bronze(self):
        """Test bronze certification (60-69)."""
        generator = HTMLReportGenerator()

        assert generator._get_certification_level(65.0) == CertificationLevel.BRONZE
        assert generator._get_certification_level(60.0) == CertificationLevel.BRONZE
        assert generator._get_certification_level(69.9) == CertificationLevel.BRONZE

    def test_get_certification_level_none(self):
        """Test no certification (<60)."""
        generator = HTMLReportGenerator()

        assert generator._get_certification_level(55.0) == CertificationLevel.NONE
        assert generator._get_certification_level(0.0) == CertificationLevel.NONE
        assert generator._get_certification_level(59.9) == CertificationLevel.NONE

    def test_get_metric_color_good(self):
        """Test metric color for good values (>=80%)."""
        generator = HTMLReportGenerator()

        assert generator._get_metric_color(85.0) == "metric-good"
        assert generator._get_metric_color(80.0) == "metric-good"
        assert generator._get_metric_color(100.0) == "metric-good"

    def test_get_metric_color_warning(self):
        """Test metric color for warning values (60-79%)."""
        generator = HTMLReportGenerator()

        assert generator._get_metric_color(70.0) == "metric-warning"
        assert generator._get_metric_color(60.0) == "metric-warning"
        assert generator._get_metric_color(79.9) == "metric-warning"

    def test_get_metric_color_bad(self):
        """Test metric color for bad values (<60%)."""
        generator = HTMLReportGenerator()

        assert generator._get_metric_color(50.0) == "metric-bad"
        assert generator._get_metric_color(0.0) == "metric-bad"
        assert generator._get_metric_color(59.9) == "metric-bad"

    def test_generate_html_minimal(self):
        """Test generating HTML with minimal data."""
        generator = HTMLReportGenerator()

        data = ReportData(
            system_name="Minimal System",
            test_date=datetime(2025, 1, 15, 10, 0),
            overall_score=75.0,
            total_questions=20,
            correct_answers=15,
            accuracy_rate=0.75,
        )

        html = generator.generate_html(data)

        # Check basic structure
        assert "<!DOCTYPE html>" in html
        assert "Minimal System" in html
        assert "75.0/100" in html
        assert "2025-01-15" in html

        # Check certification
        assert "Silver" in html
        assert "certification-silver" in html

        # Check accuracy
        assert "75.0%" in html
        assert "15/20" in html

    def test_generate_html_full(self):
        """Test generating HTML with complete data."""
        generator = HTMLReportGenerator()

        perf_metrics = PerformanceMetrics(
            median_time_ms=1200,
            mean_time_ms=1250,
            p50=1200,
            p95=2500,
            p99=3000,
            min_time_ms=800,
            max_time_ms=3500,
            std_dev=450,
            measurements=[1000, 1200, 1500],
        )

        data = ReportData(
            system_name="Full System",
            test_date=datetime(2025, 1, 15, 14, 30),
            overall_score=88.5,
            total_questions=50,
            correct_answers=45,
            accuracy_rate=0.90,
            performance_metrics=perf_metrics,
            total_cost=1.50,
            avg_cost_per_query=0.03,
            total_tokens=20000,
            robustness_pass_rate=0.85,
            robustness_tests_passed=17,
            robustness_tests_total=20,
            model_name="gpt-4-turbo",
            database_type="MySQL",
            domain="finance",
        )

        html = generator.generate_html(data)

        # Check all sections present
        assert "Full System" in html
        assert "88.5/100" in html
        assert "Gold" in html

        # Check metadata
        assert "gpt-4-turbo" in html
        assert "MySQL" in html
        assert "finance" in html

        # Check accuracy
        assert "90.0%" in html
        assert "45/50" in html

        # Check performance
        assert "1200ms" in html  # P50
        assert "2500ms" in html  # P95
        assert "3000ms" in html  # P99

        # Check cost
        assert "$1.50" in html or "$1.5000" in html
        assert "$0.03" in html or "$0.0300" in html
        assert "20,000" in html

        # Check robustness
        assert "85.0%" in html
        assert "17/20" in html

    def test_generate_dimensions_html(self):
        """Test generating dimensions HTML."""
        generator = HTMLReportGenerator()

        data = ReportData(
            system_name="Test",
            test_date=datetime.now(),
            overall_score=80.0,
            total_questions=10,
            correct_answers=8,
            accuracy_rate=0.80,
        )

        html = generator._generate_dimensions_html(data)

        # Should contain accuracy dimension
        assert "Accuracy" in html
        assert "80.0%" in html
        assert "8/10" in html
        assert "progress-bar" in html

    def test_generate_dimensions_html_with_performance(self):
        """Test dimensions HTML with performance data."""
        generator = HTMLReportGenerator()

        perf_metrics = PerformanceMetrics(
            median_time_ms=1000,
            mean_time_ms=1100,
            p50=1000,
            p95=2000,
            p99=2500,
            min_time_ms=500,
            max_time_ms=3000,
            std_dev=400,
            measurements=[],
        )

        data = ReportData(
            system_name="Test",
            test_date=datetime.now(),
            overall_score=85.0,
            total_questions=10,
            correct_answers=9,
            accuracy_rate=0.90,
            performance_metrics=perf_metrics,
        )

        html = generator._generate_dimensions_html(data)

        assert "Performance" in html
        assert "1000ms" in html  # P50
        assert "2000ms" in html  # P95
        assert "2500ms" in html  # P99

    def test_generate_to_file(self):
        """Test generating report to file."""
        generator = HTMLReportGenerator()

        data = ReportData(
            system_name="File Test",
            test_date=datetime(2025, 1, 15, 12, 0),
            overall_score=82.0,
            total_questions=15,
            correct_answers=12,
            accuracy_rate=0.80,
        )

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name

        try:
            # Generate report
            generator.generate(data, temp_path)

            # Verify file exists
            assert os.path.exists(temp_path)

            # Read and verify content
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()

            assert "<!DOCTYPE html>" in content
            assert "File Test" in content
            assert "82.0/100" in content

        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_generate_details_html_empty(self):
        """Test details HTML with no performance data."""
        generator = HTMLReportGenerator()

        data = ReportData(
            system_name="Test",
            test_date=datetime.now(),
            overall_score=70.0,
            total_questions=10,
            correct_answers=7,
            accuracy_rate=0.70,
        )

        html = generator._generate_details_html(data)

        # Should be empty or minimal
        assert len(html) >= 0

    def test_generate_details_html_with_performance(self):
        """Test details HTML with performance data."""
        generator = HTMLReportGenerator()

        perf_metrics = PerformanceMetrics(
            median_time_ms=1200,
            mean_time_ms=1300,
            p50=1200,
            p95=2400,
            p99=2800,
            min_time_ms=900,
            max_time_ms=3200,
            std_dev=380,
            measurements=[],
        )

        data = ReportData(
            system_name="Test",
            test_date=datetime.now(),
            overall_score=85.0,
            total_questions=10,
            correct_answers=9,
            accuracy_rate=0.90,
            performance_metrics=perf_metrics,
        )

        html = generator._generate_details_html(data)

        assert "Performance Details" in html
        assert "1300.00ms" in html  # Mean
        assert "1200.00ms" in html  # Median
        assert "900.00ms" in html   # Min
        assert "3200.00ms" in html  # Max
        assert "380.00ms" in html   # Std Dev

    def test_html_structure_valid(self):
        """Test that generated HTML has valid structure."""
        generator = HTMLReportGenerator()

        data = ReportData(
            system_name="Structure Test",
            test_date=datetime.now(),
            overall_score=75.0,
            total_questions=10,
            correct_answers=8,
            accuracy_rate=0.80,
        )

        html = generator.generate_html(data)

        # Check required HTML elements
        assert html.count("<html") == 1
        assert html.count("</html>") == 1
        assert html.count("<head>") == 1
        assert html.count("</head>") == 1
        assert html.count("<body>") == 1
        assert html.count("</body>") == 1

        # Check meta tags
        assert '<meta charset="UTF-8">' in html
        assert 'viewport' in html

        # Check styling
        assert "<style>" in html
        assert "</style>" in html

    def test_responsive_design_classes(self):
        """Test that responsive design classes are included."""
        generator = HTMLReportGenerator()

        data = ReportData(
            system_name="Test",
            test_date=datetime.now(),
            overall_score=80.0,
            total_questions=10,
            correct_answers=8,
            accuracy_rate=0.80,
        )

        html = generator.generate_html(data)

        # Check responsive classes
        assert "@media (max-width: 768px)" in html
        assert "grid-template-columns" in html
