"""Unit tests for performance profiling and benchmarking module."""
import asyncio
import statistics
import time
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pandas as pd
import pytest

from onb.core.types import PerformanceMetrics
from onb.evaluation.performance import (
    ConcurrentPerformanceTester,
    PerformanceProfiler,
    PerformanceSample,
    ThroughputMeter,
    measure_execution_time,
)


class TestPerformanceSample:
    """Test PerformanceSample dataclass."""

    def test_initialization_minimal(self):
        """Test minimal initialization."""
        sample = PerformanceSample(total_time_ms=123.45)

        assert sample.total_time_ms == 123.45
        assert sample.nl2sql_time_ms is None
        assert sample.sql_generation_time_ms is None
        assert sample.sql_execution_time_ms is None
        assert sample.success is True
        assert sample.error is None
        assert isinstance(sample.timestamp, float)

    def test_initialization_full(self):
        """Test full initialization with all fields."""
        sample = PerformanceSample(
            total_time_ms=500.0,
            nl2sql_time_ms=200.0,
            sql_generation_time_ms=150.0,
            sql_execution_time_ms=150.0,
            timestamp=1234567890.0,
            success=False,
            error="Test error",
        )

        assert sample.total_time_ms == 500.0
        assert sample.nl2sql_time_ms == 200.0
        assert sample.sql_generation_time_ms == 150.0
        assert sample.sql_execution_time_ms == 150.0
        assert sample.timestamp == 1234567890.0
        assert sample.success is False
        assert sample.error == "Test error"


