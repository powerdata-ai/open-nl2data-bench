"""
Base database adapter interface.

This module defines the abstract base class for all database adapters.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from onb.core.exceptions import (
    ConnectionError,
    QueryExecutionError,
    SchemaNotFoundError,
    TableNotFoundError,
)
from onb.core.types import (
    ColumnInfo,
    DatabaseConfig,
    DatabaseType,
    IndexInfo,
    SchemaInfo,
    TableInfo,
)


class DatabaseAdapter(ABC):
    """Abstract base class for database adapters."""

    def __init__(self, config: DatabaseConfig):
        """
        Initialize database adapter.

        Args:
            config: Database connection configuration
        """
        self.config = config
        self._engine: Optional[Engine] = None
        self._connected = False

    @property
    @abstractmethod
    def database_type(self) -> DatabaseType:
        """Get database type."""
        pass

    def connect(self) -> None:
        """Establish database connection."""
        if self._connected:
            return

        try:
            connection_string = self._build_connection_string()
            self._engine = create_engine(
                connection_string,
                **self._get_engine_params(),
            )
            # Test connection
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            self._connected = True
        except SQLAlchemyError as e:
            raise ConnectionError(f"Failed to connect to {self.database_type}: {e}")

    def disconnect(self) -> None:
        """Close database connection."""
        if self._engine:
            self._engine.dispose()
            self._connected = False
            self._engine = None

    def __enter__(self) -> "DatabaseAdapter":
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.disconnect()

    @abstractmethod
    def _build_connection_string(self) -> str:
        """Build database-specific connection string."""
        pass

    def _get_engine_params(self) -> Dict[str, Any]:
        """Get SQLAlchemy engine parameters."""
        params = {
            "pool_size": 5,
            "max_overflow": 10,
            "pool_pre_ping": True,
            "echo": False,
        }
        params.update(self.config.connection_params)
        return params

    def execute_query(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None,
        timeout_ms: int = 30000,
    ) -> pd.DataFrame:
        """
        Execute SQL query and return results as DataFrame.

        Args:
            sql: SQL query to execute (can use :param syntax for parameters)
            params: Optional parameters for parameterized query
            timeout_ms: Query timeout in milliseconds

        Returns:
            Query results as pandas DataFrame

        Raises:
            QueryExecutionError: If query execution fails
        """
        if not self._connected or not self._engine:
            raise ConnectionError("Not connected to database")

        try:
            with self._engine.connect() as conn:
                # Set query timeout if supported
                self._set_query_timeout(conn, timeout_ms)

                # Execute query with parameters if provided
                if params:
                    result = conn.execute(text(sql), params)
                else:
                    result = conn.execute(text(sql))

                # Convert to DataFrame
                df = pd.DataFrame(result.fetchall(), columns=result.keys())

                # Normalize result
                return self.normalize_result(df)

        except SQLAlchemyError as e:
            raise QueryExecutionError(f"Query execution failed: {e}\nSQL: {sql}")

    @abstractmethod
    def _set_query_timeout(self, connection: Any, timeout_ms: int) -> None:
        """Set query timeout for the connection."""
        pass

    def get_schema_info(
        self, database_name: Optional[str] = None, include_stats: bool = False
    ) -> SchemaInfo:
        """
        Get database schema information.

        Args:
            database_name: Database name (defaults to config.database)
            include_stats: Whether to include table statistics

        Returns:
            SchemaInfo object with complete schema metadata

        Raises:
            SchemaNotFoundError: If schema is not found
        """
        if not self._connected or not self._engine:
            raise ConnectionError("Not connected to database")

        db_name = database_name or self.config.database

        try:
            inspector = inspect(self._engine)
            table_names = inspector.get_table_names(schema=db_name)

            tables = []
            for table_name in table_names:
                table_info = self._get_table_info(
                    inspector, table_name, db_name, include_stats
                )
                tables.append(table_info)

            return SchemaInfo(
                database_name=db_name,
                database_type=self.database_type,
                tables=tables,
            )

        except SQLAlchemyError as e:
            raise SchemaNotFoundError(f"Failed to get schema info for {db_name}: {e}")

    def _get_table_info(
        self,
        inspector: Any,
        table_name: str,
        database_name: str,
        include_stats: bool = False,
    ) -> TableInfo:
        """Get table metadata."""
        try:
            # Get columns
            columns = []
            for col in inspector.get_columns(table_name, schema=database_name):
                column_info = ColumnInfo(
                    name=col["name"],
                    type=str(col["type"]),
                    nullable=col["nullable"],
                    default=col.get("default"),
                    comment=col.get("comment"),
                )
                columns.append(column_info)

            # Get primary keys
            pk_constraint = inspector.get_pk_constraint(table_name, schema=database_name)
            if pk_constraint:
                pk_columns = pk_constraint.get("constrained_columns", [])
                for col in columns:
                    if col.name in pk_columns:
                        col.primary_key = True

            # Get indexes
            indexes = []
            for idx in inspector.get_indexes(table_name, schema=database_name):
                index_info = IndexInfo(
                    name=idx["name"],
                    columns=idx["column_names"],
                    unique=idx["unique"],
                )
                indexes.append(index_info)

            # Get row count if requested
            row_count = None
            if include_stats:
                row_count = self._get_table_row_count(table_name, database_name)

            return TableInfo(
                name=table_name,
                columns=columns,
                indexes=indexes,
                row_count=row_count,
            )

        except SQLAlchemyError as e:
            raise TableNotFoundError(f"Failed to get info for table {table_name}: {e}")

    def _get_table_row_count(self, table_name: str, database_name: str) -> int:
        """Get approximate row count for table."""
        try:
            sql = f"SELECT COUNT(*) FROM `{database_name}`.`{table_name}`"
            df = self.execute_query(sql)
            return int(df.iloc[0, 0])
        except Exception:
            return 0

    @abstractmethod
    def normalize_result(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize result DataFrame for consistent comparison.

        This handles:
        - Type conversion (DECIMAL -> float64, DATETIME -> datetime64)
        - Column name normalization
        - NULL value handling
        - Timezone conversion

        Args:
            df: Raw result DataFrame

        Returns:
            Normalized DataFrame
        """
        pass

    def get_database_version(self) -> str:
        """Get database version string."""
        if not self._connected or not self._engine:
            raise ConnectionError("Not connected to database")

        try:
            version_query = self._get_version_query()
            df = self.execute_query(version_query)
            return str(df.iloc[0, 0])
        except Exception as e:
            return f"Unknown ({e})"

    @abstractmethod
    def _get_version_query(self) -> str:
        """Get database-specific version query."""
        pass

    def supports_feature(self, feature: str) -> bool:
        """
        Check if database supports a specific SQL feature.

        Args:
            feature: Feature name (e.g., "WINDOW_FUNCTIONS", "CTE")

        Returns:
            True if feature is supported
        """
        supported = self._get_supported_features()
        return feature in supported

    @abstractmethod
    def _get_supported_features(self) -> List[str]:
        """Get list of supported SQL features."""
        pass
