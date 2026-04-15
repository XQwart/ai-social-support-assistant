from __future__ import annotations

from math import ceil
from typing import TYPE_CHECKING

from app.clients.base_clients import LLMUsage

if TYPE_CHECKING:
    from app.core.config import Config
    from app.schemas.chat_schemas import ChatContextStats


class ContextBudgetService:
    _config: Config

    def __init__(self, config: Config) -> None:
        self._config = config

    def should_compress(self, ctx_stats: ChatContextStats) -> bool:
        predicted_next_input = ctx_stats.last_total_tokens + max(
            ctx_stats.reserve_input_tokens,
            self._config.llm_default_input_reserve_tokens,
        )

        return predicted_next_input >= self._config.llm_context_threshold

    def build_usage_updates(
        self,
        ctx_stats: ChatContextStats,
        usage: LLMUsage | None,
        was_compressed_before_request: bool,
    ) -> dict[str, object]:
        if usage is None:
            return {}

        updates: dict[str, object] = {
            "last_total_tokens": usage.total_tokens,
        }

        if was_compressed_before_request:
            return updates

        previous_total = ctx_stats.last_total_tokens
        if previous_total == 0:
            return updates

        observed_input_delta = usage.input_tokens - previous_total
        if observed_input_delta <= 0:
            return updates

        samples = list(ctx_stats.recent_input_deltas)
        samples.append(observed_input_delta)

        max_len = self._config.llm_reserve_history_size
        if len(samples) > max_len:
            samples = samples[-max_len:]

        updates["recent_input_deltas"] = samples
        updates["reserve_input_tokens"] = max(
            self._percentile_95(samples),
            self._config.llm_default_input_reserve_tokens,
        )
        return updates

    @staticmethod
    def _percentile_95(values: list[int]) -> int:
        positive = sorted(values)
        if not positive:
            return 0

        index = max(0, ceil(len(positive) * 0.95) - 1)
        return positive[index]
