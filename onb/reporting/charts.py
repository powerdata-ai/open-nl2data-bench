"""
Chart generation module for OpenNL2Data-Bench.

This module generates interactive charts using Chart.js for benchmark reports.
Supports: line charts, bar charts, radar charts, pie charts.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class ChartType(str, Enum):
    """Supported chart types."""

    LINE = "line"
    BAR = "bar"
    RADAR = "radar"
    PIE = "pie"
    DOUGHNUT = "doughnut"


@dataclass
class ChartData:
    """Data for a single chart."""

    chart_id: str
    chart_type: ChartType
    title: str
    labels: List[str]
    datasets: List[Dict[str, Any]]
    options: Optional[Dict[str, Any]] = None


class ChartGenerator:
    """
    Generate interactive charts using Chart.js.

    Features:
    - Multiple chart types
    - Customizable colors and styling
    - Responsive design
    - Animation support
    """

    # Default color palette
    COLORS = [
        "rgba(102, 126, 234, 0.8)",  # Purple
        "rgba(118, 75, 162, 0.8)",   # Dark purple
        "rgba(237, 100, 166, 0.8)",  # Pink
        "rgba(255, 159, 64, 0.8)",   # Orange
        "rgba(75, 192, 192, 0.8)",   # Teal
        "rgba(54, 162, 235, 0.8)",   # Blue
        "rgba(153, 102, 255, 0.8)",  # Light purple
        "rgba(255, 99, 132, 0.8)",   # Red
    ]

    BORDER_COLORS = [
        "rgb(102, 126, 234)",
        "rgb(118, 75, 162)",
        "rgb(237, 100, 166)",
        "rgb(255, 159, 64)",
        "rgb(75, 192, 192)",
        "rgb(54, 162, 235)",
        "rgb(153, 102, 255)",
        "rgb(255, 99, 132)",
    ]

    def __init__(self):
        """Initialize chart generator."""
        self.charts: List[ChartData] = []

    def add_chart(self, chart_data: ChartData) -> None:
        """
        Add a chart to the generator.

        Args:
            chart_data: Chart data
        """
        self.charts.append(chart_data)

    def generate_accuracy_trend_chart(
        self,
        labels: List[str],
        accuracy_values: List[float],
        chart_id: str = "accuracyTrend",
    ) -> ChartData:
        """
        Generate accuracy trend line chart.

        Args:
            labels: X-axis labels (e.g., test dates or run numbers)
            accuracy_values: Accuracy percentages (0-100)
            chart_id: HTML element ID

        Returns:
            Chart data
        """
        dataset = {
            "label": "Accuracy Rate",
            "data": accuracy_values,
            "borderColor": self.BORDER_COLORS[0],
            "backgroundColor": self.COLORS[0],
            "tension": 0.4,
            "fill": True,
        }

        options = {
            "responsive": True,
            "plugins": {
                "legend": {"display": True, "position": "top"},
                "title": {"display": False},
            },
            "scales": {
                "y": {
                    "beginAtZero": True,
                    "max": 100,
                    "ticks": {"callback": "function(value) { return value + '%'; }"},
                }
            },
        }

        chart = ChartData(
            chart_id=chart_id,
            chart_type=ChartType.LINE,
            title="Accuracy Trend",
            labels=labels,
            datasets=[dataset],
            options=options,
        )

        self.add_chart(chart)
        return chart

    def generate_performance_comparison_chart(
        self,
        system_names: List[str],
        p50_values: List[float],
        p95_values: List[float],
        p99_values: List[float],
        chart_id: str = "performanceComparison",
    ) -> ChartData:
        """
        Generate performance comparison bar chart.

        Args:
            system_names: Names of systems being compared
            p50_values: P50 latencies in milliseconds
            p95_values: P95 latencies
            p99_values: P99 latencies
            chart_id: HTML element ID

        Returns:
            Chart data
        """
        datasets = [
            {
                "label": "P50 Latency",
                "data": p50_values,
                "backgroundColor": self.COLORS[0],
                "borderColor": self.BORDER_COLORS[0],
                "borderWidth": 1,
            },
            {
                "label": "P95 Latency",
                "data": p95_values,
                "backgroundColor": self.COLORS[1],
                "borderColor": self.BORDER_COLORS[1],
                "borderWidth": 1,
            },
            {
                "label": "P99 Latency",
                "data": p99_values,
                "backgroundColor": self.COLORS[2],
                "borderColor": self.BORDER_COLORS[2],
                "borderWidth": 1,
            },
        ]

        options = {
            "responsive": True,
            "plugins": {
                "legend": {"display": True, "position": "top"},
                "title": {"display": False},
            },
            "scales": {
                "y": {
                    "beginAtZero": True,
                    "ticks": {"callback": "function(value) { return value + 'ms'; }"},
                }
            },
        }

        chart = ChartData(
            chart_id=chart_id,
            chart_type=ChartType.BAR,
            title="Performance Comparison",
            labels=system_names,
            datasets=datasets,
            options=options,
        )

        self.add_chart(chart)
        return chart

    def generate_cost_distribution_chart(
        self,
        model_names: List[str],
        costs: List[float],
        chart_id: str = "costDistribution",
    ) -> ChartData:
        """
        Generate cost distribution pie chart.

        Args:
            model_names: Names of models
            costs: Costs for each model
            chart_id: HTML element ID

        Returns:
            Chart data
        """
        dataset = {
            "label": "Cost Distribution",
            "data": costs,
            "backgroundColor": self.COLORS[: len(model_names)],
            "borderColor": self.BORDER_COLORS[: len(model_names)],
            "borderWidth": 2,
        }

        options = {
            "responsive": True,
            "plugins": {
                "legend": {"display": True, "position": "right"},
                "title": {"display": False},
                "tooltip": {
                    "callbacks": {
                        "label": "function(context) { return context.label + ': $' + context.parsed.toFixed(4); }"
                    }
                },
            },
        }

        chart = ChartData(
            chart_id=chart_id,
            chart_type=ChartType.PIE,
            title="Cost Distribution by Model",
            labels=model_names,
            datasets=[dataset],
            options=options,
        )

        self.add_chart(chart)
        return chart

    def generate_six_dimension_radar_chart(
        self,
        scores: Dict[str, float],
        chart_id: str = "sixDimensionRadar",
    ) -> ChartData:
        """
        Generate six-dimension evaluation radar chart.

        Args:
            scores: Dictionary with dimension names and scores (0-100)
                   e.g., {"Accuracy": 85, "Performance": 90, ...}
            chart_id: HTML element ID

        Returns:
            Chart data
        """
        labels = list(scores.keys())
        values = list(scores.values())

        dataset = {
            "label": "Evaluation Scores",
            "data": values,
            "backgroundColor": "rgba(102, 126, 234, 0.2)",
            "borderColor": "rgb(102, 126, 234)",
            "borderWidth": 2,
            "pointBackgroundColor": "rgb(102, 126, 234)",
            "pointBorderColor": "#fff",
            "pointHoverBackgroundColor": "#fff",
            "pointHoverBorderColor": "rgb(102, 126, 234)",
        }

        options = {
            "responsive": True,
            "plugins": {
                "legend": {"display": False},
                "title": {"display": False},
            },
            "scales": {
                "r": {
                    "beginAtZero": True,
                    "max": 100,
                    "ticks": {"stepSize": 20},
                }
            },
        }

        chart = ChartData(
            chart_id=chart_id,
            chart_type=ChartType.RADAR,
            title="Six-Dimensional Evaluation",
            labels=labels,
            datasets=[dataset],
            options=options,
        )

        self.add_chart(chart)
        return chart

    def generate_token_usage_chart(
        self,
        labels: List[str],
        input_tokens: List[int],
        output_tokens: List[int],
        chart_id: str = "tokenUsage",
    ) -> ChartData:
        """
        Generate stacked bar chart for token usage.

        Args:
            labels: X-axis labels
            input_tokens: Input token counts
            output_tokens: Output token counts
            chart_id: HTML element ID

        Returns:
            Chart data
        """
        datasets = [
            {
                "label": "Input Tokens",
                "data": input_tokens,
                "backgroundColor": self.COLORS[4],
                "borderColor": self.BORDER_COLORS[4],
                "borderWidth": 1,
            },
            {
                "label": "Output Tokens",
                "data": output_tokens,
                "backgroundColor": self.COLORS[3],
                "borderColor": self.BORDER_COLORS[3],
                "borderWidth": 1,
            },
        ]

        options = {
            "responsive": True,
            "plugins": {
                "legend": {"display": True, "position": "top"},
                "title": {"display": False},
            },
            "scales": {
                "x": {"stacked": True},
                "y": {"stacked": True, "beginAtZero": True},
            },
        }

        chart = ChartData(
            chart_id=chart_id,
            chart_type=ChartType.BAR,
            title="Token Usage",
            labels=labels,
            datasets=datasets,
            options=options,
        )

        self.add_chart(chart)
        return chart

    def generate_chart_html(self, chart: ChartData) -> str:
        """
        Generate HTML for a single chart.

        Args:
            chart: Chart data

        Returns:
            HTML string with canvas and script
        """
        return f"""
