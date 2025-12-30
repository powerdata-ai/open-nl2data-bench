"""
Custom exceptions for OpenNL2SQL-Bench.

This module defines all custom exceptions used throughout the benchmark framework.
"""


class ONBException(Exception):
    """Base exception for all OpenNL2SQL-Bench exceptions."""

    pass


# ============================================================================
# Configuration Exceptions
# ============================================================================


class ConfigError(ONBException):
    """Raised when configuration is invalid or missing."""

    pass


class InvalidConfigError(ConfigError):
    """Raised when configuration validation fails."""

    pass


class MissingConfigError(ConfigError):
    """Raised when required configuration is missing."""

    pass


# ============================================================================
# Database Exceptions
# ============================================================================


class DatabaseError(ONBException):
    """Base exception for database-related errors."""

    pass


class ConnectionError(DatabaseError):
    """Raised when database connection fails."""

    pass


class QueryExecutionError(DatabaseError):
    """Raised when SQL query execution fails."""

    pass


class SchemaNotFoundError(DatabaseError):
    """Raised when database schema is not found."""

    pass


class TableNotFoundError(DatabaseError):
    """Raised when table is not found in schema."""

    pass


# ============================================================================
# SUT Adapter Exceptions
# ============================================================================


class SUTAdapterError(ONBException):
    """Base exception for SUT adapter errors."""

    pass


class SUTConnectionError(SUTAdapterError):
    """Raised when connection to SUT fails."""

    pass


class SUTTimeoutError(SUTAdapterError):
    """Raised when SUT request times out."""

    pass


class SUTResponseError(SUTAdapterError):
    """Raised when SUT response is invalid or cannot be parsed."""

    pass


class SUTAuthenticationError(SUTAdapterError):
    """Raised when SUT authentication fails."""

    pass


# ============================================================================
# Question Bank Exceptions
# ============================================================================


class QuestionBankError(ONBException):
    """Base exception for question bank errors."""

    pass


class QuestionNotFoundError(QuestionBankError):
    """Raised when question is not found."""

    pass


class InvalidQuestionError(QuestionBankError):
    """Raised when question definition is invalid."""

    pass


class GoldenAnswerNotFoundError(QuestionBankError):
    """Raised when golden answer is not found."""

    pass


class DependencyNotMetError(QuestionBankError):
    """Raised when question dependencies are not met."""

    pass


# ============================================================================
# Evaluation Exceptions
# ============================================================================


class EvaluationError(ONBException):
    """Base exception for evaluation errors."""

    pass


class ComparisonError(EvaluationError):
    """Raised when result set comparison fails."""

    pass


class SchemaMatchError(ComparisonError):
    """Raised when result set schemas don't match."""

    pass


class DataTypeMatchError(ComparisonError):
    """Raised when data types don't match."""

    pass


# ============================================================================
# Data Generation Exceptions
# ============================================================================


class DataGenerationError(ONBException):
    """Base exception for data generation errors."""

    pass


class InvalidSchemaDefinitionError(DataGenerationError):
    """Raised when schema definition is invalid."""

    pass


class DataGenerationFailedError(DataGenerationError):
    """Raised when data generation fails."""

    pass


# ============================================================================
# Validation Exceptions
# ============================================================================


class ValidationError(ONBException):
    """Base exception for validation errors."""

    pass


class JSONPathExtractionError(ValidationError):
    """Raised when JSONPath extraction fails."""

    pass


class DataIntegrityError(ValidationError):
    """Raised when data integrity check fails."""

    pass


class FraudDetectionError(ValidationError):
    """Raised when fraud is detected in test results."""

    pass


# ============================================================================
# File I/O Exceptions
# ============================================================================


class FileError(ONBException):
    """Base exception for file I/O errors."""

    pass


class FileNotFoundError(FileError):
    """Raised when file is not found."""

    pass


class FileFormatError(FileError):
    """Raised when file format is invalid."""

    pass


class FileWriteError(FileError):
    """Raised when file write operation fails."""

    pass