class TestPerformanceProfiler:
    """Test PerformanceProfiler class."""

    def test_initialization(self):
        """Test profiler initialization."""
        profiler = PerformanceProfiler(warmup_iterations=3)

        assert profiler.warmup_iterations == 3
        assert profiler.samples == []
        assert profiler.warmup_samples == []

    def test_initialization_default(self):
        """Test profiler with default warmup."""
        profiler = PerformanceProfiler()

        assert profiler.warmup_iterations == 0

    def test_add_sample(self):
        """Test adding samples."""
        profiler = PerformanceProfiler()
        sample = PerformanceSample(total_time_ms=100.0)

        profiler.add_sample(sample)

        assert len(profiler.samples) == 1
        assert profiler.samples[0] == sample

    def test_measure_single_iteration(self):
        """Test measuring a function for single iteration."""
        profiler = PerformanceProfiler()

        def test_func():
            time.sleep(0.01)  # 10ms
            return "result"

        metrics = profiler.measure(test_func, iterations=1)

        assert len(profiler.samples) == 1
        assert profiler.samples[0].success is True
        assert profiler.samples[0].total_time_ms >= 10.0
        assert metrics.mean_time_ms >= 10.0
        assert metrics.median_time_ms >= 10.0

    def test_measure_multiple_iterations(self):
        """Test measuring function for multiple iterations."""
        profiler = PerformanceProfiler()

        def test_func():
            time.sleep(0.005)  # 5ms
            return "result"

        metrics = profiler.measure(test_func, iterations=5)

        assert len(profiler.samples) == 5
        assert all(s.success for s in profiler.samples)
        assert all(s.total_time_ms >= 5.0 for s in profiler.samples)

    def test_measure_with_warmup(self):
        """Test measuring with warmup iterations."""
        profiler = PerformanceProfiler(warmup_iterations=2)

        def test_func():
            time.sleep(0.005)
            return "result"

        metrics = profiler.measure(test_func, iterations=3)

        assert len(profiler.warmup_samples) == 2
        assert len(profiler.samples) == 3
        # Warmup samples don't affect final metrics
        assert len(metrics.measurements) == 3

    def test_measure_with_error(self):
        """Test measuring function that raises error."""
        profiler = PerformanceProfiler()

        def failing_func():
            raise ValueError("Test error")

        metrics = profiler.measure(failing_func, iterations=2)

        assert len(profiler.samples) == 2
        assert all(not s.success for s in profiler.samples)
        assert all(s.error == "Test error" for s in profiler.samples)
        # Should return zero metrics
        assert metrics.mean_time_ms == 0
        assert metrics.median_time_ms == 0

    def test_measure_with_result_timing(self):
        """Test extracting timing from result object."""
        profiler = PerformanceProfiler()

        class ResultWithTiming:
            def __init__(self):
                self.time_ms = 123.45

        def test_func():
            return ResultWithTiming()

        profiler.measure(test_func, iterations=1)

        assert profiler.samples[0].nl2sql_time_ms == 123.45

    def test_compute_metrics_empty(self):
        """Test computing metrics with no samples."""
        profiler = PerformanceProfiler()
        metrics = profiler.compute_metrics()

        assert metrics.mean_time_ms == 0
        assert metrics.median_time_ms == 0
        assert metrics.p50 == 0
        assert metrics.p95 == 0
        assert metrics.p99 == 0
        assert metrics.min_time_ms == 0
        assert metrics.max_time_ms == 0
        assert metrics.std_dev == 0
        assert metrics.measurements == []

    def test_compute_metrics_single_sample(self):
        """Test computing metrics with single sample."""
        profiler = PerformanceProfiler()
        profiler.add_sample(PerformanceSample(total_time_ms=100.0))

        metrics = profiler.compute_metrics()

        assert metrics.mean_time_ms == 100.0
        assert metrics.median_time_ms == 100.0
        assert metrics.p50 == 100.0
        assert metrics.p95 == 100.0
        assert metrics.p99 == 100.0
        assert metrics.min_time_ms == 100.0
        assert metrics.max_time_ms == 100.0
        assert metrics.std_dev == 0.0  # Only one sample

    def test_compute_metrics_multiple_samples(self):
        """Test computing metrics with multiple samples."""
        profiler = PerformanceProfiler()
        times = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]

        for t in times:
            profiler.add_sample(PerformanceSample(total_time_ms=t))

        metrics = profiler.compute_metrics()

        assert metrics.mean_time_ms == statistics.mean(times)
        assert metrics.median_time_ms == statistics.median(times)
        assert metrics.p50 == pytest.approx(50.0, rel=0.1)
        assert metrics.p95 == pytest.approx(95.0, rel=0.1)
        assert metrics.p99 == pytest.approx(99.0, rel=0.1)
        assert metrics.min_time_ms == 10.0
        assert metrics.max_time_ms == 100.0
        assert metrics.std_dev > 0

    def test_compute_metrics_with_detailed_timings(self):
        """Test computing metrics with detailed timing breakdowns."""
        profiler = PerformanceProfiler()

        profiler.add_sample(
            PerformanceSample(
                total_time_ms=300.0,
                nl2sql_time_ms=100.0,
                sql_generation_time_ms=50.0,
                sql_execution_time_ms=150.0,
            )
        )
        profiler.add_sample(
            PerformanceSample(
                total_time_ms=400.0,
                nl2sql_time_ms=150.0,
                sql_generation_time_ms=75.0,
                sql_execution_time_ms=175.0,
            )
        )

        metrics = profiler.compute_metrics()

        assert metrics.nl2sql_time_ms == pytest.approx(125.0)
        assert metrics.sql_generation_time_ms == pytest.approx(62.5)
        assert metrics.sql_execution_time_ms == pytest.approx(162.5)

    def test_compute_metrics_mixed_success(self):
        """Test computing metrics with mix of success and failure."""
        profiler = PerformanceProfiler()

        profiler.add_sample(PerformanceSample(total_time_ms=100.0, success=True))
        profiler.add_sample(PerformanceSample(total_time_ms=0.0, success=False))
        profiler.add_sample(PerformanceSample(total_time_ms=200.0, success=True))

        metrics = profiler.compute_metrics()

        # Should only use successful samples
        assert len(metrics.measurements) == 2
        assert metrics.mean_time_ms == 150.0

    def test_reset(self):
        """Test resetting profiler."""
        profiler = PerformanceProfiler(warmup_iterations=2)

        def test_func():
            return "result"

        profiler.measure(test_func, iterations=3)
        assert len(profiler.samples) == 3
        assert len(profiler.warmup_samples) == 2

        profiler.reset()

        assert len(profiler.samples) == 0
        assert len(profiler.warmup_samples) == 0


