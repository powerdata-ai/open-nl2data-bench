"""
Tests for CLI module (onb/cli/main.py).

This module tests the command-line interface using Typer's testing utilities.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from onb.cli.main import app
from onb.core.types import ComplexityLevel, Question

# Initialize test runner
runner = CliRunner()


@pytest.fixture
def sample_questions_dir(tmp_path: Path) -> Path:
    """Create a temporary directory with sample question files."""
    questions_dir = tmp_path / "questions"
    questions_dir.mkdir()

    # Create sample question file
    question_file = questions_dir / "sample.yaml"
    question_file.write_text("""
questions:
  - question_id: "TEST-001"
    question_text: "Sample question"
    difficulty_level: "L1"
    complexity: "L1"
    domain: "test"
    tags: ["sample", "test"]
    target_tables: ["table1"]
    golden_sql: "SELECT * FROM table1;"
    created_at: "2025-01-01"
""")

    return questions_dir


@pytest.fixture
def sample_config(tmp_path: Path) -> Path:
    """Create a temporary configuration file."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
database:
  type: "mysql"
  host: "localhost"
  port: 3306
  database: "test_db"
  username: "test_user"
  password: "test_pass"

sut:
  name: "TestSUT"
  type: "mock"
  version: "1.0.0"
  config: {}
