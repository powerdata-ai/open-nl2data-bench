"""
Base classes and metadata for SQLAlchemy schema definitions.

This module provides:
- Declarative base with standardized naming conventions
- Common mixins for timestamps and soft deletes
- Type annotations for better IDE support
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import MetaData, SmallInteger
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# Standardized naming conventions for constraints and indexes
# This ensures consistent naming across all databases
convention = {
    "ix": "idx_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=convention)


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.

    Features:
    - Standardized constraint naming
    - Type annotations support
    - Declarative configuration
    """

    metadata = metadata


class TimestampMixin:
    """
    Mixin for created_at and updated_at timestamp columns.

    Usage:
        class MyModel(Base, TimestampMixin):
            __tablename__ = "my_table"
            id: Mapped[int] = mapped_column(primary_key=True)
    """

    created_at: Mapped[datetime] = mapped_column(
        default=datetime.now, comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.now,
        onupdate=datetime.now,
        comment="更新时间",
    )


class SoftDeleteMixin:
    """
    Mixin for soft delete functionality.

    Usage:
        class MyModel(Base, SoftDeleteMixin):
            __tablename__ = "my_table"
            id: Mapped[int] = mapped_column(primary_key=True)
    """

    is_deleted: Mapped[int] = mapped_column(
        SmallInteger, default=0, comment="删除标记：0未删除/1已删除"
    )
