"""Unit tests for cost evaluation module."""
import pytest

from onb.core.types import TokenUsage
from onb.evaluation.cost import (
    CostCalculator,
    CostSample,
    CostTracker,
    LLMProvider,
    ModelPricing,
    calculate_batch_cost,
)


class TestModelPricing:
    """Test ModelPricing dataclass."""

    def test_initialization(self):
        """Test basic initialization."""
        pricing = ModelPricing(
            model_name="gpt-4",
            provider=LLMProvider.OPENAI,
            input_price_per_1k=0.03,
            output_price_per_1k=0.06,
        )

        assert pricing.model_name == "gpt-4"
        assert pricing.provider == LLMProvider.OPENAI
        assert pricing.input_price_per_1k == 0.03
        assert pricing.output_price_per_1k == 0.06
        assert pricing.currency == "USD"
        assert pricing.effective_date is None

    def test_initialization_with_optional_fields(self):
        """Test initialization with optional fields."""
        pricing = ModelPricing(
            model_name="custom-model",
            provider=LLMProvider.CUSTOM,
            input_price_per_1k=0.01,
            output_price_per_1k=0.02,
            currency="EUR",
            effective_date="2025-01-01",
        )

        assert pricing.currency == "EUR"
        assert pricing.effective_date == "2025-01-01"


class TestCostSample:
    """Test CostSample dataclass."""

    def test_initialization(self):
        """Test basic initialization."""
        sample = CostSample(
            input_tokens=1000,
            output_tokens=500,
            total_tokens=1500,
            input_cost=0.01,
            output_cost=0.015,
            total_cost=0.025,
            model_name="gpt-4",
            provider=LLMProvider.OPENAI,
        )

        assert sample.input_tokens == 1000
        assert sample.output_tokens == 500
        assert sample.total_tokens == 1500
        assert sample.input_cost == 0.01
        assert sample.output_cost == 0.015
        assert sample.total_cost == 0.025
        assert sample.model_name == "gpt-4"
        assert sample.provider == LLMProvider.OPENAI
        assert sample.currency == "USD"
        assert sample.metadata == {}

    def test_initialization_with_metadata(self):
        """Test initialization with metadata."""
        sample = CostSample(
            input_tokens=1000,
            output_tokens=500,
            total_tokens=1500,
            input_cost=0.01,
            output_cost=0.015,
            total_cost=0.025,
            model_name="gpt-4",
            provider=LLMProvider.OPENAI,
            metadata={"query_id": "q123", "domain": "ecommerce"},
        )

        assert sample.metadata["query_id"] == "q123"
        assert sample.metadata["domain"] == "ecommerce"