""")

    return config_file


class TestCLITestRun:
    """Test the 'onb test run' command."""

    def test_run_without_questions_dir_fails(self):
        """Test that run fails when questions directory is not provided."""
        result = runner.invoke(app, ["test", "run"])

        assert result.exit_code == 1
        assert "questions directory is required" in result.stdout.lower()

    @patch("onb.cli.main.QuestionLoader")
    @patch("onb.cli.main.TestRunner")
    def test_run_with_no_questions_found(
        self,
        mock_runner: MagicMock,
        mock_loader: MagicMock,
        sample_questions_dir: Path,
    ):
        """Test run when no questions are found."""
        # Mock question loader to return empty list
        mock_loader_instance = MagicMock()
        mock_loader_instance.load_questions.return_value = []
        mock_loader.return_value = mock_loader_instance

        result = runner.invoke(
            app, ["test", "run", "--questions", str(sample_questions_dir)]
        )

        assert result.exit_code == 1
        assert "no questions found" in result.stdout.lower()

    @patch("onb.cli.main.QuestionLoader")
    @patch("onb.cli.main.TestRunner")
    @patch("onb.cli.main.MockSUTAdapter")
    def test_run_with_sample_questions(
        self,
        mock_sut: MagicMock,
        mock_runner: MagicMock,
        mock_loader: MagicMock,
        sample_questions_dir: Path,
    ):
        """Test successful run with sample questions."""
        # Mock question loader
        sample_questions = [
            Question(
                id="TEST-001",
                version="1.0",
                question_text={"en": "Sample question", "zh": "示例问题"},
                complexity=ComplexityLevel.L1,
                domain="test",
                tags=["sample"],
                dependencies={"tables": ["table1"], "features": []},
                golden_sql="SELECT * FROM table1;",
                metadata={"created_by": "test", "created_at": "2025-01-01"},
            )
        ]
        mock_loader_instance = MagicMock()
        mock_loader_instance.load_questions.return_value = sample_questions
        mock_loader_instance.filter_questions.return_value = sample_questions
        mock_loader_instance.get_statistics.return_value = {
            "total": 1,
            "by_domain": {"test": 1},
            "by_complexity": {"L1": 1},
            "by_tags": {"sample": 1},
        }
        mock_loader.return_value = mock_loader_instance

        # Mock test runner
        from onb.core.types import DatabaseType, TestReport, TestStatus
        from datetime import datetime

        mock_report = MagicMock(spec=TestReport)
        mock_report.sut_name = "MockSUT"
        mock_report.database_type = DatabaseType.MYSQL
        mock_report.domain = "test"
        mock_report.total_questions = 1
        mock_report.correct_count = 1
        mock_report.accuracy = 1.0
        mock_report.total_duration_seconds = 0.5
        mock_report.question_results = []

        mock_runner_instance = MagicMock()
        mock_runner_instance.run_test_suite.return_value = mock_report
        mock_runner.return_value = mock_runner_instance

        result = runner.invoke(
            app, ["test", "run", "--questions", str(sample_questions_dir)]
        )

        # Debug: print output if failed
        if result.exit_code != 0:
            print(f"\nActual output:\n{result.stdout}")
            if result.exception:
                print(f"Exception: {result.exception}")

        # Should succeed
        assert result.exit_code == 0
        assert "loaded 1 questions" in result.stdout.lower()

    @patch("onb.cli.main.QuestionLoader")
    @patch("onb.cli.main.TestRunner")
    @patch("onb.cli.main.ConfigLoader")
    def test_run_with_config_file(
        self,
        mock_config_loader: MagicMock,
        mock_runner: MagicMock,
        mock_loader: MagicMock,
        sample_questions_dir: Path,
        sample_config: Path,
    ):
        """Test run with configuration file."""
        # Mock config loader
        mock_config_instance = MagicMock()
        mock_config_instance.load_yaml.return_value = {
            "database": {
                "type": "mysql",
                "host": "localhost",
                "database": "test_db",
            },
            "sut": {"name": "TestSUT", "type": "mock", "version": "1.0.0"},
        }
        mock_config_loader.return_value = mock_config_instance

        # Mock question loader
        sample_questions = [
            Question(
                id="TEST-001",
                version="1.0",
                question_text={"en": "Sample question", "zh": "示例问题"},
                complexity=ComplexityLevel.L1,
                domain="test",
                tags=[],
                dependencies={"tables": ["table1"], "features": []},
                golden_sql="SELECT * FROM table1;",
                metadata={"created_by": "test", "created_at": "2025-01-01"},
            )
        ]
        mock_loader_instance = MagicMock()
        mock_loader_instance.load_questions.return_value = sample_questions
        mock_loader.return_value = mock_loader_instance

        # Mock test runner
        from onb.core.types import DatabaseType, TestReport, TestStatus
        from datetime import datetime

        mock_report = MagicMock(spec=TestReport)
        mock_report.sut_name = "MockSUT"
        mock_report.database_type = DatabaseType.MYSQL
        mock_report.domain = "test"
        mock_report.total_questions = 1
        mock_report.correct_count = 1
        mock_report.accuracy = 1.0
        mock_report.total_duration_seconds = 0.5
        mock_report.question_results = []

        mock_runner_instance = MagicMock()
        mock_runner_instance.run_test_suite.return_value = mock_report
        mock_runner.return_value = mock_runner_instance

        result = runner.invoke(
            app,
            [
                "test",
                "run",
                "--config",
                str(sample_config),
                "--questions",
                str(sample_questions_dir),
            ],
        )

        assert result.exit_code == 0
        assert "loading configuration" in result.stdout.lower()

    @patch("onb.cli.main.QuestionLoader")
    @patch("onb.cli.main.TestRunner")
    def test_run_with_filters(
        self,
        mock_runner: MagicMock,
        mock_loader: MagicMock,
        sample_questions_dir: Path,
    ):
        """Test run with domain and complexity filters."""
        sample_questions = [
            Question(
                id="TEST-001",
                version="1.0",
                question_text={"en": "Sample question", "zh": "示例问题"},
                complexity=ComplexityLevel.L1,
                domain="test",
                tags=["sample"],
                dependencies={"tables": ["table1"], "features": []},
                golden_sql="SELECT * FROM table1;",
                metadata={"created_by": "test", "created_at": "2025-01-01"},
            )
        ]

        mock_loader_instance = MagicMock()
        mock_loader_instance.load_questions.return_value = sample_questions
        mock_loader_instance.filter_questions.return_value = sample_questions
        mock_loader.return_value = mock_loader_instance

        # Mock test runner
        from onb.core.types import DatabaseType, TestReport, TestStatus
        from datetime import datetime

        mock_report = MagicMock(spec=TestReport)
        mock_report.sut_name = "MockSUT"
        mock_report.database_type = DatabaseType.MYSQL
        mock_report.domain = "test"
        mock_report.total_questions = 1
        mock_report.correct_count = 1
        mock_report.accuracy = 1.0
        mock_report.total_duration_seconds = 0.5
        mock_report.question_results = []

        mock_runner_instance = MagicMock()
        mock_runner_instance.run_test_suite.return_value = mock_report
        mock_runner.return_value = mock_runner_instance

        result = runner.invoke(
            app,
            [
                "test",
                "run",
                "--questions",
                str(sample_questions_dir),
                "--domain",
                "test",
                "--complexity",
                "L1",
            ],
        )

        assert result.exit_code == 0
        # Verify filter was called
        mock_loader_instance.filter_questions.assert_called_once()

    @patch("onb.cli.main.QuestionLoader")
    @patch("onb.cli.main.TestRunner")
    def test_run_with_invalid_complexity(
        self,
        mock_runner: MagicMock,
        mock_loader: MagicMock,
        sample_questions_dir: Path,
    ):
        """Test run with invalid complexity level."""
        sample_questions = [
            Question(
                id="TEST-001",
                version="1.0",
                question_text={"en": "Sample question", "zh": "示例问题"},
                complexity=ComplexityLevel.L1,
                domain="test",
                tags=[],
                dependencies={"tables": ["table1"], "features": []},
                golden_sql="SELECT * FROM table1;",
                metadata={"created_by": "test", "created_at": "2025-01-01"},
            )
        ]

        mock_loader_instance = MagicMock()
        mock_loader_instance.load_questions.return_value = sample_questions
        mock_loader.return_value = mock_loader_instance

        result = runner.invoke(
            app,
            [
                "test",
                "run",
                "--questions",
                str(sample_questions_dir),
                "--complexity",
                "INVALID",
            ],
        )

        assert result.exit_code == 1
        assert "invalid complexity level" in result.stdout.lower()

    @patch("onb.cli.main.QuestionLoader")
    @patch("onb.cli.main.TestRunner")
    def test_run_with_verbose_output(
        self,
        mock_runner: MagicMock,
        mock_loader: MagicMock,
        sample_questions_dir: Path,
    ):
        """Test run with verbose output."""
        sample_questions = [
            Question(
                id="TEST-001",
                version="1.0",
                question_text={"en": "Sample question", "zh": "示例问题"},
                complexity=ComplexityLevel.L1,
                domain="test",
                tags=["sample"],
                dependencies={"tables": ["table1"], "features": []},
                golden_sql="SELECT * FROM table1;",
                metadata={"created_by": "test", "created_at": "2025-01-01"},
            )
        ]

        mock_loader_instance = MagicMock()
        mock_loader_instance.load_questions.return_value = sample_questions
        mock_loader_instance.get_statistics.return_value = {
            "total": 1,
            "by_domain": {"test": 1},
            "by_complexity": {"L1": 1},
            "by_tags": {"sample": 1},
        }
        mock_loader.return_value = mock_loader_instance

        # Mock test runner
        from onb.core.types import DatabaseType, TestReport, TestStatus
        from datetime import datetime

        mock_report = MagicMock(spec=TestReport)
        mock_report.sut_name = "MockSUT"
        mock_report.database_type = DatabaseType.MYSQL
        mock_report.domain = "test"
        mock_report.total_questions = 1
        mock_report.correct_count = 1
        mock_report.accuracy = 1.0
        mock_report.total_duration_seconds = 0.5
        mock_report.question_results = []

        mock_runner_instance = MagicMock()
        mock_runner_instance.run_test_suite.return_value = mock_report
        mock_runner.return_value = mock_runner_instance

        result = runner.invoke(
            app,
            [
                "test",
                "run",
                "--questions",
                str(sample_questions_dir),
                "--verbose",
            ],
        )

        assert result.exit_code == 0
        assert "question statistics" in result.stdout.lower()

    @patch("onb.cli.main.QuestionLoader")
    @patch("onb.cli.main.TestRunner")
    def test_run_with_output_file(
        self,
        mock_runner: MagicMock,
        mock_loader: MagicMock,
        sample_questions_dir: Path,
        tmp_path: Path,
    ):
        """Test run with output file."""
        sample_questions = [
            Question(
                id="TEST-001",
                version="1.0",
                question_text={"en": "Sample question", "zh": "示例问题"},
                complexity=ComplexityLevel.L1,
                domain="test",
                tags=[],
                dependencies={"tables": ["table1"], "features": []},
                golden_sql="SELECT * FROM table1;",
                metadata={"created_by": "test", "created_at": "2025-01-01"},
            )
        ]

        mock_loader_instance = MagicMock()
        mock_loader_instance.load_questions.return_value = sample_questions
        mock_loader.return_value = mock_loader_instance

        # Mock test runner
        from onb.core.types import DatabaseType, TestReport, TestStatus
        from datetime import datetime

        mock_report = MagicMock(spec=TestReport)
        mock_report.sut_name = "MockSUT"
        mock_report.database_type = DatabaseType.MYSQL
        mock_report.domain = "test"
        mock_report.total_questions = 1
        mock_report.correct_count = 1
        mock_report.accuracy = 1.0
        mock_report.total_duration_seconds = 0.5
        mock_report.question_results = []

        mock_runner_instance = MagicMock()
        mock_runner_instance.run_test_suite.return_value = mock_report
        mock_runner.return_value = mock_runner_instance

        output_file = tmp_path / "results.json"

        result = runner.invoke(
            app,
            [
                "test",
                "run",
                "--questions",
                str(sample_questions_dir),
                "--output",
                str(output_file),
            ],
        )

        assert result.exit_code == 0


class TestCLIHelp:
    """Test CLI help messages."""

    def test_main_help(self):
        """Test main help message."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "opennl2sql-bench" in result.stdout.lower() or "nl2sql" in result.stdout.lower()

    def test_test_help(self):
        """Test 'test' subcommand help."""
        result = runner.invoke(app, ["test", "--help"])

        assert result.exit_code == 0
        assert "test" in result.stdout.lower()

    def test_test_run_help(self):
        """Test 'test run' command help."""
        result = runner.invoke(app, ["test", "run", "--help"])

        assert result.exit_code == 0
        assert "run benchmark tests" in result.stdout.lower()
        assert "--questions" in result.stdout.lower()
