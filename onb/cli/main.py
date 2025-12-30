"""
Main CLI application for OpenNL2SQL-Bench.

This module provides the command-line interface using Typer.
"""

from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.table import Table

from onb.adapters.database.mysql import MySQLAdapter
from onb.adapters.sut.mock import MockSUTAdapter
from onb.core.config import ConfigLoader
from onb.core.types import (
    ComplexityLevel,
    DatabaseConfig,
    SUTConfig,
    TestStatus,
)
from onb.questions.loader import QuestionLoader
from onb.runner.test_runner import TestRunner

app = typer.Typer(
    name="onb",
    help="OpenNL2SQL-Bench: Production-grade NL2SQL/ChatBI benchmark framework",
    add_completion=False,
)

test_app = typer.Typer(help="Test execution commands")
app.add_typer(test_app, name="test")

console = Console()


@test_app.command("run")
def test_run(
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file (YAML)",
        exists=True,
    ),
    questions_dir: Optional[Path] = typer.Option(
        None,
        "--questions",
        "-q",
        help="Directory containing question files",
        exists=True,
    ),
    domain: Optional[str] = typer.Option(
        None,
        "--domain",
        "-d",
        help="Filter questions by domain",
    ),
    complexity: Optional[List[str]] = typer.Option(
        None,
        "--complexity",
        "-l",
        help="Filter by complexity levels (L1, L2, L3, L4, L5)",
    ),
    tags: Optional[List[str]] = typer.Option(
        None,
        "--tag",
        "-t",
        help="Filter by tags",
    ),
    language: str = typer.Option(
        "zh",
        "--language",
        "-lang",
        help="Question language (en/zh)",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file for test report (JSON)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Verbose output",
    ),
):
    """
    Run benchmark tests.

    Examples:
        # Run all questions from a directory
        onb test run -q ./questions

        # Run with specific domain and complexity
        onb test run -q ./questions -d ecommerce -l L1 -l L2

        # Run with configuration file
        onb test run -c config.yaml -q ./questions

        # Save results to file
        onb test run -q ./questions -o results.json
    """
    try:
        console.print("[bold blue]OpenNL2SQL-Bench Test Runner[/bold blue]")
        console.print()

        # Load configuration
        if config:
            console.print(f"Loading configuration from: {config}")
            loader = ConfigLoader()
            config_data = loader.load_yaml(config)
            db_config = DatabaseConfig(**config_data.get("database", {}))
            sut_config = SUTConfig(**config_data.get("sut", {}))
        else:
            console.print("[yellow]No configuration file provided, using defaults[/yellow]")
            # Use mock adapters for demo
            db_config = None
            sut_config = SUTConfig(
                name="MockSUT",
                type="mock",
                version="1.0.0",
                config={},
            )

        # Load questions
        if not questions_dir:
            console.print(
                "[red]Error: --questions directory is required[/red]",
                style="bold",
            )
            raise typer.Exit(1)

        console.print(f"Loading questions from: {questions_dir}")
        question_loader = QuestionLoader()
        questions = question_loader.load_questions(questions_dir)

        if not questions:
            console.print(
                f"[red]No questions found in {questions_dir}[/red]",
                style="bold",
            )
            raise typer.Exit(1)

        console.print(f"Loaded {len(questions)} questions")

        # Apply filters
        if domain or complexity or tags:
            complexity_levels = None
            if complexity:
                try:
                    complexity_levels = [ComplexityLevel(c) for c in complexity]
                except ValueError as e:
                    console.print(f"[red]Invalid complexity level: {e}[/red]")
                    raise typer.Exit(1)

            filtered = question_loader.filter_questions(
                questions,
                domain=domain,
                complexity=complexity_levels,
                tags=tags,
            )

            console.print(
                f"Filtered to {len(filtered)} questions "
                f"(domain={domain}, complexity={complexity}, tags={tags})"
            )
            questions = filtered

        if not questions:
            console.print(
                "[red]No questions match the filter criteria[/red]",
                style="bold",
            )
            raise typer.Exit(1)

        # Show statistics
        if verbose:
            stats = question_loader.get_statistics(questions)
            console.print("\n[bold]Question Statistics:[/bold]")
            console.print(f"  Total: {stats['total']}")
            console.print(f"  By Domain: {stats['by_domain']}")
            console.print(f"  By Complexity: {stats['by_complexity']}")
            console.print(f"  By Tags: {stats['by_tags']}")
            console.print()

        # Initialize adapters
        console.print("[bold]Initializing adapters...[/bold]")

        if db_config:
            db_adapter = MySQLAdapter(db_config)
        else:
            # Use mock database adapter for demo
            from onb.adapters.database.base import DatabaseAdapter
            from onb.core.types import DatabaseType, SchemaInfo, TableInfo, ColumnInfo
            from unittest.mock import MagicMock

            db_adapter = MagicMock(spec=DatabaseAdapter)
            db_adapter.database_type = DatabaseType.MYSQL
            db_adapter.get_schema_info.return_value = SchemaInfo(
                database_name="demo_db",
                database_type=DatabaseType.MYSQL,
                tables=[
                    TableInfo(
                        name="users",
                        columns=[
                            ColumnInfo(name="id", type="int", primary_key=True),
                            ColumnInfo(name="name", type="varchar"),
                        ],
                    )
                ],
            )

        sut_adapter = MockSUTAdapter(sut_config)
        sut_adapter.initialize()

        # Run tests
        console.print(f"\n[bold green]Running {len(questions)} tests...[/bold green]\n")

        runner = TestRunner(db_adapter, sut_adapter)
        report = runner.run_test_suite(questions, language=language)

        # Display results
        console.print("\n[bold]Test Results:[/bold]\n")

        # Summary table
        summary_table = Table(title="Summary")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="magenta")

        summary_table.add_row("SUT Name", report.sut_name)
        summary_table.add_row("Database Type", report.database_type.value)
        summary_table.add_row("Domain", report.domain)
        summary_table.add_row("Total Questions", str(report.total_questions))
        summary_table.add_row("Correct", str(report.correct_count))
        summary_table.add_row(
            "Accuracy",
            f"{report.accuracy * 100:.2f}%",
            style="bold green" if report.accuracy >= 0.8 else "bold yellow"
            if report.accuracy >= 0.5 else "bold red",
        )
        summary_table.add_row(
            "Duration", f"{report.total_duration_seconds:.2f}s"
        )

        console.print(summary_table)

        # Results by status
        if verbose:
            console.print("\n[bold]Detailed Results:[/bold]\n")

            results_table = Table()
            results_table.add_column("Question ID", style="cyan")
            results_table.add_column("Status", style="magenta")
            results_table.add_column("Generated SQL", style="white", overflow="fold")
            results_table.add_column("Reason", style="yellow", overflow="fold")

            for result in report.question_results:
                status_style = (
                    "green" if result.status == TestStatus.PASSED
                    else "red" if result.status == TestStatus.FAILED
                    else "yellow"
                )

                sql_preview = result.sut_response.generated_sql[:50] + "..." \
                    if len(result.sut_response.generated_sql) > 50 \
                    else result.sut_response.generated_sql

                results_table.add_row(
                    result.question.id,
                    f"[{status_style}]{result.status.value}[/{status_style}]",
                    sql_preview,
                    result.comparison_result.reason or "",
                )

            console.print(results_table)

        # Save to file
        if output:
            console.print(f"\n[bold]Saving results to: {output}[/bold]")
            import json
            from dataclasses import asdict

            # Convert report to dict for JSON serialization
            report_dict = {
                "sut_name": report.sut_name,
                "test_id": report.test_id,
                "domain": report.domain,
                "database_type": report.database_type.value,
                "total_questions": report.total_questions,
                "correct_count": report.correct_count,
                "accuracy": report.accuracy,
                "start_time": report.start_time.isoformat(),
                "end_time": report.end_time.isoformat(),
                "total_duration_seconds": report.total_duration_seconds,
                "results": [
                    {
                        "question_id": r.question.id,
                        "status": r.status.value,
                        "generated_sql": r.sut_response.generated_sql,
                        "match": r.comparison_result.match,
                        "reason": r.comparison_result.reason,
                    }
                    for r in report.question_results
                ],
            }

            with open(output, "w", encoding="utf-8") as f:
                json.dump(report_dict, f, indent=2, ensure_ascii=False)

            console.print("[green]Results saved successfully![/green]")

        # Exit with appropriate code
        if report.accuracy < 1.0:
            console.print(
                f"\n[yellow]Some tests failed. Accuracy: {report.accuracy * 100:.2f}%[/yellow]"
            )
        else:
            console.print("\n[green]All tests passed![/green]")

    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]", style="bold")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        raise typer.Exit(1)


@app.command("version")
def version():
    """Show version information."""
    console.print("[bold]OpenNL2SQL-Bench[/bold]")
    console.print("Version: 0.1.0")
    console.print("License: Apache 2.0")
    console.print("Copyright: PowerData Community")


if __name__ == "__main__":
    app()
