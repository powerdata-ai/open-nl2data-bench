"""
SUT (System Under Test) adapters for OpenNL2SQL-Bench.

This module provides adapters for connecting to different NL2SQL systems.
"""

from onb.adapters.sut.base import SUTAdapter
from onb.adapters.sut.http import HTTPSUTAdapter
from onb.adapters.sut.mock import MockSUTAdapter

__all__ = ["SUTAdapter", "HTTPSUTAdapter", "MockSUTAdapter"]
