"""
Performance profiling and benchmarking module for OpenNL2Data-Bench.

This module provides comprehensive performance evaluation including:
- Execution time measurement
- Throughput calculation
- Latency percentiles (P50, P95, P99)
- Concurrent performance testing
- Performance regression detection
"""

import statistics
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

import numpy as np

from onb.core.types import PerformanceMetrics


@dataclass
class PerformanceSample:
    """Single performance measurement sample."""

    total_time_ms: float
    nl2sql_time_ms: Optional[float] = None
    sql_generation_time_ms: Optional[float] = None
    sql_execution_time_ms: Optional[float] = None
    timestamp: float = field(default_factory=time.time)
    success: bool = True
    error: Optional[str] = None


class PerformanceProfiler:
    """
    Performance profiler for measuring and analyzing system performance.

    Supports:
    - Single query profiling
    - Batch query profiling
    - Percentile calculations (P50, P95, P99)
    - Statistical analysis
    """

    def __init__(self, warmup_iterations: int = 0):
        """
        Initialize performance profiler.

        Args:
            warmup_iterations: Number of warmup iterations to discard
        """
        self.warmup_iterations = warmup_iterations
        self.samples: List[PerformanceSample] = []
        self.warmup_samples: List[PerformanceSample] = []

    def measure(
        self,
        func: Callable,
        *args: Any,
        iterations: int = 1,
        **kwargs: Any,
    ) -> PerformanceMetrics:
        """
        Measure performance of a function.

        Args:
            func: Function to measure
            *args: Positional arguments for function
            iterations: Number of iterations to run
            **kwargs: Keyword arguments for function

        Returns:
            Performance metrics
        """
        # Warmup
        for _ in range(self.warmup_iterations):
            try:
                start = time.perf_counter()
                func(*args, **kwargs)
                end = time.perf_counter()
                elapsed_ms = (end - start) * 1000
                self.warmup_samples.append(
                    PerformanceSample(total_time_ms=elapsed_ms, success=True)
                )
            except Exception as e:
                self.warmup_samples.append(
                    PerformanceSample(
                        total_time_ms=0, success=False, error=str(e)
                    )
                )

        # Actual measurements
        for _ in range(iterations):
            try:
                start = time.perf_counter()
                result = func(*args, **kwargs)
                end = time.perf_counter()
                elapsed_ms = (end - start) * 1000

                # Try to extract detailed timings if available
                sample = PerformanceSample(total_time_ms=elapsed_ms, success=True)

                if hasattr(result, "time_ms"):
                    sample.nl2sql_time_ms = result.time_ms

                self.samples.append(sample)

            except Exception as e:
                self.samples.append(
                    PerformanceSample(
                        total_time_ms=0, success=False, error=str(e)
                    )
                )

        return self.compute_metrics()

    def add_sample(self, sample: PerformanceSample) -> None:
        """
        Add a performance sample.

        Args:
            sample: Performance sample to add
        """
        self.samples.append(sample)

    def compute_metrics(self) -> PerformanceMetrics:
        """
        Compute performance metrics from collected samples.

        Returns:
            Performance metrics
        """
        # Filter successful samples
        successful_samples = [s for s in self.samples if s.success]

        if not successful_samples:
            # Return zero metrics if no successful samples
            return PerformanceMetrics(
                median_time_ms=0,
                mean_time_ms=0,
                p50=0,
                p95=0,
                p99=0,
                min_time_ms=0,
                max_time_ms=0,
                std_dev=0,
                measurements=[],
            )

        times = [s.total_time_ms for s in successful_samples]

        # Calculate percentiles
        p50 = float(np.percentile(times, 50))
        p95 = float(np.percentile(times, 95))
        p99 = float(np.percentile(times, 99))

        # Calculate statistics
        mean_time = statistics.mean(times)
        median_time = statistics.median(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0.0

        # Get detailed timings if available
        nl2sql_times = [s.nl2sql_time_ms for s in successful_samples if s.nl2sql_time_ms]
        sql_gen_times = [
            s.sql_generation_time_ms
            for s in successful_samples
            if s.sql_generation_time_ms
        ]
        sql_exec_times = [
            s.sql_execution_time_ms
            for s in successful_samples
            if s.sql_execution_time_ms
        ]

        return PerformanceMetrics(
            median_time_ms=median_time,
            mean_time_ms=mean_time,
            p50=p50,
            p95=p95,
            p99=p99,
            min_time_ms=min(times),
            max_time_ms=max(times),
            std_dev=std_dev,
            measurements=times,
            nl2sql_time_ms=statistics.mean(nl2sql_times) if nl2sql_times else None,
            sql_generation_time_ms=(
                statistics.mean(sql_gen_times) if sql_gen_times else None
            ),
            sql_execution_time_ms=(
                statistics.mean(sql_exec_times) if sql_exec_times else None
            ),
        )

    def reset(self) -> None:
        """Reset all samples."""
        self.samples.clear()
        self.warmup_samples.clear()


class ThroughputMeter:
    """
    Throughput measurement for batch operations.

    Measures queries per second (QPS) and related metrics.
    """

    def __init__(self):
        """Initialize throughput meter."""
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.total_queries: int = 0
        self.successful_queries: int = 0
        self.failed_queries: int = 0

    def start(self) -> None:
        """Start throughput measurement."""
        self.start_time = time.perf_counter()
        self.total_queries = 0
        self.successful_queries = 0
        self.failed_queries = 0

    def record_query(self, success: bool = True) -> None:
        """
        Record a query execution.

        Args:
            success: Whether query was successful
        """
        self.total_queries += 1
        if success:
            self.successful_queries += 1
        else:
            self.failed_queries += 1

    def stop(self) -> Dict[str, Any]:
        """
        Stop measurement and compute throughput metrics.

        Returns:
            Dictionary with throughput metrics
        """
        self.end_time = time.perf_counter()

        if not self.start_time:
            return {
                "qps": 0,
                "total_queries": 0,
                "successful_queries": 0,
                "failed_queries": 0,
                "success_rate": 0,
                "duration_seconds": 0,
            }

        duration = self.end_time - self.start_time
        qps = self.total_queries / duration if duration > 0 else 0
        success_rate = (
            self.successful_queries / self.total_queries
            if self.total_queries > 0
            else 0
        )

        return {
            "qps": qps,
            "total_queries": self.total_queries,
            "successful_queries": self.successful_queries,
            "failed_queries": self.failed_queries,
            "success_rate": success_rate,
            "duration_seconds": duration,
        }


class ConcurrentPerformanceTester:
    """
    Concurrent performance testing for load testing scenarios.

    Simulates multiple concurrent users/queries.
    """

    def __init__(self, concurrency: int = 1):
        """
        Initialize concurrent performance tester.

        Args:
            concurrency: Number of concurrent workers
        """
        self.concurrency = concurrency
        self.results: List[PerformanceSample] = []

    async def run_async(
        self,
        async_func: Callable,
        test_duration_seconds: int = 60,
        *args: Any,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Run async concurrent performance test.

        Args:
            async_func: Async function to test
            test_duration_seconds: Duration of test in seconds
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Performance metrics
        """
        import asyncio

        start_time = time.perf_counter()
        end_time = start_time + test_duration_seconds

        tasks = []
        query_count = 0

        async def worker():
            nonlocal query_count
            while time.perf_counter() < end_time:
                try:
                    task_start = time.perf_counter()
                    await async_func(*args, **kwargs)
                    task_end = time.perf_counter()

                    elapsed_ms = (task_end - task_start) * 1000
                    self.results.append(
                        PerformanceSample(total_time_ms=elapsed_ms, success=True)
                    )
                    query_count += 1

                except Exception as e:
                    self.results.append(
                        PerformanceSample(
                            total_time_ms=0, success=False, error=str(e)
                        )
                    )
                    query_count += 1

        # Create concurrent workers
        for _ in range(self.concurrency):
            tasks.append(asyncio.create_task(worker()))

        # Wait for all workers to complete
        await asyncio.gather(*tasks)

        actual_duration = time.perf_counter() - start_time

        # Compute metrics
        profiler = PerformanceProfiler()
        profiler.samples = self.results
        metrics = profiler.compute_metrics()

        return {
            "concurrency": self.concurrency,
            "total_queries": query_count,
            "duration_seconds": actual_duration,
            "qps": query_count / actual_duration if actual_duration > 0 else 0,
            "performance_metrics": metrics,
        }


def measure_execution_time(func: Callable) -> Callable:
    """
    Decorator to measure function execution time.

    Args:
        func: Function to measure

    Returns:
        Wrapped function with timing
    """

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()

        elapsed_ms = (end - start) * 1000

        # Attach timing to result if it's an object
        if hasattr(result, "__dict__"):
            result.execution_time_ms = elapsed_ms

        return result

    return wrapper