class TestCostCalculator:
    """Test CostCalculator class."""

    def test_initialization_default(self):
        """Test initialization with default pricing."""
        calculator = CostCalculator()

        # Should have default pricing loaded
        assert "gpt-4" in calculator.pricing
        assert "claude-3-opus" in calculator.pricing

    def test_initialization_custom_pricing(self):
        """Test initialization with custom pricing."""
        custom_pricing = {
            "custom-model": ModelPricing(
                model_name="custom-model",
                provider=LLMProvider.CUSTOM,
                input_price_per_1k=0.001,
                output_price_per_1k=0.002,
            )
        }

        calculator = CostCalculator(custom_pricing=custom_pricing)

        # Should have both default and custom pricing
        assert "gpt-4" in calculator.pricing
        assert "custom-model" in calculator.pricing

    def test_add_pricing(self):
        """Test adding new pricing."""
        calculator = CostCalculator()

        new_pricing = ModelPricing(
            model_name="new-model",
            provider=LLMProvider.CUSTOM,
            input_price_per_1k=0.005,
            output_price_per_1k=0.01,
        )

        calculator.add_pricing(new_pricing)

        assert "new-model" in calculator.pricing
        assert calculator.pricing["new-model"] == new_pricing

    def test_get_pricing(self):
        """Test getting pricing for a model."""
        calculator = CostCalculator()

        pricing = calculator.get_pricing("gpt-4")

        assert pricing is not None
        assert pricing.model_name == "gpt-4"
        assert pricing.provider == LLMProvider.OPENAI

    def test_get_pricing_not_found(self):
        """Test getting pricing for unknown model."""
        calculator = CostCalculator()

        pricing = calculator.get_pricing("unknown-model")

        assert pricing is None

    def test_calculate_cost_gpt4(self):
        """Test cost calculation for GPT-4."""
        calculator = CostCalculator()

        token_usage = TokenUsage(
            input_tokens=1000,
            output_tokens=500,
            total_tokens=1500,
        )

        sample = calculator.calculate_cost(token_usage, "gpt-4")

        # GPT-4: $0.03 per 1K input, $0.06 per 1K output
        assert sample.input_tokens == 1000
        assert sample.output_tokens == 500
        assert sample.input_cost == pytest.approx(0.03)  # 1000/1000 * 0.03
        assert sample.output_cost == pytest.approx(0.03)  # 500/1000 * 0.06
        assert sample.total_cost == pytest.approx(0.06)
        assert sample.model_name == "gpt-4"

    def test_calculate_cost_claude(self):
        """Test cost calculation for Claude."""
        calculator = CostCalculator()

        token_usage = TokenUsage(
            input_tokens=2000,
            output_tokens=1000,
            total_tokens=3000,
        )

        sample = calculator.calculate_cost(token_usage, "claude-3-sonnet")

        # Claude Sonnet: $0.003 per 1K input, $0.015 per 1K output
        assert sample.input_cost == pytest.approx(0.006)  # 2000/1000 * 0.003
        assert sample.output_cost == pytest.approx(0.015)  # 1000/1000 * 0.015
        assert sample.total_cost == pytest.approx(0.021)

    def test_calculate_cost_unknown_model(self):
        """Test cost calculation for unknown model raises error."""
        calculator = CostCalculator()

        token_usage = TokenUsage(
            input_tokens=1000,
            output_tokens=500,
            total_tokens=1500,
        )

        with pytest.raises(ValueError, match="No pricing found"):
            calculator.calculate_cost(token_usage, "unknown-model")

    def test_estimate_cost(self):
        """Test cost estimation."""
        calculator = CostCalculator()

        cost = calculator.estimate_cost(
            input_tokens=1000, output_tokens=500, model_name="gpt-3.5-turbo"
        )

        # GPT-3.5: $0.0005 per 1K input, $0.0015 per 1K output
        expected = (1000 / 1000 * 0.0005) + (500 / 1000 * 0.0015)
        assert cost == pytest.approx(expected)

    def test_estimate_cost_unknown_model(self):
        """Test cost estimation for unknown model raises error."""
        calculator = CostCalculator()

        with pytest.raises(ValueError, match="No pricing found"):
            calculator.estimate_cost(
                input_tokens=1000, output_tokens=500, model_name="unknown"
            )


