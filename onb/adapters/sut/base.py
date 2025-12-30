"""
Base SUT (System Under Test) adapter interface.

This module defines the abstract base class for all SUT adapters.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import pandas as pd

from onb.core.types import NL2SQLResponse, SchemaInfo, SUTConfig


class SUTAdapter(ABC):
    """Abstract base class for SUT adapters."""

    def __init__(self, config: SUTConfig):
        """
        Initialize SUT adapter.

        Args:
            config: SUT configuration
        """
        self.config = config
        self._initialized = False

    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize the SUT adapter.

        This may include establishing connections, loading models,
        or other setup tasks.

        Raises:
            SUTAdapterError: If initialization fails
        """
        pass

    @abstractmethod
    def query(
        self,
        question: str,
        schema: SchemaInfo,
        language: str = "zh",
        **kwargs: Any,
    ) -> NL2SQLResponse:
        """
        Execute NL2SQL query against the SUT.

        Args:
            question: Natural language question
            schema: Database schema information
            language: Question language (zh/en)
            **kwargs: Additional adapter-specific parameters

        Returns:
            NL2SQLResponse with generated SQL and results

        Raises:
            SUTAdapterError: If query execution fails
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """
        Clean up adapter resources.

        This may include closing connections, releasing resources, etc.
        """
        pass

    def __enter__(self) -> "SUTAdapter":
        """Context manager entry."""
        self.initialize()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.cleanup()

    @property
    def name(self) -> str:
        """Get SUT adapter name."""
        return self.config.name

    @property
    def version(self) -> str:
        """Get SUT adapter version."""
        return self.config.version

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get adapter metadata.

        Returns:
            Dictionary with adapter information
        """
        return {
            "name": self.name,
            "version": self.version,
            "type": self.config.type,
            "initialized": self._initialized,
        }