<div class="chart-container" style="position: relative; height: 400px; margin: 20px 0;">
    <canvas id="{chart.chart_id}"></canvas>
</div>
"""

    def generate_chart_script(self, chart: ChartData) -> str:
        """
        Generate JavaScript for a single chart.

        Args:
            chart: Chart data

        Returns:
            JavaScript code
        """
        import json

        # Convert options callbacks to actual JS functions
        options_json = json.dumps(chart.options) if chart.options else "{}"

        # Handle callback functions (they're strings, need to be unquoted)
        options_json = options_json.replace(
            '"function(value) { return value + \'%\'; }"',
            "function(value) { return value + '%'; }",
        )
        options_json = options_json.replace(
            '"function(value) { return value + \'ms\'; }"',
            "function(value) { return value + 'ms'; }",
        )
        options_json = options_json.replace(
            '"function(context) { return context.label + \': $\' + context.parsed.toFixed(4); }"',
            "function(context) { return context.label + ': $' + context.parsed.toFixed(4); }",
        )

        datasets_json = json.dumps(chart.datasets)
        labels_json = json.dumps(chart.labels)

        return f"""
    new Chart(document.getElementById('{chart.chart_id}'), {{
        type: '{chart.chart_type.value}',
        data: {{
            labels: {labels_json},
            datasets: {datasets_json}
        }},
        options: {options_json}
    }});
"""

    def generate_all_charts_html(self) -> str:
        """
        Generate HTML for all charts.

        Returns:
            HTML string
        """
        return "\n".join(self.generate_chart_html(chart) for chart in self.charts)

    def generate_all_charts_script(self) -> str:
        """
        Generate JavaScript for all charts.

        Returns:
            JavaScript code
        """
        scripts = [self.generate_chart_script(chart) for chart in self.charts]
        return f"""
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<script>
document.addEventListener('DOMContentLoaded', function() {{
    {''.join(scripts)}
}});
</script>
"""

    def reset(self) -> None:
        """Clear all charts."""
        self.charts.clear()
