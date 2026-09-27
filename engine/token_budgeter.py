"""
VeloceGrid: Token Budgeter & Dynamic Quota Controller
Calculates dynamic token envelopes, cost projections, and throughput metrics for Nebius Token Factory.
"""

from typing import Dict, Any, List
from dataclasses import dataclass

# Nebius Token Factory Price Matrix (USD per 1M tokens)
NEBIUS_PRICING = {
    "nvidia/nemotron-4-340b": {"prompt": 2.50, "completion": 7.50},
    "nvidia/nemotron-4-70b": {"prompt": 0.80, "completion": 2.40},
    "nvidia/nemotron-3-8b": {"prompt": 0.20, "completion": 0.60},
    "nvidia/nemotron-mini-4b": {"prompt": 0.10, "completion": 0.30},
}

@dataclass
class CostBreakdown:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    model_name: str

class TokenBudgeter:
    def __init__(self, max_pipeline_budget_usd: float = 10.0):
        self.max_pipeline_budget_usd = max_pipeline_budget_usd
        self.accumulated_cost_usd = 0.0
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0

    def calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> CostBreakdown:
        pricing = NEBIUS_PRICING.get(model, NEBIUS_PRICING["nvidia/nemotron-4-70b"])
        prompt_cost = (prompt_tokens / 1_000_000) * pricing["prompt"]
        completion_cost = (completion_tokens / 1_000_000) * pricing["completion"]
        total_cost = prompt_cost + completion_cost

        return CostBreakdown(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            estimated_cost_usd=round(total_cost, 6),
            model_name=model
        )

    def allocate_node_quota(self, task_complexity: str, base_limit: int = 2048) -> int:
        """Dynamically scales token limit based on task complexity tier."""
        multipliers = {
            "low": 0.5,
            "medium": 1.0,
            "high": 2.0,
            "critical": 4.0
        }
        mult = multipliers.get(task_complexity.lower(), 1.0)
        return int(base_limit * mult)

    def record_usage(self, model: str, prompt_tokens: int, completion_tokens: int) -> CostBreakdown:
        breakdown = self.calculate_cost(model, prompt_tokens, completion_tokens)
        self.accumulated_cost_usd += breakdown.estimated_cost_usd
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        return breakdown

    def is_within_budget(self) -> bool:
        return self.accumulated_cost_usd <= self.max_pipeline_budget_usd

    def get_summary(self) -> Dict[str, Any]:
        return {
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_prompt_tokens + self.total_completion_tokens,
            "total_cost_usd": round(self.accumulated_cost_usd, 6),
            "max_budget_usd": self.max_pipeline_budget_usd,
            "budget_utilized_pct": round((self.accumulated_cost_usd / max(self.max_pipeline_budget_usd, 0.0001)) * 100, 2)
        }
