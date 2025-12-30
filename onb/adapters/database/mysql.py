"""
MySQL database adapter implementation.

This module provides a MySQL-specific implementation of the DatabaseAdapter.
"""

from typing import Any, List
from urllib.parse import quote_plus

import numpy as np
import pandas as pd
from sqlalchemy import text

from onb.adapters.database.base import DatabaseAdapter
from onb.core.types import DatabaseType


class MySQLAdapter(DatabaseAdapter):
    """MySQL database adapter."""

    @property
    def database_type(self) -> DatabaseType:
        """Get database type."""
        return DatabaseType.MYSQL

    def _build_connection_string(self) -> str:
        """Build MySQL connection string."""
        # URL-encode username and password to handle special characters
        user = quote_plus(self.config.user)
        password = quote_plus(self.config.password)

        # Use PyMySQL driver with charset
        conn_str = (
            f"mysql+pymysql://{user}:{password}"
            f"@{self.config.host}:{self.config.port}/{self.config.database}"
            "?charset=utf8mb4"
        )

        # Add SSL parameter if enabled
        if self.config.ssl:
            conn_str += "&ssl=true"

        return conn_str

    def _set_query_timeout(self, connection: Any, timeout_ms: int) -> None:
        """Set query timeout for MySQL connection."""
        # MySQL uses max_execution_time in milliseconds (MySQL 5.7.8+)
        timeout_seconds = max(1, timeout_ms // 1000)
        try:
            connection.execute(
                text(f"SET SESSION max_execution_time = {timeout_ms}")
            )
        except Exception:
            # Fallback for older MySQL versions
            pass

    def normalize_result(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize MySQL result DataFrame.

        Handles:
        - DECIMAL -> float64 conversion
        - DATETIME -> datetime64 conversion
        - Column name normalization (lowercase)
        - NULL handling
        """
        if df.empty:
            return df

        # Create a copy to avoid modifying the original
        normalized = df.copy()

        # Normalize column names (lowercase)
        normalized.columns = [col.lower() for col in normalized.columns]

        # Type conversions
        for col in normalized.columns:
            dtype = normalized[col].dtype

            # Convert object columns that might be DECIMAL
            if dtype == object:
                try:
                    # Try to convert to numeric (handles DECIMAL)
                    normalized[col] = pd.to_numeric(normalized[col], errors="ignore")
                except Exception:
                    pass

            # Handle datetime columns
            if pd.api.types.is_datetime64_any_dtype(normalized[col]):
                # Ensure timezone-aware (convert to UTC if not already)
                if normalized[col].dt.tz is None:
                    normalized[col] = normalized[col].dt.tz_localize("UTC")
                else:
                    normalized[col] = normalized[col].dt.tz_convert("UTC")

            # Convert None/NaN to standard pd.NA
            if dtype == object:
                normalized[col] = normalized[col].replace({None: pd.NA})

        return normalized

    def _get_version_query(self) -> str:
        """Get MySQL version query."""
        return "SELECT VERSION()"

    def _get_supported_features(self) -> List[str]:
        """Get list of supported SQL features in MySQL."""
        return [
            "WINDOW_FUNCTIONS",  # MySQL 8.0+
            "CTE",  # Common Table Expressions (MySQL 8.0+)
            "JSON_FUNCTIONS",
            "FULL_TEXT_SEARCH",
            "SPATIAL_INDEX",
            "STORED_PROCEDURES",
            "TRIGGERS",
            "VIEWS",
            "SUBQUERIES",
            "UNION",
            "JOINS",
            "AGGREGATIONS",
            "GROUP_BY",
            "HAVING",
            "ORDER_BY",
            "LIMIT",
        ]

    def _get_table_row_count(self, table_name: str, database_name: str) -> int:
        """
        Get approximate row count for MySQL table.

        Uses INFORMATION_SCHEMA for faster approximate count.
        """
        try:
            # Try fast approximate count first
            sql = f"""
                SELECT TABLE_ROWS
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = '{database_name}'
                AND TABLE_NAME = '{table_name}'
            """
            df = self.execute_query(sql)
            if not df.empty and df.iloc[0, 0] is not None:
                return int(df.iloc[0, 0])
        except Exception:
            pass

        # Fallback to exact count
        return super()._get_table_row_count(table_name, database_name)
