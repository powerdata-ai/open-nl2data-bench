"""
HTML report generator for OpenNL2Data-Bench.

This module generates comprehensive, professional HTML reports with:
- Overall score and certification level
- Six-dimensional evaluation metrics (accuracy, performance, cost, robustness, UX, concurrency)
- Detailed breakdowns with tables and charts
- Responsive design with modern styling
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from onb.core.types import PerformanceMetrics


class CertificationLevel(str, Enum):
    """Certification levels based on overall score."""

    PLATINUM = "Platinum"  # 90-100
    GOLD = "Gold"  # 80-89
    SILVER = "Silver"  # 70-79
    BRONZE = "Bronze"  # 60-69
    NONE = "None"  # <60


@dataclass
class ReportData:
    """Data for generating benchmark report."""

    system_name: str
    test_date: datetime
    overall_score: float

    # Accuracy metrics
    total_questions: int
    correct_answers: int
    accuracy_rate: float

    # Performance metrics
    performance_metrics: Optional[PerformanceMetrics] = None

    # Cost metrics
    total_cost: Optional[float] = None
    avg_cost_per_query: Optional[float] = None
    total_tokens: Optional[int] = None

    # Robustness metrics
    robustness_pass_rate: Optional[float] = None
    robustness_tests_passed: Optional[int] = None
    robustness_tests_total: Optional[int] = None

    # Additional metadata
    model_name: Optional[str] = None
    database_type: Optional[str] = None
    domain: Optional[str] = None
    metadata: Dict[str, Any] = None


class HTMLReportGenerator:
    """
    Generate professional HTML reports for benchmark results.

    Features:
    - Responsive design
    - Six-dimensional evaluation display
    - Charts and visualizations
    - Certification badges
    """

    def __init__(self):
        """Initialize report generator."""
        self.template = self._load_template()

    def _load_template(self) -> str:
        """Load HTML template with embedded CSS."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenNL2Data-Bench Report - {system_name}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
        }}

        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}

        header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}

        .report-meta {{
            background: #f8f9fa;
            padding: 20px 40px;
            border-bottom: 1px solid #dee2e6;
        }}

        .report-meta table {{
            width: 100%;
        }}

        .report-meta td {{
            padding: 8px;
        }}

        .report-meta td:first-child {{
            font-weight: 600;
            width: 150px;
        }}

        .content {{
            padding: 40px;
        }}

        .overall-score {{
            text-align: center;
            padding: 40px;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            border-radius: 8px;
            margin-bottom: 40px;
        }}

        .overall-score h2 {{
            font-size: 1.5em;
            margin-bottom: 20px;
            opacity: 0.9;
        }}

        .score-value {{
            font-size: 4em;
            font-weight: bold;
            margin: 20px 0;
        }}

        .certification-badge {{
            display: inline-block;
            padding: 10px 30px;
            background: rgba(255,255,255,0.2);
            border-radius: 25px;
            font-size: 1.3em;
            font-weight: 600;
            margin-top: 20px;
        }}

        .certification-platinum {{
            background: linear-gradient(135deg, #e0e0e0 0%, #f5f5f5 100%);
            color: #333;
        }}

        .certification-gold {{
            background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
            color: #333;
        }}

        .certification-silver {{
            background: linear-gradient(135deg, #C0C0C0 0%, #A8A8A8 100%);
            color: #333;
        }}

        .certification-bronze {{
            background: linear-gradient(135deg, #CD7F32 0%, #A0522D 100%);
            color: white;
        }}

        .dimension-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}

        .dimension-card {{
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 20px;
            background: white;
        }}

        .dimension-card h3 {{
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.2em;
        }}

        .metric-row {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #f0f0f0;
        }}

        .metric-row:last-child {{
            border-bottom: none;
        }}

        .metric-label {{
            color: #666;
        }}

        .metric-value {{
            font-weight: 600;
            color: #333;
        }}

        .metric-good {{
            color: #28a745;
        }}

        .metric-warning {{
            color: #ffc107;
        }}

        .metric-bad {{
            color: #dc3545;
        }}

        table.details {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}

        table.details th {{
            background: #f8f9fa;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #dee2e6;
        }}

        table.details td {{
            padding: 12px;
            border-bottom: 1px solid #f0f0f0;
        }}

        table.details tr:hover {{
            background: #f8f9fa;
        }}

        .section {{
            margin-bottom: 40px;
        }}

        .section h2 {{
            color: #333;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }}

        footer {{
            background: #f8f9fa;
            padding: 20px 40px;
            text-align: center;
            color: #666;
            border-top: 1px solid #dee2e6;
        }}

        .progress-bar {{
            height: 8px;
            background: #e9ecef;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 5px;
        }}

        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            transition: width 0.3s ease;
        }}

        @media (max-width: 768px) {{
            .dimension-grid {{
                grid-template-columns: 1fr;
            }}

            header h1 {{
                font-size: 1.8em;
            }}

            .score-value {{
                font-size: 3em;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>OpenNL2Data-Bench Test Report</h1>
            <p>{system_name}</p>
        </header>

        <div class="report-meta">
            <table>
                <tr>
                    <td>Test Date:</td>
                    <td>{test_date}</td>
                </tr>
                <tr>
                    <td>Model:</td>
                    <td>{model_name}</td>
                </tr>
                <tr>
                    <td>Database:</td>
                    <td>{database_type}</td>
                </tr>
                <tr>
                    <td>Domain:</td>
                    <td>{domain}</td>
                </tr>
            </table>
        </div>

        <div class="content">
            <div class="overall-score">
                <h2>Overall Score</h2>
                <div class="score-value">{overall_score}/100</div>
                <div class="certification-badge {certification_class}">
                    {certification_level} 🏆
                </div>
            </div>

            <div class="section">
                <h2>📊 Six-Dimensional Evaluation</h2>
                <div class="dimension-grid">
                    {dimensions_html}
                </div>
            </div>

            {details_html}
        </div>

        <footer>
            <p>Generated by OpenNL2Data-Bench | PowerData Community</p>
            <p>🤖 <a href="https://github.com/powerdata-ai/open-nl2data-bench" style="color: #667eea; text-decoration: none;">GitHub</a> |
               <a href="https://opennl2data-bench.powerdata.org" style="color: #667eea; text-decoration: none;">Website</a></p>
        </footer>
    </div>
</body>
</html>
"""

    def generate(self, data: ReportData, output_path: str) -> None:
        """
        Generate HTML report and save to file.

        Args:
            data: Report data
            output_path: Output file path
        """
        html = self.generate_html(data)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

    def generate_html(self, data: ReportData) -> str:
        """
        Generate HTML report as string.

        Args:
            data: Report data

        Returns:
            HTML string
        """
        # Determine certification level
        cert_level = self._get_certification_level(data.overall_score)
        cert_class = f"certification-{cert_level.value.lower()}"

        # Generate dimensions HTML
        dimensions_html = self._generate_dimensions_html(data)

        # Generate details HTML
        details_html = self._generate_details_html(data)

        # Fill template
        html = self.template.format(
            system_name=data.system_name,
            test_date=data.test_date.strftime("%Y-%m-%d %H:%M:%S"),
            model_name=data.model_name or "N/A",
            database_type=data.database_type or "N/A",
            domain=data.domain or "N/A",
            overall_score=f"{data.overall_score:.1f}",
            certification_level=cert_level.value,
            certification_class=cert_class,
            dimensions_html=dimensions_html,
            details_html=details_html,
        )

        return html

    def _get_certification_level(self, score: float) -> CertificationLevel:
        """Get certification level based on score."""
        if score >= 90:
            return CertificationLevel.PLATINUM
        elif score >= 80:
            return CertificationLevel.GOLD
        elif score >= 70:
            return CertificationLevel.SILVER
        elif score >= 60:
            return CertificationLevel.BRONZE
        else:
            return CertificationLevel.NONE

    def _generate_dimensions_html(self, data: ReportData) -> str:
        """Generate HTML for six dimensions."""
        dimensions = []

        # Accuracy
        accuracy_color = self._get_metric_color(data.accuracy_rate * 100)
        dimensions.append(f"""
            <div class="dimension-card">
                <h3>✅ Accuracy</h3>
                <div class="metric-row">
                    <span class="metric-label">Accuracy Rate:</span>
                    <span class="metric-value {accuracy_color}">{data.accuracy_rate * 100:.1f}%</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Correct Answers:</span>
                    <span class="metric-value">{data.correct_answers}/{data.total_questions}</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {data.accuracy_rate * 100}%"></div>
                </div>
            </div>
        """)

        # Performance
        if data.performance_metrics:
            perf = data.performance_metrics
            p95_color = "metric-good" if perf.p95 < 3000 else "metric-warning" if perf.p95 < 5000 else "metric-bad"
            dimensions.append(f"""
                <div class="dimension-card">
                    <h3>⚡ Performance</h3>
                    <div class="metric-row">
                        <span class="metric-label">P50 Latency:</span>
                        <span class="metric-value">{perf.p50:.0f}ms</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">P95 Latency:</span>
                        <span class="metric-value {p95_color}">{perf.p95:.0f}ms</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">P99 Latency:</span>
                        <span class="metric-value">{perf.p99:.0f}ms</span>
                    </div>
                </div>
            """)

        # Cost
        if data.total_cost is not None and data.avg_cost_per_query is not None:
            cost_color = "metric-good" if data.avg_cost_per_query < 0.01 else "metric-warning" if data.avg_cost_per_query < 0.05 else "metric-bad"
            dimensions.append(f"""
                <div class="dimension-card">
                    <h3>💰 Cost</h3>
                    <div class="metric-row">
                        <span class="metric-label">Total Cost:</span>
                        <span class="metric-value">${data.total_cost:.4f}</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Avg Cost/Query:</span>
                        <span class="metric-value {cost_color}">${data.avg_cost_per_query:.4f}</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Total Tokens:</span>
                        <span class="metric-value">{data.total_tokens:,}</span>
                    </div>
                </div>
            """)

        # Robustness
        if data.robustness_pass_rate is not None:
            robust_color = self._get_metric_color(data.robustness_pass_rate * 100)
            dimensions.append(f"""
                <div class="dimension-card">
                    <h3>🛡️ Robustness</h3>
                    <div class="metric-row">
                        <span class="metric-label">Pass Rate:</span>
                        <span class="metric-value {robust_color}">{data.robustness_pass_rate * 100:.1f}%</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Tests Passed:</span>
                        <span class="metric-value">{data.robustness_tests_passed}/{data.robustness_tests_total}</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {data.robustness_pass_rate * 100}%"></div>
                    </div>
                </div>
            """)

        return "\n".join(dimensions)

    def _generate_details_html(self, data: ReportData) -> str:
        """Generate detailed results HTML."""
        sections = []

        # Performance details
        if data.performance_metrics:
            perf = data.performance_metrics
            sections.append(f"""
                <div class="section">
                    <h2>⚡ Performance Details</h2>
                    <table class="details">
                        <thead>
                            <tr>
                                <th>Metric</th>
                                <th>Value</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>Mean Time</td>
                                <td>{perf.mean_time_ms:.2f}ms</td>
                            </tr>
                            <tr>
                                <td>Median Time</td>
                                <td>{perf.median_time_ms:.2f}ms</td>
                            </tr>
                            <tr>
                                <td>Min Time</td>
                                <td>{perf.min_time_ms:.2f}ms</td>
                            </tr>
                            <tr>
                                <td>Max Time</td>
                                <td>{perf.max_time_ms:.2f}ms</td>
                            </tr>
                            <tr>
                                <td>Std Deviation</td>
                                <td>{perf.std_dev:.2f}ms</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            """)

        return "\n".join(sections)

    def _get_metric_color(self, percentage: float) -> str:
        """Get CSS class for metric based on percentage."""
        if percentage >= 80:
            return "metric-good"
        elif percentage >= 60:
            return "metric-warning"
        else:
            return "metric-bad"
