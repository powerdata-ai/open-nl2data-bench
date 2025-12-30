"""Unit tests for question loader module."""
import pytest
import yaml
from pathlib import Path

from onb.core.exceptions import InvalidConfigError, MissingConfigError
from onb.core.types import ComplexityLevel, Question
from onb.questions.loader import QuestionLoader


@pytest.fixture
def sample_question_data():
    """Sample question data for testing."""
    return {
        "id": "ecommerce_L1_001",
        "version": "1.0",
        "domain": "ecommerce",
        "complexity": "L1",
        "question": {
            "en": "How many users are there?",
            "zh": "有多少用户？"
        },
        "golden_sql": "SELECT COUNT(*) FROM users",
        "dependencies": {
            "tables": ["users"],
            "features": ["COUNT"]
        },
        "tags": ["basic", "aggregation"],
        "metadata": {
            "difficulty": "easy",
            "author": "test"
        }
    }


@pytest.fixture
def sample_question_with_rules():
    """Sample question with comparison rules."""
    return {
        "id": "finance_L2_001",
        "version": "1.0",
        "domain": "finance",
        "complexity": "L2",
        "question": {
            "en": "What is the average balance?",
            "zh": "平均余额是多少？"
        },
        "golden_sql": "SELECT AVG(balance) FROM accounts",
        "dependencies": {
            "tables": ["accounts"],
            "features": ["AVG"]
        },
        "comparison_rules": {
            "row_order_matters": False,
            "float_tolerance": 0.01,
            "float_comparison_mode": "absolute_error"
        }
    }


