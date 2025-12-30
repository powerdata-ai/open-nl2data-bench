"""Unit tests for chart generation module."""
import pytest

from onb.reporting.charts import ChartData, ChartGenerator, ChartType


class TestChartType:
    """Test ChartType enum."""

    def test_enum_values(self):
        """Test all chart types."""
        assert ChartType.LINE == "line"
        assert ChartType.BAR == "bar"
        assert ChartType.RADAR == "radar"
        assert ChartType.PIE == "pie"
        assert ChartType.DOUGHNUT == "doughnut"


class TestChartData:
    """Test ChartData dataclass."""

    def test_initialization_minimal(self):
        """Test minimal initialization."""
        data = ChartData(
            chart_id="test_chart",
            chart_type=ChartType.LINE,
            title="Test Chart",
            labels=["A", "B", "C"],
            datasets=[{"label": "Data", "data": [1, 2, 3]}],
        )

        assert data.chart_id == "test_chart"
        assert data.chart_type == ChartType.LINE
        assert data.title == "Test Chart"
        assert data.labels == ["A", "B", "C"]
        assert len(data.datasets) == 1
        assert data.options is None

    def test_initialization_with_options(self):
        """Test initialization with options."""
        options = {"responsive": True, "plugins": {"legend": {"display": True}}}

        data = ChartData(
            chart_id="chart_with_options",
            chart_type=ChartType.BAR,
            title="Bar Chart",
            labels=["X", "Y"],
            datasets=[{"label": "Values", "data": [10, 20]}],
            options=options,
        )

        assert data.options == options
        assert data.options["responsive"] is True