class TestCostTracker:
    """Test CostTracker class."""

    def test_initialization(self):
        """Test tracker initialization."""
        tracker = CostTracker()

        assert tracker.calculator is not None
        assert tracker.samples == []

    def test_initialization_custom_calculator(self):
        """Test initialization with custom calculator."""
        custom_calculator = CostCalculator()
        tracker = CostTracker(calculator=custom_calculator)

        assert tracker.calculator is custom_calculator

    def test_track_single_query(self):
        """Test tracking a single query."""
        tracker = CostTracker()

        token_usage = TokenUsage(
            input_tokens=1000,
            output_tokens=500,
            total_tokens=1500,
        )

        sample = tracker.track(token_usage, "gpt-4")

        assert len(tracker.samples) == 1
        assert tracker.samples[0] == sample
        assert sample.total_cost > 0

    def test_track_multiple_queries(self):
        """Test tracking multiple queries."""
        tracker = CostTracker()

        for i in range(5):
            token_usage = TokenUsage(
                input_tokens=1000,
                output_tokens=500,
                total_tokens=1500,
            )
            tracker.track(token_usage, "gpt-4")

        assert len(tracker.samples) == 5

    def test_get_total_cost(self):
        """Test getting total cost."""
        tracker = CostTracker()

        # Track 3 queries
        for _ in range(3):
            token_usage = TokenUsage(
                input_tokens=1000,
                output_tokens=500,
                total_tokens=1500,
            )
            tracker.track(token_usage, "gpt-4")

        total_cost = tracker.get_total_cost()

        # Each query costs 0.06 (GPT-4)
        assert total_cost == pytest.approx(0.18)

    def test_get_total_tokens(self):
        """Test getting total tokens."""
        tracker = CostTracker()

        tracker.track(
            TokenUsage(input_tokens=1000, output_tokens=500, total_tokens=1500),
            "gpt-4",
        )
        tracker.track(
            TokenUsage(input_tokens=2000, output_tokens=1000, total_tokens=3000),
            "gpt-4",
        )

        total_tokens = tracker.get_total_tokens()

        assert total_tokens == 4500

    def test_get_average_cost_per_query(self):
        """Test getting average cost per query."""
        tracker = CostTracker()

        # Track 4 queries
        for _ in range(4):
            token_usage = TokenUsage(
                input_tokens=1000,
                output_tokens=500,
                total_tokens=1500,
            )
            tracker.track(token_usage, "gpt-4")

        avg_cost = tracker.get_average_cost_per_query()

        # Each query costs 0.06
        assert avg_cost == pytest.approx(0.06)

    def test_get_average_cost_empty(self):
        """Test getting average cost with no samples."""
        tracker = CostTracker()

        avg_cost = tracker.get_average_cost_per_query()

        assert avg_cost == 0.0

    def test_get_cost_breakdown(self):
        """Test getting cost breakdown."""
        tracker = CostTracker()

        # Track 2 different queries
        tracker.track(
            TokenUsage(input_tokens=1000, output_tokens=500, total_tokens=1500),
            "gpt-4",
        )
        tracker.track(
            TokenUsage(input_tokens=2000, output_tokens=1000, total_tokens=3000),
            "gpt-3.5-turbo",
        )

        breakdown = tracker.get_cost_breakdown()

        assert "input_cost" in breakdown
        assert "output_cost" in breakdown
        assert "total_cost" in breakdown
        assert breakdown["total_cost"] > 0
        assert (
            breakdown["total_cost"]
            == breakdown["input_cost"] + breakdown["output_cost"]
        )

    def test_get_cost_by_model(self):
        """Test getting cost grouped by model."""
        tracker = CostTracker()

        # Track queries for different models
        tracker.track(
            TokenUsage(input_tokens=1000, output_tokens=500, total_tokens=1500),
            "gpt-4",
        )
        tracker.track(
            TokenUsage(input_tokens=1000, output_tokens=500, total_tokens=1500),
            "gpt-4",
        )
        tracker.track(
            TokenUsage(input_tokens=2000, output_tokens=1000, total_tokens=3000),
            "gpt-3.5-turbo",
        )

        cost_by_model = tracker.get_cost_by_model()

        assert "gpt-4" in cost_by_model
        assert "gpt-3.5-turbo" in cost_by_model
        assert cost_by_model["gpt-4"] == pytest.approx(0.12)  # 2 queries * 0.06
        assert cost_by_model["gpt-3.5-turbo"] > 0

    def test_get_token_stats(self):
        """Test getting token statistics."""
        tracker = CostTracker()

        # Track 3 queries
        tracker.track(
            TokenUsage(input_tokens=1000, output_tokens=500, total_tokens=1500),
            "gpt-4",
        )
        tracker.track(
            TokenUsage(input_tokens=2000, output_tokens=1000, total_tokens=3000),
            "gpt-4",
        )
        tracker.track(
            TokenUsage(input_tokens=1500, output_tokens=750, total_tokens=2250),
            "gpt-4",
        )

        stats = tracker.get_token_stats()

        assert stats["total_input_tokens"] == 4500
        assert stats["total_output_tokens"] == 2250
        assert stats["total_tokens"] == 6750
        assert stats["avg_input_tokens"] == 1500
        assert stats["avg_output_tokens"] == 750
        assert stats["avg_total_tokens"] == 2250

    def test_get_token_stats_empty(self):
        """Test getting token stats with no samples."""
        tracker = CostTracker()

        stats = tracker.get_token_stats()

        assert stats["total_input_tokens"] == 0
        assert stats["total_output_tokens"] == 0
        assert stats["total_tokens"] == 0

    def test_reset(self):
        """Test resetting tracker."""
        tracker = CostTracker()

        # Track some queries
        for _ in range(3):
            tracker.track(
                TokenUsage(input_tokens=1000, output_tokens=500, total_tokens=1500),
                "gpt-4",
            )

        assert len(tracker.samples) == 3

        tracker.reset()

        assert len(tracker.samples) == 0
        assert tracker.get_total_cost() == 0.0

    def test_get_summary(self):
        """Test getting comprehensive summary."""
        tracker = CostTracker()

        # Track queries
        tracker.track(
            TokenUsage(input_tokens=1000, output_tokens=500, total_tokens=1500),
            "gpt-4",
        )
        tracker.track(
            TokenUsage(input_tokens=2000, output_tokens=1000, total_tokens=3000),
            "gpt-3.5-turbo",
        )

        summary = tracker.get_summary()

        assert summary["total_queries"] == 2
        assert summary["total_cost"] > 0
        assert summary["average_cost_per_query"] > 0
        assert "cost_breakdown" in summary
        assert "cost_by_model" in summary
        assert "token_stats" in summary