class TestQuestionLoader:
    """Test QuestionLoader class."""

    def test_loader_initialization(self):
        """Test loader initialization."""
        loader = QuestionLoader()
        assert loader._cache == {}

    def test_load_question_success(self, tmp_path, sample_question_data):
        """Test loading a valid question."""
        # Create question file
        question_file = tmp_path / "question.yaml"
        with open(question_file, "w", encoding="utf-8") as f:
            yaml.dump(sample_question_data, f)

        loader = QuestionLoader()
        question = loader.load_question(question_file)

        assert question.id == "ecommerce_L1_001"
        assert question.domain == "ecommerce"
        assert question.complexity == ComplexityLevel.L1
        assert question.get_question("en") == "How many users are there?"
        assert question.get_question("zh") == "有多少用户？"
        assert question.golden_sql == "SELECT COUNT(*) FROM users"
        assert "users" in question.dependencies["tables"]
        assert "basic" in question.tags

    def test_load_question_file_not_found(self):
        """Test loading non-existent file."""
        loader = QuestionLoader()

        with pytest.raises(MissingConfigError, match="not found"):
            loader.load_question(Path("/nonexistent/question.yaml"))

    def test_load_question_empty_file(self, tmp_path):
        """Test loading empty file."""
        question_file = tmp_path / "empty.yaml"
        question_file.touch()

        loader = QuestionLoader()

        with pytest.raises(InvalidConfigError, match="Empty question file"):
            loader.load_question(question_file)

    def test_load_question_invalid_yaml(self, tmp_path):
        """Test loading invalid YAML."""
        question_file = tmp_path / "invalid.yaml"
        with open(question_file, "w") as f:
            f.write("invalid: yaml: content:")

        loader = QuestionLoader()

        with pytest.raises(InvalidConfigError, match="Invalid YAML"):
            loader.load_question(question_file)

    def test_load_question_missing_required_field(self, tmp_path):
        """Test loading question with missing required field."""
        question_data = {
            "id": "test_001",
            "version": "1.0",
            # Missing domain, complexity, question, golden_sql
        }

        question_file = tmp_path / "incomplete.yaml"
        with open(question_file, "w", encoding="utf-8") as f:
            yaml.dump(question_data, f)

        loader = QuestionLoader()

        with pytest.raises(InvalidConfigError, match="Missing required field"):
            loader.load_question(question_file)

    def test_load_question_invalid_complexity(self, tmp_path):
        """Test loading question with invalid complexity level."""
        question_data = {
            "id": "test_001",
            "version": "1.0",
            "domain": "test",
            "complexity": "INVALID",  # Invalid complexity
            "question": {"en": "Test"},
            "golden_sql": "SELECT 1"
        }

        question_file = tmp_path / "bad_complexity.yaml"
        with open(question_file, "w", encoding="utf-8") as f:
            yaml.dump(question_data, f)

        loader = QuestionLoader()

        with pytest.raises(InvalidConfigError, match="Invalid complexity level"):
            loader.load_question(question_file)

    def test_load_question_invalid_question_text_format(self, tmp_path):
        """Test loading question with invalid question_text format."""
        question_data = {
            "id": "test_001",
            "version": "1.0",
            "domain": "test",
            "complexity": "L1",
            "question": "This should be a dict",  # Invalid format
            "golden_sql": "SELECT 1"
        }

        question_file = tmp_path / "bad_question.yaml"
        with open(question_file, "w", encoding="utf-8") as f:
            yaml.dump(question_data, f)

        loader = QuestionLoader()

        with pytest.raises(InvalidConfigError, match="must be a dict"):
            loader.load_question(question_file)

    def test_load_question_empty_question_text(self, tmp_path):
        """Test loading question with empty question_text."""
        question_data = {
            "id": "test_001",
            "version": "1.0",
            "domain": "test",
            "complexity": "L1",
            "question": {},  # Empty dict
            "golden_sql": "SELECT 1"
        }

        question_file = tmp_path / "empty_question.yaml"
        with open(question_file, "w", encoding="utf-8") as f:
            yaml.dump(question_data, f)

        loader = QuestionLoader()

        with pytest.raises(InvalidConfigError, match="at least one language"):
            loader.load_question(question_file)

    def test_load_question_with_comparison_rules(self, tmp_path, sample_question_with_rules):
        """Test loading question with comparison rules."""
        question_file = tmp_path / "with_rules.yaml"
        with open(question_file, "w", encoding="utf-8") as f:
            yaml.dump(sample_question_with_rules, f)

        loader = QuestionLoader()
        question = loader.load_question(question_file)

        assert question.comparison_rules is not None
        assert question.comparison_rules.row_order_matters is False
        assert question.comparison_rules.float_tolerance == 0.01
        assert question.comparison_rules.float_comparison_mode == "absolute_error"

    def test_load_question_caching(self, tmp_path, sample_question_data):
        """Test question caching."""
        question_file = tmp_path / "question.yaml"
        with open(question_file, "w", encoding="utf-8") as f:
            yaml.dump(sample_question_data, f)

        loader = QuestionLoader()
        assert len(loader._cache) == 0

        question = loader.load_question(question_file)
        assert len(loader._cache) == 1
        assert loader._cache[question.id] == question

    def test_get_question_by_id(self, tmp_path, sample_question_data):
        """Test getting cached question by ID."""
        question_file = tmp_path / "question.yaml"
        with open(question_file, "w", encoding="utf-8") as f:
            yaml.dump(sample_question_data, f)

        loader = QuestionLoader()
        loader.load_question(question_file)

        # Get from cache
        cached = loader.get_question_by_id("ecommerce_L1_001")
        assert cached is not None
        assert cached.id == "ecommerce_L1_001"

        # Non-existent ID
        not_found = loader.get_question_by_id("nonexistent")
        assert not_found is None

    def test_clear_cache(self, tmp_path, sample_question_data):
        """Test clearing question cache."""
        question_file = tmp_path / "question.yaml"
        with open(question_file, "w", encoding="utf-8") as f:
            yaml.dump(sample_question_data, f)

        loader = QuestionLoader()
        loader.load_question(question_file)

        assert len(loader._cache) == 1

        loader.clear_cache()
        assert len(loader._cache) == 0