class TestChartGenerator:
    """Test ChartGenerator class."""

    def test_initialization(self):
        """Test generator initialization."""
        generator = ChartGenerator()

        assert generator.charts == []
        assert len(ChartGenerator.COLORS) == 8
        assert len(ChartGenerator.BORDER_COLORS) == 8

    def test_add_chart(self):
        """Test adding chart."""
        generator = ChartGenerator()

        chart_data = ChartData(
            chart_id="test",
            chart_type=ChartType.LINE,
            title="Test",
            labels=["A"],
            datasets=[{"data": [1]}],
        )

        generator.add_chart(chart_data)

        assert len(generator.charts) == 1
        assert generator.charts[0] == chart_data

    def test_generate_accuracy_trend_chart(self):
        """Test generating accuracy trend chart."""
        generator = ChartGenerator()

        labels = ["Run 1", "Run 2", "Run 3", "Run 4"]
        values = [75.0, 80.5, 82.3, 85.0]

        chart = generator.generate_accuracy_trend_chart(labels, values)

        assert chart.chart_id == "accuracyTrend"
        assert chart.chart_type == ChartType.LINE
        assert chart.title == "Accuracy Trend"
        assert chart.labels == labels
        assert len(chart.datasets) == 1
        assert chart.datasets[0]["data"] == values
        assert chart.datasets[0]["label"] == "Accuracy Rate"
        assert chart.options is not None
        assert len(generator.charts) == 1

    def test_generate_accuracy_trend_chart_custom_id(self):
        """Test accuracy trend chart with custom ID."""
        generator = ChartGenerator()

        chart = generator.generate_accuracy_trend_chart(
            labels=["A", "B"],
            accuracy_values=[70.0, 75.0],
            chart_id="customAccuracy",
        )

        assert chart.chart_id == "customAccuracy"

    def test_generate_performance_comparison_chart(self):
        """Test generating performance comparison chart."""
        generator = ChartGenerator()

        systems = ["System A", "System B", "System C"]
        p50 = [1000, 1200, 900]
        p95 = [2000, 2500, 1800]
        p99 = [3000, 3500, 2500]

        chart = generator.generate_performance_comparison_chart(
            systems, p50, p95, p99
        )

        assert chart.chart_id == "performanceComparison"
        assert chart.chart_type == ChartType.BAR
        assert chart.title == "Performance Comparison"
        assert chart.labels == systems
        assert len(chart.datasets) == 3
        assert chart.datasets[0]["label"] == "P50 Latency"
        assert chart.datasets[0]["data"] == p50
        assert chart.datasets[1]["label"] == "P95 Latency"
        assert chart.datasets[1]["data"] == p95
        assert chart.datasets[2]["label"] == "P99 Latency"
        assert chart.datasets[2]["data"] == p99

    def test_generate_cost_distribution_chart(self):
        """Test generating cost distribution pie chart."""
        generator = ChartGenerator()

        models = ["GPT-4", "Claude-3", "Gemini"]
        costs = [0.45, 0.32, 0.18]

        chart = generator.generate_cost_distribution_chart(models, costs)

        assert chart.chart_id == "costDistribution"
        assert chart.chart_type == ChartType.PIE
        assert chart.title == "Cost Distribution by Model"
        assert chart.labels == models
        assert len(chart.datasets) == 1
        assert chart.datasets[0]["data"] == costs
        assert len(chart.datasets[0]["backgroundColor"]) == 3

    def test_generate_six_dimension_radar_chart(self):
        """Test generating six-dimension radar chart."""
        generator = ChartGenerator()

        scores = {
            "Accuracy": 85.0,
            "Performance": 90.0,
            "Cost": 75.0,
            "Robustness": 80.0,
            "UX": 88.0,
            "Concurrency": 92.0,
        }

        chart = generator.generate_six_dimension_radar_chart(scores)

        assert chart.chart_id == "sixDimensionRadar"
        assert chart.chart_type == ChartType.RADAR
        assert chart.title == "Six-Dimensional Evaluation"
        assert chart.labels == list(scores.keys())
        assert len(chart.datasets) == 1
        assert chart.datasets[0]["data"] == list(scores.values())
        assert chart.options["scales"]["r"]["max"] == 100

    def test_generate_token_usage_chart(self):
        """Test generating token usage stacked bar chart."""
        generator = ChartGenerator()

        labels = ["Query 1", "Query 2", "Query 3"]
        input_tokens = [1000, 1200, 950]
        output_tokens = [500, 600, 450]

        chart = generator.generate_token_usage_chart(
            labels, input_tokens, output_tokens
        )

        assert chart.chart_id == "tokenUsage"
        assert chart.chart_type == ChartType.BAR
        assert chart.title == "Token Usage"
        assert chart.labels == labels
        assert len(chart.datasets) == 2
        assert chart.datasets[0]["label"] == "Input Tokens"
        assert chart.datasets[0]["data"] == input_tokens
        assert chart.datasets[1]["label"] == "Output Tokens"
        assert chart.datasets[1]["data"] == output_tokens
        assert chart.options["scales"]["x"]["stacked"] is True
        assert chart.options["scales"]["y"]["stacked"] is True

    def test_generate_chart_html(self):
        """Test generating HTML for a chart."""
        generator = ChartGenerator()

        chart_data = ChartData(
            chart_id="testChart",
            chart_type=ChartType.LINE,
            title="Test",
            labels=["A"],
            datasets=[{"data": [1]}],
        )

        html = generator.generate_chart_html(chart_data)

        assert 'id="testChart"' in html
        assert "<canvas" in html
        assert "</canvas>" in html
        assert "chart-container" in html

    def test_generate_chart_script(self):
        """Test generating JavaScript for a chart."""
        generator = ChartGenerator()

        chart_data = ChartData(
            chart_id="scriptTest",
            chart_type=ChartType.BAR,
            title="Test",
            labels=["X", "Y"],
            datasets=[{"label": "Data", "data": [10, 20]}],
            options={"responsive": True},
        )

        script = generator.generate_chart_script(chart_data)

        assert "new Chart(" in script
        assert 'document.getElementById(\'scriptTest\')' in script
        assert "type: 'bar'" in script
        assert '"responsive": true' in script
        assert '["X", "Y"]' in script

    def test_generate_all_charts_html(self):
        """Test generating HTML for all charts."""
        generator = ChartGenerator()

        # Add multiple charts
        generator.generate_accuracy_trend_chart(
            labels=["A", "B"], accuracy_values=[70, 80]
        )
        generator.generate_cost_distribution_chart(
            model_names=["Model A"], costs=[0.5]
        )

        html = generator.generate_all_charts_html()

        assert 'id="accuracyTrend"' in html
        assert 'id="costDistribution"' in html
        assert html.count("<canvas") == 2

    def test_generate_all_charts_script(self):
        """Test generating JavaScript for all charts."""
        generator = ChartGenerator()

        # Add charts
        generator.generate_accuracy_trend_chart(
            labels=["A"], accuracy_values=[75]
        )
        generator.generate_performance_comparison_chart(
            system_names=["Sys1"], p50_values=[1000], p95_values=[2000], p99_values=[3000]
        )

        script = generator.generate_all_charts_script()

        assert "<script" in script
        assert "</script>" in script
        assert "chart.js" in script
        assert "DOMContentLoaded" in script
        assert "new Chart(" in script
        assert script.count("new Chart(") == 2

    def test_reset(self):
        """Test resetting generator."""
        generator = ChartGenerator()

        # Add some charts
        generator.generate_accuracy_trend_chart(
            labels=["A"], accuracy_values=[80]
        )
        generator.generate_cost_distribution_chart(
            model_names=["M1"], costs=[0.3]
        )

        assert len(generator.charts) == 2

        generator.reset()

        assert len(generator.charts) == 0

    def test_multiple_datasets_colors(self):
        """Test that multiple datasets get different colors."""
        generator = ChartGenerator()

        chart = generator.generate_performance_comparison_chart(
            system_names=["A"],
            p50_values=[100],
            p95_values=[200],
            p99_values=[300],
        )

        # Should have 3 different colors
        colors = [ds["backgroundColor"] for ds in chart.datasets]
        assert len(set(colors)) == 3
        assert colors[0] == ChartGenerator.COLORS[0]
        assert colors[1] == ChartGenerator.COLORS[1]
        assert colors[2] == ChartGenerator.COLORS[2]

    def test_chart_options_structure(self):
        """Test that chart options have proper structure."""
        generator = ChartGenerator()

        chart = generator.generate_accuracy_trend_chart(
            labels=["A"], accuracy_values=[85]
        )

        assert "responsive" in chart.options
        assert "plugins" in chart.options
        assert "scales" in chart.options
        assert "y" in chart.options["scales"]
        assert chart.options["scales"]["y"]["max"] == 100

    def test_empty_data_handling(self):
        """Test handling empty data."""
        generator = ChartGenerator()

        chart = generator.generate_accuracy_trend_chart(
            labels=[], accuracy_values=[]
        )

        assert chart.labels == []
        assert chart.datasets[0]["data"] == []

    def test_single_data_point(self):
        """Test chart with single data point."""
        generator = ChartGenerator()

        chart = generator.generate_performance_comparison_chart(
            system_names=["Only One"],
            p50_values=[1500],
            p95_values=[2500],
            p99_values=[3000],
        )

        assert len(chart.labels) == 1
        assert chart.labels[0] == "Only One"
        assert all(len(ds["data"]) == 1 for ds in chart.datasets)

    def test_large_dataset(self):
        """Test chart with large dataset."""
        generator = ChartGenerator()

        labels = [f"Run {i}" for i in range(100)]
        values = [70.0 + (i * 0.2) for i in range(100)]

        chart = generator.generate_accuracy_trend_chart(labels, values)

        assert len(chart.labels) == 100
        assert len(chart.datasets[0]["data"]) == 100
