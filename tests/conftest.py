"""Test utilities and fixtures."""
import pytest


@pytest.fixture
def sample_database_config():
    """Sample database configuration for testing."""
    from onb.core.types import DatabaseConfig, DatabaseType

    return DatabaseConfig(
        type=DatabaseType.MYSQL,
        host="localhost",
        port=3306,
        user="test_user",
        password="test_password",
        database="test_db",
    )


@pytest.fixture
def sample_schema_info():
    """Sample schema information for testing."""
    from onb.core.types import (
        ColumnInfo,
        DatabaseType,
        QualityLevel,
        SchemaInfo,
        TableInfo,
    )

    columns = [
        ColumnInfo(
            name="user_id",
            type="BIGINT",
            nullable=False,
            primary_key=True,
            comment="用户ID",
        ),
        ColumnInfo(
            name="username",
            type="VARCHAR(100)",
            nullable=False,
            comment="用户名",
        ),
        ColumnInfo(
            name="created_at",
            type="DATETIME",
            nullable=False,
            comment="创建时间",
        ),
    ]

    table = TableInfo(name="users", columns=columns, quality=QualityLevel.HIGH)

    return SchemaInfo(
        database_name="test_db",
        database_type=DatabaseType.MYSQL,
        tables=[table],
    )


@pytest.fixture
def sample_question():
    """Sample test question for testing."""
    from onb.core.types import ComplexityLevel, Question

    return Question(
        id="test_L1_001",
        version="1.0",
        domain="test",
        complexity=ComplexityLevel.L1,
        question_text={"en": "Select all users", "zh": "查询所有用户"},
        golden_sql="SELECT * FROM users",
        dependencies={"tables": ["users"], "features": ["SELECT"]},
        tags=["basic", "select"],
    )