class TestLoadQuestions:
    """Test loading multiple questions from directory."""

    def test_load_questions_from_directory(self, tmp_path):
        """Test loading all questions from directory."""
        # Create multiple question files
        for i in range(3):
            question_data = {
                "id": f"test_L1_00{i+1}",
                "version": "1.0",
                "domain": "test",
                "complexity": "L1",
                "question": {"en": f"Question {i+1}"},
                "golden_sql": f"SELECT {i+1}"
            }
            question_file = tmp_path / f"question_{i+1}.yaml"
            with open(question_file, "w", encoding="utf-8") as f:
                yaml.dump(question_data, f)

        loader = QuestionLoader()
        questions = loader.load_questions(tmp_path)

        assert len(questions) == 3
        assert questions[0].id == "test_L1_001"
        assert questions[1].id == "test_L1_002"
        assert questions[2].id == "test_L1_003"

    def test_load_questions_directory_not_found(self):
        """Test loading from non-existent directory."""
        loader = QuestionLoader()

        with pytest.raises(MissingConfigError, match="not found"):
            loader.load_questions(Path("/nonexistent/directory"))

    def test_load_questions_not_a_directory(self, tmp_path):
        """Test loading from a file instead of directory."""
        question_file = tmp_path / "not_a_dir.yaml"
        question_file.touch()

        loader = QuestionLoader()

        with pytest.raises(InvalidConfigError, match="Not a directory"):
            loader.load_questions(question_file)

    def test_load_questions_with_pattern(self, tmp_path):
        """Test loading questions with glob pattern."""
        # Create YAML files
        for i in range(2):
            question_data = {
                "id": f"test_L1_00{i+1}",
                "version": "1.0",
                "domain": "test",
                "complexity": "L1",
                "question": {"en": f"Question {i+1}"},
                "golden_sql": f"SELECT {i+1}"
            }
            question_file = tmp_path / f"question_{i+1}.yaml"
            with open(question_file, "w", encoding="utf-8") as f:
                yaml.dump(question_data, f)

        # Create a non-YAML file (should be ignored with pattern)
        (tmp_path / "readme.txt").write_text("Not a question")

        loader = QuestionLoader()
        questions = loader.load_questions(tmp_path, pattern="*.yaml")

        assert len(questions) == 2

    def test_load_questions_skip_invalid_files(self, tmp_path):
        """Test that invalid files are skipped with warning."""
        # Create valid question
        valid_data = {
            "id": "test_L1_001",
            "version": "1.0",
            "domain": "test",
            "complexity": "L1",
            "question": {"en": "Valid question"},
            "golden_sql": "SELECT 1"
        }
        valid_file = tmp_path / "valid.yaml"
        with open(valid_file, "w", encoding="utf-8") as f:
            yaml.dump(valid_data, f)

        # Create invalid question (missing required fields)
        invalid_data = {"id": "incomplete"}
        invalid_file = tmp_path / "invalid.yaml"
        with open(invalid_file, "w", encoding="utf-8") as f:
            yaml.dump(invalid_data, f)

        loader = QuestionLoader()
        questions = loader.load_questions(tmp_path)

        # Should load valid question and skip invalid one
        assert len(questions) == 1
        assert questions[0].id == "test_L1_001"