class TestCalculateBatchCost:
    """Test calculate_batch_cost function."""

    def test_calculate_batch_cost(self):
        """Test calculating cost for batch of queries."""
        token_usages = [
            TokenUsage(input_tokens=1000, output_tokens=500, total_tokens=1500),
            TokenUsage(input_tokens=1500, output_tokens=750, total_tokens=2250),
            TokenUsage(input_tokens=2000, output_tokens=1000, total_tokens=3000),
        ]

        result = calculate_batch_cost(token_usages, "gpt-4")

        assert "total_cost" in result
        assert "average_cost" in result
        assert "cost_breakdown" in result
        # Query 1: 0.06, Query 2: 0.09, Query 3: 0.12 => Total: 0.27
        assert result["total_cost"] == pytest.approx(0.27)
        assert result["average_cost"] == pytest.approx(0.09)

    def test_calculate_batch_cost_empty(self):
        """Test calculating cost for empty batch."""
        result = calculate_batch_cost([], "gpt-4")

        assert result["total_cost"] == 0.0
        assert result["average_cost"] == 0.0

    def test_calculate_batch_cost_different_sizes(self):
        """Test calculating cost for queries with different token counts."""
        token_usages = [
            TokenUsage(input_tokens=500, output_tokens=250, total_tokens=750),
            TokenUsage(input_tokens=10000, output_tokens=5000, total_tokens=15000),
        ]

        result = calculate_batch_cost(token_usages, "gpt-3.5-turbo")

        assert result["total_cost"] > 0
        # First query is smaller, second is much larger
        assert result["average_cost"] > 0


class TestLLMProvider:
    """Test LLMProvider enum."""

    def test_provider_values(self):
        """Test all provider enum values."""
        assert LLMProvider.OPENAI == "openai"
        assert LLMProvider.ANTHROPIC == "anthropic"
        assert LLMProvider.AZURE_OPENAI == "azure_openai"
        assert LLMProvider.GOOGLE == "google"
        assert LLMProvider.COHERE == "cohere"
        assert LLMProvider.CUSTOM == "custom"
