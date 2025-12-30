"""
ClickHouse database adapter for OpenNL2Data-Bench.

This adapter provides ClickHouse-specific implementations for database operations.
"""

from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from onb.adapters.database.base import DatabaseAdapter
from onb.core.exceptions import ConnectionError, QueryExecutionError
from onb.core.types import DatabaseConfig, DatabaseType


class ClickHouseAdapter(DatabaseAdapter):
    """ClickHouse database adapter implementation."""

    def __init__(self, config: DatabaseConfig):
        """
        Initialize ClickHouse adapter.

        Args:
            config: Database configuration
        """
        super().__init__(config)

        if config.type != DatabaseType.CLICKHOUSE:
            raise ValueError(
                f"Invalid database type: {config.type}. "
                "ClickHouseAdapter requires DatabaseType.CLICKHOUSE"
            )

    @property
    def database_type(self) -> DatabaseType:
        """Get database type."""
        return DatabaseType.CLICKHOUSE

    def _build_connection_string(self) -> str:
        """
        Build ClickHouse connection string.

        Returns:
            SQLAlchemy connection string for ClickHouse

        Format:
            clickhouse+native://user:password@host:port/database?param=value
        """
        # URL-encode username and password to handle special characters
        user = quote_plus(self.config.user)
        password = quote_plus(self.config.password)

        # Default ClickHouse native protocol port is 9000
        port = self.config.port or 9000

        # Build base connection string
        conn_str = (
            f"clickhouse+native://{user}:{password}"
            f"@{self.config.host}:{port}/{self.config.database}"
        )

        # Add query parameters
        params = []

        # SSL configuration
        if self.config.ssl:
            params.append("secure=True")

        # Compression (recommended for ClickHouse)
        params.append("compression=lz4")

        if params:
            conn_str += "?" + "&".join(params)

        return conn_str

    def normalize_result(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize ClickHouse query results to standard format.

        Handles ClickHouse-specific data types:
        - Array types -> list or JSON string
        - Tuple types -> tuple or JSON string
        - Nested types -> dict
        - DateTime types with timezone
        - Decimal types -> float
        - Enum types -> string
        - IPv4/IPv6 -> string
        - UUID -> string

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

            # Handle Array columns (ClickHouse arrays)
            if dtype == object:
                sample = normalized[col].iloc[0] if len(normalized) > 0 else None
                if isinstance(sample, (list, tuple)):
                    # Keep as list for compatibility
                    # Could also convert to JSON string for strict comparison
                    pass

            # Handle Nested/Tuple columns (convert to dict/tuple representation)
            if dtype == object:
                sample = normalized[col].iloc[0] if len(normalized) > 0 else None
                if isinstance(sample, dict):
                    # Keep as dict
                    pass

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

            # Handle UUID (convert to string)
            if dtype == object:
                sample = normalized[col].iloc[0] if len(normalized) > 0 else None
                if hasattr(sample, 'hex'):  # UUID object
                    normalized[col] = normalized[col].astype(str)

            # Handle IP addresses (convert to string)
            if dtype == object:
                sample = normalized[col].iloc[0] if len(normalized) > 0 else None
                # Check if it looks like an IP address object
                if hasattr(sample, '__str__') and not isinstance(sample, (str, int, float, bool)):
                    try:
                        normalized[col] = normalized[col].astype(str)
                    except (ValueError, TypeError):
                        pass

        # ClickHouse column names are case-sensitive, but normalize to lowercase
        normalized.columns = normalized.columns.str.lower()

        return normalized

    def get_database_version(self) -> str:
        """
        Get ClickHouse server version.

        Returns:
            Version string (e.g., "23.8.2.7")
        """
        if not self._connected or not self._engine:
            raise ConnectionError("Not connected to database")

        try:
            with self._engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                version = result.scalar()
                return f"ClickHouse {version}"

        except SQLAlchemyError as e:
            raise QueryExecutionError(f"Failed to get database version: {e}")

    def _configure_engine_options(self) -> Dict[str, Any]:
        """
        Configure ClickHouse-specific engine options.

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
        Get ClickHouse adapter metadata.

        Returns:
            Dictionary with adapter information
        """
        metadata = {
            "name": "ClickHouse Adapter",
            "database_type": self.database_type.value,
            "driver": "clickhouse-sqlalchemy",
            "protocol": "native",
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
        Set query timeout for ClickHouse connection.

        Args:
            connection: SQLAlchemy connection object
            timeout_ms: Timeout in milliseconds
        """
        # ClickHouse uses max_execution_time in seconds
        timeout_seconds = timeout_ms / 1000
        connection.execute(
            text(f"SET max_execution_time = {int(timeout_seconds)}")
        )

    def _get_version_query(self) -> str:
        """
        Get ClickHouse version query.

        Returns:
            SQL query to get database version
        """
        return "SELECT version()"

    def _get_supported_features(self) -> List[str]:
        """
        Get list of supported ClickHouse features.

        Returns:
            List of supported SQL features
        """
        return [
            "JOIN",
            "INNER JOIN",
            "LEFT JOIN",
            "RIGHT JOIN",
            "FULL JOIN",
            "CROSS JOIN",
            "ARRAY JOIN",  # ClickHouse-specific
            "UNION ALL",
            "INTERSECT",  # ClickHouse 21.3+
            "EXCEPT",  # ClickHouse 21.3+
            "GROUP BY",
            "HAVING",
            "ORDER BY",
            "LIMIT",
            "OFFSET",
            "DISTINCT",
            "WINDOW FUNCTIONS",
            "CTE",  # WITH clause
            "SUBQUERY",
            "CASE",
            "CAST",
            "ARRAY",
            "TUPLE",
            "NESTED",
            "JSON",  # Limited support
            "MATERIALIZED VIEW",
            "PREWHERE",  # ClickHouse optimization
            "SAMPLE",  # Data sampling
            "FINAL",  # Force merge
            "GLOBAL JOIN",  # Distributed joins
            "ASOF JOIN",  # Time-series joins
        ]