class TestThroughputMeter:
    """Test ThroughputMeter class."""

    def test_initialization(self):
        """Test meter initialization."""
        meter = ThroughputMeter()

        assert meter.start_time is None
        assert meter.end_time is None
        assert meter.total_queries == 0
        assert meter.successful_queries == 0
        assert meter.failed_queries == 0

    def test_start(self):
        """Test starting measurement."""
        meter = ThroughputMeter()
        meter.start()

        assert meter.start_time is not None
        assert isinstance(meter.start_time, float)
        assert meter.total_queries == 0

    def test_record_query_success(self):
        """Test recording successful query."""
        meter = ThroughputMeter()
        meter.start()

        meter.record_query(success=True)

        assert meter.total_queries == 1
        assert meter.successful_queries == 1
        assert meter.failed_queries == 0

    def test_record_query_failure(self):
        """Test recording failed query."""
        meter = ThroughputMeter()
        meter.start()

        meter.record_query(success=False)

        assert meter.total_queries == 1
        assert meter.successful_queries == 0
        assert meter.failed_queries == 1

    def test_record_multiple_queries(self):
        """Test recording multiple queries."""
        meter = ThroughputMeter()
        meter.start()

        meter.record_query(success=True)
        meter.record_query(success=True)
        meter.record_query(success=False)
        meter.record_query(success=True)

        assert meter.total_queries == 4
        assert meter.successful_queries == 3
        assert meter.failed_queries == 1

    def test_stop_basic(self):
        """Test stopping measurement and getting metrics."""
        meter = ThroughputMeter()
        meter.start()

        # Simulate some queries
        time.sleep(0.1)  # 100ms
        meter.record_query(success=True)
        meter.record_query(success=True)
        meter.record_query(success=True)

        metrics = meter.stop()

        assert metrics["total_queries"] == 3
        assert metrics["successful_queries"] == 3
        assert metrics["failed_queries"] == 0
        assert metrics["success_rate"] == 1.0
        assert metrics["duration_seconds"] >= 0.1
        assert metrics["qps"] > 0

    def test_stop_with_failures(self):
        """Test metrics with some failures."""
        meter = ThroughputMeter()
        meter.start()

        meter.record_query(success=True)
        meter.record_query(success=False)
        meter.record_query(success=True)
        meter.record_query(success=False)

        metrics = meter.stop()

        assert metrics["total_queries"] == 4
        assert metrics["successful_queries"] == 2
        assert metrics["failed_queries"] == 2
        assert metrics["success_rate"] == 0.5

    def test_stop_without_start(self):
        """Test stopping without starting returns zero metrics."""
        meter = ThroughputMeter()
        metrics = meter.stop()

        assert metrics["qps"] == 0
        assert metrics["total_queries"] == 0
        assert metrics["success_rate"] == 0
        assert metrics["duration_seconds"] == 0

    def test_qps_calculation(self):
        """Test QPS calculation accuracy."""
        meter = ThroughputMeter()
        meter.start()

        # Simulate 10 queries over 0.1 seconds
        for _ in range(10):
            meter.record_query(success=True)

        time.sleep(0.1)
        metrics = meter.stop()

        # Should be approximately 100 QPS (10 queries / 0.1 seconds)
        # Allow some tolerance for timing variation
        assert 50 <= metrics["qps"] <= 200


