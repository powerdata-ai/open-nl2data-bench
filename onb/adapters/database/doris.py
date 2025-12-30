"""
Apache Doris database adapter for OpenNL2Data-Bench.

This adapter provides Doris-specific implementations for database operations.
Apache Doris is a high-performance, real-time analytical database based on MPP architecture.
It is compatible with MySQL protocol.
"""

from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from onb.adapters.database.base import DatabaseAdapter
from onb.core.exceptions import ConnectionError, QueryExecutionError
from onb.core.types import DatabaseConfig, DatabaseType


class DorisAdapter(DatabaseAdapter):
    """Apache Doris database adapter implementation."""

    def __init__(self, config: DatabaseConfig):
        """
        Initialize Doris adapter.

        Args:
            config: Database configuration
        """
        super().__init__(config)

        if config.type != DatabaseType.DORIS:
            raise ValueError(
                f"Invalid database type: {config.type}. "
                "DorisAdapter requires DatabaseType.DORIS"
            )

    @property
    def database_type(self) -> DatabaseType:
        """Get database type."""
        return DatabaseType.DORIS

    def _build_connection_string(self) -> str:
        """
        Build Doris connection string.

        Doris is compatible with MySQL protocol, so we use the MySQL driver.

        Returns:
            SQLAlchemy connection string for Doris

        Format:
            mysql+pymysql://user:password@host:port/database?charset=utf8mb4
        """
        # URL-encode username and password to handle special characters
        user = quote_plus(self.config.user)
        password = quote_plus(self.config.password)

        # Default Doris MySQL protocol port is 9030
        port = self.config.port or 9030

        # Build base connection string using MySQL driver
        conn_str = (
            f"mysql+pymysql://{user}:{password}"
            f"@{self.config.host}:{port}/{self.config.database}"
        )

        # Add query parameters
        params = []

        # Character set (UTF-8)
        params.append("charset=utf8mb4")

        # SSL configuration
        if self.config.ssl:
            params.append("ssl_disabled=false")
        else:
            params.append("ssl_disabled=true")

        if params:
            conn_str += "?" + "&".join(params)

        return conn_str

    def normalize_result(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize Doris query results to standard format.

        Handles Doris-specific data types:
        - BITMAP -> binary or string representation
        - HLL (HyperLogLog) -> binary or string representation
        - ARRAY -> list (Doris 2.0+)
        - JSON -> dict or string
        - DECIMAL -> float
        - DATETIME -> datetime64

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

            # Handle numeric types (DECIMAL, INT, BIGINT, etc.)
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

            # Handle ARRAY columns (Doris 2.0+)
            if dtype == object:
                sample = normalized[col].iloc[0] if len(normalized) > 0 else None
                if isinstance(sample, list):
                    # Keep as list for compatibility
                    pass

            # Handle JSON columns
            if dtype == object:
                sample = normalized[col].iloc[0] if len(normalized) > 0 else None
                if isinstance(sample, dict):
                    # Keep as dict or convert to JSON string for strict comparison
                    import json
                    normalized[col] = normalized[col].apply(
                        lambda x: json.dumps(x) if isinstance(x, dict) else x
                    )

            # Handle binary data (BITMAP, HLL)
            if dtype == object:
                sample = normalized[col].iloc[0] if len(normalized) > 0 else None
                if isinstance(sample, (bytes, bytearray)):
                    # Convert binary to hex string for comparison
                    normalized[col] = normalized[col].apply(
                        lambda x: x.hex() if isinstance(x, (bytes, bytearray)) else x
                    )

        # Lowercase column names for consistency
        normalized.columns = normalized.columns.str.lower()

        return normalized

    def get_database_version(self) -> str:
        """
        Get Doris server version.

        Returns:
            Version string (e.g., "Doris 2.0.3")
        """
        if not self._connected or not self._engine:
            raise ConnectionError("Not connected to database")

        try:
            with self._engine.connect() as conn:
                result = conn.execute(text("SELECT VERSION()"))
                version = result.scalar()
                # Doris returns version like: "5.7.99 Doris version 2.0.3-rc01"
                if "Doris" in version:
                    return version
                return f"Doris {version}"

        except SQLAlchemyError as e:
            raise QueryExecutionError(f"Failed to get database version: {e}")

    def _configure_engine_options(self) -> Dict[str, Any]:
        """
        Configure Doris-specific engine options.

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
        Get Doris adapter metadata.

        Returns:
            Dictionary with adapter information
        """
        metadata = {
            "name": "Apache Doris Adapter",
            "database_type": self.database_type.value,
            "driver": "pymysql",
            "protocol": "mysql",
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
        Set query timeout for Doris connection.

        Args:
            connection: SQLAlchemy connection object
            timeout_ms: Timeout in milliseconds
        """
        # Doris uses query_timeout in seconds (session variable)
        timeout_seconds = timeout_ms / 1000
        connection.execute(
            text(f"SET query_timeout = {int(timeout_seconds)}")
        )

    def _get_version_query(self) -> str:
        """
        Get Doris version query.

        Returns:
            SQL query to get database version
        """
        return "SELECT VERSION()"

    def _get_supported_features(self) -> List[str]:
        """
        Get list of supported Doris features.

        Returns:
            List of supported SQL features
        """
        return [
            "JOIN",
            "INNER JOIN",
            "LEFT JOIN",
            "RIGHT JOIN",
            "FULL OUTER JOIN",
            "CROSS JOIN",
            "SEMI JOIN",
            "ANTI JOIN",
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
            "CTE",  # WITH clause
            "SUBQUERY",
            "CASE",
            "CAST",
            "ARRAY",  # Doris 2.0+
            "JSON",
            "BITMAP",  # Doris-specific
            "HLL",  # HyperLogLog for approximate counting
            "MATERIALIZED VIEW",
            "ROLLUP",  # Pre-aggregation
            "PARTITION",  # Table partitioning
            "BUCKET",  # Data distribution
            "COLOCATE JOIN",  # Optimized distributed join
        ]

    def _get_table_row_count(self, table_name: str, database_name: str) -> int:
        """
        Get approximate row count for Doris table.

        Uses INFORMATION_SCHEMA for faster approximate count.

        Args:
            table_name: Table name
            database_name: Database name

        Returns:
            Approximate row count
        """
        try:
            # Try fast approximate count from INFORMATION_SCHEMA
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
