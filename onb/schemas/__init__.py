"""
Database schema definitions using SQLAlchemy ORM.

This module provides:
- Declarative base for all models
- Schema definitions for different business scenarios
- DDL generation utilities for multiple databases

Supported scenarios:
- ecommerce: Complete e-commerce company schema (120+ tables)
"""

from onb.schemas.base import Base, metadata

__all__ = ["Base", "metadata"]
