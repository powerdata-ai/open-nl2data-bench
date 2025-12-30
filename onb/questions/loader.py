"""
Question loader for OpenNL2SQL-Bench.

This module provides functionality to load and manage test questions
from YAML files.
"""

from pathlib import Path
from typing import Dict, List, Optional

import yaml

from onb.core.exceptions import InvalidConfigError, MissingConfigError
from onb.core.types import ComplexityLevel, ComparisonRules, Question, QualityLevel


class QuestionLoader:
    """Loader for test questions from YAML files."""

    def __init__(self):
        """Initialize question loader."""
        self._cache: Dict[str, Question] = {}

    def load_question(self, file_path: Path) -> Question:
        """
        Load a single question from YAML file.

        Args:
            file_path: Path to question YAML file

        Returns:
            Question object

        Raises:
            MissingConfigError: If file not found
            InvalidConfigError: If YAML is invalid or missing required fields
        """
        if not file_path.exists():
            raise MissingConfigError(f"Question file not found: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data:
                raise InvalidConfigError(f"Empty question file: {file_path}")

            # Parse and validate question
            question = self._parse_question(data, file_path)

            # Cache the question
            self._cache[question.id] = question

            return question

        except yaml.YAMLError as e:
            raise InvalidConfigError(f"Invalid YAML in {file_path}: {e}")
        except KeyError as e:
            raise InvalidConfigError(
                f"Missing required field in {file_path}: {e}"
            )
        except Exception as e:
            raise InvalidConfigError(f"Failed to load question from {file_path}: {e}")

    def load_questions(
        self, directory: Path, pattern: str = "*.yaml"
    ) -> List[Question]:
        """
        Load all questions from a directory.

        Args:
            directory: Directory containing question files
            pattern: Glob pattern for question files (default: *.yaml)

        Returns:
            List of Question objects

        Raises:
            MissingConfigError: If directory not found
        """
        if not directory.exists():
            raise MissingConfigError(f"Question directory not found: {directory}")

        if not directory.is_dir():
            raise InvalidConfigError(f"Not a directory: {directory}")

        questions = []
        question_files = sorted(directory.glob(pattern))

        for file_path in question_files:
            try:
                question = self.load_question(file_path)
                questions.append(question)
            except Exception as e:
                # Log warning but continue loading other questions
                print(f"Warning: Failed to load {file_path}: {e}")
                continue

        return questions

    def filter_questions(
        self,
        questions: List[Question],
        domain: Optional[str] = None,
        complexity: Optional[List[ComplexityLevel]] = None,
        tags: Optional[List[str]] = None,
    ) -> List[Question]:
        """
        Filter questions by criteria.

        Args:
            questions: List of questions to filter
            domain: Filter by domain (e.g., "ecommerce", "finance")
            complexity: Filter by complexity levels
            tags: Filter by tags (any match)

        Returns:
            Filtered list of questions
        """
        filtered = questions

        if domain:
            filtered = [q for q in filtered if q.domain == domain]

        if complexity:
            filtered = [q for q in filtered if q.complexity in complexity]

        if tags:
            # Match if question has ANY of the specified tags
            filtered = [
                q for q in filtered if any(tag in q.tags for tag in tags)
            ]

        return filtered

    def get_question_by_id(self, question_id: str) -> Optional[Question]:
        """
        Get cached question by ID.

        Args:
            question_id: Question ID

        Returns:
            Question object if found, None otherwise
        """
        return self._cache.get(question_id)

    def clear_cache(self) -> None:
        """Clear question cache."""
        self._cache.clear()

    def _parse_question(self, data: dict, file_path: Path) -> Question:
        """
        Parse question data from dictionary.

        Args:
            data: Question data dictionary
            file_path: Source file path (for error messages)

        Returns:
            Question object

        Raises:
            InvalidConfigError: If data is invalid
        """
        try:
            # Required fields
            question_id = data["id"]
            version = data["version"]
            domain = data["domain"]
            complexity_str = data["complexity"]
            question_text = data["question"]
            golden_sql = data["golden_sql"]
            dependencies = data.get("dependencies", {})

            # Parse complexity level
            try:
                complexity = ComplexityLevel(complexity_str)
            except ValueError:
                raise InvalidConfigError(
                    f"Invalid complexity level '{complexity_str}' in {file_path}. "
                    f"Valid values: {[e.value for e in ComplexityLevel]}"
                )

            # Optional fields
            tags = data.get("tags", [])
            metadata = data.get("metadata", {})

            # Parse comparison rules if provided
            comparison_rules = None
            if "comparison_rules" in data:
                comparison_rules = self._parse_comparison_rules(
                    data["comparison_rules"]
                )

            # Validate question_text format
            if not isinstance(question_text, dict):
                raise InvalidConfigError(
                    f"question_text must be a dict with language keys in {file_path}"
                )

            # Ensure at least one language is provided
            if not question_text:
                raise InvalidConfigError(
                    f"question_text must contain at least one language in {file_path}"
                )

            return Question(
                id=question_id,
                version=version,
                domain=domain,
                complexity=complexity,
                question_text=question_text,
                golden_sql=golden_sql,
                dependencies=dependencies,
                comparison_rules=comparison_rules,
                tags=tags,
                metadata=metadata,
            )

        except KeyError as e:
            raise InvalidConfigError(
                f"Missing required field {e} in question file {file_path}"
            )

    def _parse_comparison_rules(self, rules_data: dict) -> ComparisonRules:
        """
        Parse comparison rules from dictionary.

        Args:
            rules_data: Comparison rules data

        Returns:
            ComparisonRules object
        """
        return ComparisonRules(
            row_order_matters=rules_data.get("row_order_matters", True),
            column_order_matters=rules_data.get("column_order_matters", True),
            float_tolerance=rules_data.get("float_tolerance", 1e-6),
            float_comparison_mode=rules_data.get(
                "float_comparison_mode", "relative_error"
            ),
            null_handling=rules_data.get("null_handling", "strict"),
            string_normalization=rules_data.get("string_normalization", "trim"),
            string_case_sensitive=rules_data.get("string_case_sensitive", False),
            datetime_normalize_timezone=rules_data.get(
                "datetime_normalize_timezone", True
            ),
            datetime_tolerance_ms=rules_data.get("datetime_tolerance_ms", 0),
        )

    def get_statistics(self, questions: List[Question]) -> Dict[str, any]:
        """
        Get statistics about loaded questions.

        Args:
            questions: List of questions

        Returns:
            Dictionary with statistics
        """
        if not questions:
            return {
                "total": 0,
                "by_domain": {},
                "by_complexity": {},
                "by_tags": {},
            }

        # Count by domain
        by_domain = {}
        for q in questions:
            by_domain[q.domain] = by_domain.get(q.domain, 0) + 1

        # Count by complexity
        by_complexity = {}
        for q in questions:
            level = q.complexity.value
            by_complexity[level] = by_complexity.get(level, 0) + 1

        # Count by tags
        by_tags = {}
        for q in questions:
            for tag in q.tags:
                by_tags[tag] = by_tags.get(tag, 0) + 1

        return {
            "total": len(questions),
            "by_domain": by_domain,
            "by_complexity": by_complexity,
            "by_tags": by_tags,
        }