class TestConcurrentPerformanceTester:
    """Test ConcurrentPerformanceTester class."""

    def test_initialization(self):
        """Test tester initialization."""
        tester = ConcurrentPerformanceTester(concurrency=5)

        assert tester.concurrency == 5
        assert tester.results == []

    def test_initialization_default(self):
        """Test default concurrency."""
        tester = ConcurrentPerformanceTester()

        assert tester.concurrency == 1

    @pytest.mark.asyncio
    async def test_run_async_basic(self):
        """Test basic async concurrent test."""
        tester = ConcurrentPerformanceTester(concurrency=2)

        async def test_func():
            await asyncio.sleep(0.01)  # 10ms
            return "result"

        metrics = await tester.run_async(test_func, test_duration_seconds=1)

        assert metrics["concurrency"] == 2
        assert metrics["total_queries"] > 0
        assert metrics["duration_seconds"] >= 1.0
        assert metrics["qps"] > 0
        assert "performance_metrics" in metrics

    @pytest.mark.asyncio
    async def test_run_async_short_duration(self):
        """Test with very short duration."""
        tester = ConcurrentPerformanceTester(concurrency=1)

        async def fast_func():
            await asyncio.sleep(0.001)  # 1ms

        metrics = await tester.run_async(fast_func, test_duration_seconds=1)

        # Should complete many iterations
        assert metrics["total_queries"] > 10
        assert len(tester.results) > 10

    @pytest.mark.asyncio
    async def test_run_async_with_errors(self):
        """Test handling errors during concurrent test."""
        tester = ConcurrentPerformanceTester(concurrency=2)

        call_count = 0

        async def failing_func():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)
            if call_count % 2 == 0:
                raise ValueError("Test error")
            return "result"

        metrics = await tester.run_async(failing_func, test_duration_seconds=1)

        # Should have both successful and failed results
        successful = [r for r in tester.results if r.success]
        failed = [r for r in tester.results if not r.success]

        assert len(successful) > 0
        assert len(failed) > 0
        assert all(r.error == "Test error" for r in failed)

    @pytest.mark.asyncio
    async def test_run_async_performance_metrics(self):
        """Test that performance metrics are computed correctly."""
        tester = ConcurrentPerformanceTester(concurrency=1)

        async def test_func():
            await asyncio.sleep(0.01)

        metrics = await tester.run_async(test_func, test_duration_seconds=1)

        perf_metrics = metrics["performance_metrics"]
        assert isinstance(perf_metrics, PerformanceMetrics)
        assert perf_metrics.mean_time_ms >= 10.0
        assert perf_metrics.p50 > 0
        assert perf_metrics.p95 > 0
        assert perf_metrics.p99 > 0


class TestMeasureExecutionTimeDecorator:
    """Test measure_execution_time decorator."""

    def test_decorator_basic(self):
        """Test basic decorator usage."""

        @measure_execution_time
        def test_func():
            time.sleep(0.01)
            return "result"

        result = test_func()

        assert result == "result"

    def test_decorator_with_object_result(self):
        """Test decorator attaches timing to object result."""

        class Result:
            def __init__(self, value):
                self.value = value

        @measure_execution_time
        def test_func():
            time.sleep(0.01)
            return Result("test")

        result = test_func()

        assert result.value == "test"
        assert hasattr(result, "execution_time_ms")
        assert result.execution_time_ms >= 10.0

    def test_decorator_with_primitive_result(self):
        """Test decorator with primitive return value."""

        @measure_execution_time
        def test_func():
            return 42

        result = test_func()

        # Primitive types don't have __dict__, so no timing attached
        assert result == 42
        assert not hasattr(result, "execution_time_ms")

    def test_decorator_with_arguments(self):
        """Test decorator with function arguments."""

        @measure_execution_time
        def add(a, b):
            return a + b

        result = add(2, 3)

        assert result == 5

    def test_decorator_with_kwargs(self):
        """Test decorator with keyword arguments."""

        class Result:
            def __init__(self, value):
                self.value = value

        @measure_execution_time
        def create_result(value="default", multiplier=1):
            return Result(value * multiplier)

        result = create_result(value=5, multiplier=3)

        assert result.value == 15
        assert hasattr(result, "execution_time_ms")

    def test_decorator_timing_accuracy(self):
        """Test decorator timing is reasonably accurate."""

        class Result:
            pass

        @measure_execution_time
        def slow_func():
            time.sleep(0.05)  # 50ms
            return Result()

        result = slow_func()

        # Should be at least 50ms, allow some overhead
        assert result.execution_time_ms >= 50.0
        assert result.execution_time_ms < 100.0  # Shouldn't be too much overhead