class TestFilterQuestions:
    """Test question filtering functionality."""

    @pytest.fixture
    def sample_questions(self):
        """Create sample questions for filtering tests."""
        return [
            Question(
                id="ecommerce_L1_001",
                version="1.0",
                domain="ecommerce",
                complexity=ComplexityLevel.L1,
                question_text={"en": "Q1"},
                golden_sql="SELECT 1",
                dependencies={},
                tags=["basic", "select"]
            ),
            Question(
                id="ecommerce_L2_001",
                version="1.0",
                domain="ecommerce",
                complexity=ComplexityLevel.L2,
                question_text={"en": "Q2"},
                golden_sql="SELECT 2",
                dependencies={},
                tags=["aggregation"]
            ),
            Question(
                id="finance_L1_001",
                version="1.0",
                domain="finance",
                complexity=ComplexityLevel.L1,
                question_text={"en": "Q3"},
                golden_sql="SELECT 3",
                dependencies={},
                tags=["basic", "join"]
            ),
        ]

    def test_filter_by_domain(self, sample_questions):
        """Test filtering by domain."""
        loader = QuestionLoader()

        filtered = loader.filter_questions(sample_questions, domain="ecommerce")
        assert len(filtered) == 2
        assert all(q.domain == "ecommerce" for q in filtered)

        filtered = loader.filter_questions(sample_questions, domain="finance")
        assert len(filtered) == 1
        assert filtered[0].domain == "finance"

    def test_filter_by_complexity(self, sample_questions):
        """Test filtering by complexity levels."""
        loader = QuestionLoader()

        filtered = loader.filter_questions(
            sample_questions,
            complexity=[ComplexityLevel.L1]
        )
        assert len(filtered) == 2
        assert all(q.complexity == ComplexityLevel.L1 for q in filtered)

        filtered = loader.filter_questions(
            sample_questions,
            complexity=[ComplexityLevel.L2]
        )
        assert len(filtered) == 1

    def test_filter_by_tags(self, sample_questions):
        """Test filtering by tags."""
        loader = QuestionLoader()

        filtered = loader.filter_questions(sample_questions, tags=["basic"])
        assert len(filtered) == 2
        assert all("basic" in q.tags for q in filtered)

        filtered = loader.filter_questions(sample_questions, tags=["aggregation"])
        assert len(filtered) == 1

    def test_filter_multiple_criteria(self, sample_questions):
        """Test filtering with multiple criteria."""
        loader = QuestionLoader()

        filtered = loader.filter_questions(
            sample_questions,
            domain="ecommerce",
            complexity=[ComplexityLevel.L1],
            tags=["basic"]
        )
        assert len(filtered) == 1
        assert filtered[0].id == "ecommerce_L1_001"

    def test_filter_no_matches(self, sample_questions):
        """Test filtering with no matches."""
        loader = QuestionLoader()

        filtered = loader.filter_questions(sample_questions, domain="healthcare")
        assert len(filtered) == 0


class TestGetStatistics:
    """Test question statistics functionality."""

    def test_statistics_empty_list(self):
        """Test statistics for empty question list."""
        loader = QuestionLoader()
        stats = loader.get_statistics([])

        assert stats["total"] == 0
        assert stats["by_domain"] == {}
        assert stats["by_complexity"] == {}
        assert stats["by_tags"] == {}

    def test_statistics_with_questions(self):
        """Test statistics for question list."""
        questions = [
            Question(
                id="q1",
                version="1.0",
                domain="ecommerce",
                complexity=ComplexityLevel.L1,
                question_text={"en": "Q1"},
                golden_sql="SELECT 1",
                dependencies={},
                tags=["basic", "select"]
            ),
            Question(
                id="q2",
                version="1.0",
                domain="ecommerce",
                complexity=ComplexityLevel.L2,
                question_text={"en": "Q2"},
                golden_sql="SELECT 2",
                dependencies={},
                tags=["basic", "aggregation"]
            ),
            Question(
                id="q3",
                version="1.0",
                domain="finance",
                complexity=ComplexityLevel.L1,
                question_text={"en": "Q3"},
                golden_sql="SELECT 3",
                dependencies={},
                tags=["join"]
            ),
        ]

        loader = QuestionLoader()
        stats = loader.get_statistics(questions)

        assert stats["total"] == 3
        assert stats["by_domain"] == {"ecommerce": 2, "finance": 1}
        assert stats["by_complexity"] == {"L1": 2, "L2": 1}
        assert stats["by_tags"] == {"basic": 2, "select": 1, "aggregation": 1, "join": 1}
