"""
PostgreSQL database adapter for OpenNL2Data-Bench.

This adapter provides PostgreSQL-specific implementations for database operations.
"""

from typing import Any, Dict, Optional
from urllib.parse import quote_plus

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from onb.adapters.database.base import DatabaseAdapter
from onb.core.exceptions import ConnectionError, QueryExecutionError
from onb.core.types import DatabaseConfig, DatabaseType


class PostgreSQLAdapter(DatabaseAdapter):
    """PostgreSQL database adapter implementation."""

    def __init__(self, config: DatabaseConfig):
        """
        Initialize PostgreSQL adapter.

        Args:
            config: Database configuration
        """
        super().__init__(config)

        if config.type != DatabaseType.POSTGRESQL:
            raise ValueError(
                f"Invalid database type: {config.type}. "
                "PostgreSQLAdapter requires DatabaseType.POSTGRESQL"
            )

    @property
    def database_type(self) -> DatabaseType:
        """Get database type."""
        return DatabaseType.POSTGRESQL

    def _build_connection_string(self) -> str:
        """
        Build PostgreSQL connection string.

        Returns:
            SQLAlchemy connection string for PostgreSQL

        Format:
            postgresql+psycopg2://user:password@host:port/database?param=value
        """
        # URL-encode username and password to handle special characters
        user = quote_plus(self.config.user)
        password = quote_plus(self.config.password)

        # Build base connection string
        conn_str = (
            f"postgresql+psycopg2://{user}:{password}"
            f"@{self.config.host}:{self.config.port}/{self.config.database}"
        )

        # Add query parameters
        params = []

        # SSL mode
        if self.config.ssl:
            params.append("sslmode=require")
        else:
            params.append("sslmode=prefer")  # Try SSL, but allow fallback

        # Client encoding (ensure UTF-8)
        params.append("client_encoding=utf8")

        # Application name for monitoring
        params.append("application_name=open-nl2data-bench")

        if params:
            conn_str += "?" + "&".join(params)

        return conn_str

    def normalize_result(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize PostgreSQL query results to standard format.

        Handles PostgreSQL-specific data types:
        - UUID -> string
        - ARRAY -> string representation
        - JSON/JSONB -> string
        - INTERVAL -> string
        - Numeric types with proper conversion
        - Timezone-aware datetime

        Args:
            df: Raw query result DataFrame

        Returns:
            Normalized DataFrame
        """
        if df.empty:
            return df

        normalized = df.copy()

        for col in normalized.columns:
            # Get column dtype
            dtype = normalized[col].dtype

            # Handle UUID columns (convert to string)
            if dtype == object:
                # Check if it's UUID by trying to access uuid attribute
                if hasattr(normalized[col].iloc[0] if len(normalized) > 0 else None, 'hex'):
                    normalized[col] = normalized[col].astype(str)

            # Handle ARRAY columns (PostgreSQL arrays)
            if dtype == object:
                sample = normalized[col].iloc[0] if len(normalized) > 0 else None
                if isinstance(sample, list):
                    # Convert array to JSON string for consistency
                    import json
                    normalized[col] = normalized[col].apply(
                        lambda x: json.dumps(x) if isinstance(x, list) else x
                    )

            # Handle JSON/JSONB columns
            if dtype == object:
                sample = normalized[col].iloc[0] if len(normalized) > 0 else None
                if isinstance(sample, dict):
                    import json
                    normalized[col] = normalized[col].apply(
                        lambda x: json.dumps(x) if isinstance(x, dict) else x
                    )

            # Handle numeric types
            if pd.api.types.is_numeric_dtype(dtype):
                # Try to convert to numeric, preserving precision
                try:
                    normalized[col] = pd.to_numeric(normalized[col])
                except (ValueError, TypeError):
                    pass

            # Handle datetime columns
            if pd.api.types.is_datetime64_any_dtype(dtype):
                # Ensure timezone awareness
                if normalized[col].dt.tz is None:
                    # Assume UTC if no timezone
                    normalized[col] = normalized[col].dt.tz_localize('UTC')
                else:
                    # Convert to UTC
                    normalized[col] = normalized[col].dt.tz_convert('UTC')

            # Handle INTERVAL type (convert to string)
            if dtype == object:
                sample = normalized[col].iloc[0] if len(normalized) > 0 else None
                if hasattr(sample, 'total_seconds'):  # timedelta
                    normalized[col] = normalized[col].astype(str)

        # Lowercase column names (PostgreSQL convention)
        normalized.columns = normalized.columns.str.lower()

        return normalized

    def get_database_version(self) -> str:
        """
        Get PostgreSQL server version.

        Returns:
            Version string (e.g., "PostgreSQL 14.5")
        """
        if not self._connected or not self._engine:
            raise ConnectionError("Not connected to database")

        try:
            with self._engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                version = result.scalar()
                return version.split(',')[0]  # Get first part before comma

        except SQLAlchemyError as e:
            raise QueryExecutionError(f"Failed to get database version: {e}")

    def _configure_engine_options(self) -> Dict[str, Any]:
        """
        Configure PostgreSQL-specific engine options.

        Returns:
            Dictionary of engine configuration options
        """
        options = {
            "pool_size": 5,
            "max_overflow": 10,
            "pool_timeout": 30,
            "pool_recycle": 3600,  # Recycle connections after 1 hour
            "pool_pre_ping": True,  # Verify connections before using
            "echo": False,  # Set to True for SQL logging
        }

        return options

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get PostgreSQL adapter metadata.

        Returns:
            Dictionary with adapter information
        """
        metadata = {
            "name": "PostgreSQL Adapter",
            "database_type": self.database_type.value,
            "driver": "psycopg2",
            "ssl_enabled": self.config.ssl,
            "connected": self._connected,
        }

        if self._connected:
            try:
                metadata["server_version"] = self.get_database_version()
            except Exception:
                pass

        return metadata

    def _set_query_timeout(self, connection: Any, timeout_ms: int) -> None:
        """
        Set query timeout for PostgreSQL connection.

        Args:
            connection: SQLAlchemy connection object
            timeout_ms: Timeout in milliseconds
        """
        # PostgreSQL uses statement_timeout in milliseconds
        timeout_seconds = timeout_ms / 1000
        connection.execute(text(f"SET statement_timeout = '{int(timeout_seconds * 1000)}'"))

    def _get_version_query(self) -> str:
        """
        Get PostgreSQL version query.

        Returns:
            SQL query to get database version
        """
        return "SELECT version()"

    def _get_supported_features(self) -> list:
        """
        Get list of supported PostgreSQL features.

        Returns:
            List of supported SQL features
        """
        return [
            "JOIN",
            "LEFT JOIN",
            "RIGHT JOIN",
            "FULL JOIN",
            "CROSS JOIN",
            "UNION",
            "UNION ALL",
            "INTERSECT",
            "EXCEPT",
            "GROUP BY",
            "HAVING",
            "ORDER BY",
            "LIMIT",
            "OFFSET",
            "DISTINCT",
            "WINDOW FUNCTIONS",
            "CTE",  # Common Table Expressions (WITH clause)
            "RECURSIVE CTE",
            "SUBQUERY",
            "CASE",
            "CAST",
            "JSON",
            "JSONB",
            "ARRAY",
            "FULL TEXT SEARCH",
            "REGEXP",
            "LATERAL JOIN",
        ]
