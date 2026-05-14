"""
Metrics tracking for adaptation events.
"""

from collections import deque
from datetime import UTC, datetime
from typing import Optional
from app.models import NetworkTier, CompressionLevel, AdaptationEvent


MAX_EVENT_HISTORY = 100


class MetricsCollector:
    """Collects and tracks adaptation metrics."""

    def __init__(self):
        self._events: deque[AdaptationEvent] = deque(maxlen=MAX_EVENT_HISTORY)
        self._event_counter = 0
        self._total_cost_rs = 0.0
        self._total_tokens = 0
        self._cache_hits = 0
        self._requests_served = 0

    def record_adaptation(
        self,
        from_tier: Optional[NetworkTier],
        to_tier: NetworkTier,
        compression: CompressionLevel,
        original_tokens: int,
        compressed_tokens: int,
        cache_hit: bool,
    ) -> AdaptationEvent:
        """Record an adaptation event."""
        self._event_counter += 1
        event = AdaptationEvent(
            id=self._event_counter,
            timestamp=datetime.now(UTC),
            from_tier=from_tier,
            to_tier=to_tier,
            compression_applied=compression,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            cache_hit=cache_hit,
        )
        self._events.append(event)
        return event

    def record_request(
        self,
        cost_rs: float,
        tokens_used: int,
        cache_hit: bool,
    ) -> None:
        """Record a request for metrics."""
        self._requests_served += 1
        self._total_cost_rs += cost_rs
        self._total_tokens += tokens_used
        if cache_hit:
            self._cache_hits += 1

    def get_summary(self) -> dict:
        """Get metrics summary."""
        cost_per_request = self._total_cost_rs / self._requests_served if self._requests_served > 0 else 0
        tokens_per_request = self._total_tokens / self._requests_served if self._requests_served > 0 else 0
        cache_hit_rate = self._cache_hits / self._requests_served if self._requests_served > 0 else 0

        # Count tier distribution from recent events
        tier_counts: dict[str, int] = {}
        for event in list(self._events)[-20:]:  # Last 20 events
            tier_str = event.to_tier.value
            tier_counts[tier_str] = tier_counts.get(tier_str, 0) + 1

        return {
            "requests_served": self._requests_served,
            "total_cost_rs": round(self._total_cost_rs, 3),
            "total_tokens": self._total_tokens,
            "cache_hits": self._cache_hits,
            "cache_hit_rate": round(cache_hit_rate, 3),
            "cost_per_request_rs": round(cost_per_request, 3),
            "tokens_per_request": round(tokens_per_request, 1),
            "adaptation_events": len(self._events),
            "tier_distribution": tier_counts,
        }

    def get_recent_events(self, count: int = 10) -> list[dict]:
        """Get recent adaptation events."""
        events = list(self._events)[-count:]
        return [event.model_dump(mode="json") for event in events]

    def reset(self) -> None:
        """Reset all metrics."""
        self._events.clear()
        self._event_counter = 0
        self._total_cost_rs = 0.0
        self._total_tokens = 0
        self._cache_hits = 0
        self._requests_served = 0


# Global metrics instance
metrics = MetricsCollector()
