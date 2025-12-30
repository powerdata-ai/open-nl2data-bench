"""
Cost evaluation module for OpenNL2Data-Bench.

This module provides comprehensive cost analysis including:
- Token usage tracking (input/output tokens)
- Cost calculation for different LLM providers
- Per-query and aggregate cost metrics
- Multi-provider pricing support
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from onb.core.types import TokenUsage


class LLMProvider(str, Enum):
    """Supported LLM providers for cost calculation."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"
    GOOGLE = "google"
    COHERE = "cohere"
    CUSTOM = "custom"


@dataclass
class ModelPricing:
    """Pricing information for a specific model."""

    model_name: str
    provider: LLMProvider
    input_price_per_1k: float  # Price per 1000 input tokens
    output_price_per_1k: float  # Price per 1000 output tokens
    currency: str = "USD"
    effective_date: Optional[str] = None


# Default pricing as of January 2025
DEFAULT_PRICING: Dict[str, ModelPricing] = {
    # OpenAI GPT-4 models
    "gpt-4-turbo": ModelPricing(
        model_name="gpt-4-turbo",
        provider=LLMProvider.OPENAI,
        input_price_per_1k=0.01,
        output_price_per_1k=0.03,
    ),
    "gpt-4": ModelPricing(
        model_name="gpt-4",
        provider=LLMProvider.OPENAI,
        input_price_per_1k=0.03,
        output_price_per_1k=0.06,
    ),
    "gpt-4o": ModelPricing(
        model_name="gpt-4o",
        provider=LLMProvider.OPENAI,
        input_price_per_1k=0.005,
        output_price_per_1k=0.015,
    ),
    # OpenAI GPT-3.5 models
    "gpt-3.5-turbo": ModelPricing(
        model_name="gpt-3.5-turbo",
        provider=LLMProvider.OPENAI,
        input_price_per_1k=0.0005,
        output_price_per_1k=0.0015,
    ),
    # Anthropic Claude models
    "claude-3-opus": ModelPricing(
        model_name="claude-3-opus",
        provider=LLMProvider.ANTHROPIC,
        input_price_per_1k=0.015,
        output_price_per_1k=0.075,
    ),
    "claude-3-sonnet": ModelPricing(
        model_name="claude-3-sonnet",
        provider=LLMProvider.ANTHROPIC,
        input_price_per_1k=0.003,
        output_price_per_1k=0.015,
    ),
    "claude-3-haiku": ModelPricing(
        model_name="claude-3-haiku",
        provider=LLMProvider.ANTHROPIC,
        input_price_per_1k=0.00025,
        output_price_per_1k=0.00125,
    ),
    # Google Gemini models
    "gemini-pro": ModelPricing(
        model_name="gemini-pro",
        provider=LLMProvider.GOOGLE,
        input_price_per_1k=0.00025,
        output_price_per_1k=0.0005,
    ),
}


@dataclass
class CostSample:
    """Single cost measurement sample."""

    input_tokens: int
    output_tokens: int
    total_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float
    model_name: str
    provider: LLMProvider
    currency: str = "USD"
    metadata: Dict[str, str] = field(default_factory=dict)


class CostCalculator:
    """
    Cost calculator for LLM API usage.

    Supports multiple providers and models with customizable pricing.
    """

    def __init__(self, custom_pricing: Optional[Dict[str, ModelPricing]] = None):
        """
        Initialize cost calculator.

        Args:
            custom_pricing: Optional custom pricing dictionary to override defaults
        """
        self.pricing = DEFAULT_PRICING.copy()
        if custom_pricing:
            self.pricing.update(custom_pricing)

    def add_pricing(self, pricing: ModelPricing) -> None:
        """
        Add or update pricing for a model.

        Args:
            pricing: Model pricing information
        """
        self.pricing[pricing.model_name] = pricing

    def get_pricing(self, model_name: str) -> Optional[ModelPricing]:
        """
        Get pricing for a model.

        Args:
            model_name: Model name

        Returns:
            Model pricing or None if not found
        """
        return self.pricing.get(model_name)

    def calculate_cost(
        self, token_usage: TokenUsage, model_name: str
    ) -> CostSample:
        """
        Calculate cost for token usage.

        Args:
            token_usage: Token usage information
            model_name: Model name

        Returns:
            Cost sample with detailed breakdown

        Raises:
            ValueError: If pricing not found for model
        """
        pricing = self.get_pricing(model_name)
        if not pricing:
            raise ValueError(
                f"No pricing found for model '{model_name}'. "
                "Add pricing with add_pricing() or use a known model."
            )

        # Calculate costs
        input_cost = (token_usage.input_tokens / 1000) * pricing.input_price_per_1k
        output_cost = (token_usage.output_tokens / 1000) * pricing.output_price_per_1k
        total_cost = input_cost + output_cost

        return CostSample(
            input_tokens=token_usage.input_tokens,
            output_tokens=token_usage.output_tokens,
            total_tokens=token_usage.total_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=total_cost,
            model_name=model_name,
            provider=pricing.provider,
            currency=pricing.currency,
        )

    def estimate_cost(
        self, input_tokens: int, output_tokens: int, model_name: str
    ) -> float:
        """
        Estimate cost for given token counts.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model_name: Model name

        Returns:
            Estimated total cost
        """
        pricing = self.get_pricing(model_name)
        if not pricing:
            raise ValueError(f"No pricing found for model '{model_name}'")

        input_cost = (input_tokens / 1000) * pricing.input_price_per_1k
        output_cost = (output_tokens / 1000) * pricing.output_price_per_1k

        return input_cost + output_cost


class CostTracker:
    """
    Track and aggregate costs across multiple queries.

    Provides aggregated cost metrics and statistics.
    """

    def __init__(self, calculator: Optional[CostCalculator] = None):
        """
        Initialize cost tracker.

        Args:
            calculator: Cost calculator instance (creates default if None)
        """
        self.calculator = calculator or CostCalculator()
        self.samples: List[CostSample] = []

    def track(self, token_usage: TokenUsage, model_name: str) -> CostSample:
        """
        Track cost for a query.

        Args:
            token_usage: Token usage information
            model_name: Model name

        Returns:
            Cost sample for this query
        """
        sample = self.calculator.calculate_cost(token_usage, model_name)
        self.samples.append(sample)
        return sample

    def get_total_cost(self) -> float:
        """
        Get total cost across all tracked queries.

        Returns:
            Total cost
        """
        return sum(sample.total_cost for sample in self.samples)

    def get_total_tokens(self) -> int:
        """
        Get total tokens across all tracked queries.

        Returns:
            Total token count
        """
        return sum(sample.total_tokens for sample in self.samples)

    def get_average_cost_per_query(self) -> float:
        """
        Get average cost per query.

        Returns:
            Average cost per query (0 if no samples)
        """
        if not self.samples:
            return 0.0
        return self.get_total_cost() / len(self.samples)

    def get_cost_breakdown(self) -> Dict[str, float]:
        """
        Get cost breakdown by input/output.

        Returns:
            Dictionary with input_cost, output_cost, total_cost
        """
        total_input_cost = sum(sample.input_cost for sample in self.samples)
        total_output_cost = sum(sample.output_cost for sample in self.samples)

        return {
            "input_cost": total_input_cost,
            "output_cost": total_output_cost,
            "total_cost": total_input_cost + total_output_cost,
        }

    def get_cost_by_model(self) -> Dict[str, float]:
        """
        Get total cost grouped by model.

        Returns:
            Dictionary mapping model name to total cost
        """
        cost_by_model: Dict[str, float] = {}

        for sample in self.samples:
            if sample.model_name not in cost_by_model:
                cost_by_model[sample.model_name] = 0.0
            cost_by_model[sample.model_name] += sample.total_cost

        return cost_by_model

    def get_token_stats(self) -> Dict[str, int]:
        """
        Get token usage statistics.

        Returns:
            Dictionary with token statistics
        """
        if not self.samples:
            return {
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_tokens": 0,
                "avg_input_tokens": 0,
                "avg_output_tokens": 0,
                "avg_total_tokens": 0,
            }

        total_input = sum(sample.input_tokens for sample in self.samples)
        total_output = sum(sample.output_tokens for sample in self.samples)
        num_samples = len(self.samples)

        return {
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_tokens": total_input + total_output,
            "avg_input_tokens": total_input // num_samples,
            "avg_output_tokens": total_output // num_samples,
            "avg_total_tokens": (total_input + total_output) // num_samples,
        }

    def reset(self) -> None:
        """Reset all tracked samples."""
        self.samples.clear()

    def get_summary(self) -> Dict[str, any]:
        """
        Get comprehensive cost summary.

        Returns:
            Dictionary with all cost metrics
        """
        return {
            "total_queries": len(self.samples),
            "total_cost": self.get_total_cost(),
            "average_cost_per_query": self.get_average_cost_per_query(),
            "cost_breakdown": self.get_cost_breakdown(),
            "cost_by_model": self.get_cost_by_model(),
            "token_stats": self.get_token_stats(),
        }


def calculate_batch_cost(
    token_usages: List[TokenUsage], model_name: str
) -> Dict[str, float]:
    """
    Calculate total cost for a batch of queries.

    Args:
        token_usages: List of token usage information
        model_name: Model name

    Returns:
        Dictionary with total cost and breakdown
    """
    calculator = CostCalculator()
    tracker = CostTracker(calculator)

    for usage in token_usages:
        tracker.track(usage, model_name)

    return {
        "total_cost": tracker.get_total_cost(),
        "average_cost": tracker.get_average_cost_per_query(),
        "cost_breakdown": tracker.get_cost_breakdown(),
    }
