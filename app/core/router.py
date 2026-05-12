"""
Network-aware model routing.
Selects model, compression, and cost parameters based on network conditions.
"""

from typing import Optional
from app.models import NetworkTier, CompressionLevel, NetworkStatus


# Cost per 1K tokens in INR (based on Sarvam pricing)
COST_PER_1K_TOKENS: dict[str, float] = {
    "1B": 0.50,    # Tiny models
    "3B": 1.50,    # Small models
    "7B": 3.00,    # Medium models
    "30B+": 8.00,  # Full models
}


def get_tier_config(tier: NetworkTier) -> dict:
    """Get configuration for a network tier."""
    from app.core.network import TIER_CONFIG
    return TIER_CONFIG[tier]


def calculate_cost(tokens: int, model_size: str) -> float:
    """Calculate cost in INR for given tokens and model."""
    cost_per_1k = COST_PER_1K_TOKENS.get(model_size, 3.00)
    return (tokens / 1000) * cost_per_1k


def estimate_tokens(text: str, compression: CompressionLevel) -> int:
    """
    Rough token estimate.
    Hindi/Indic scripts: ~2 chars/token
    English: ~4 chars/token
    """
    from app.core.compression import detect_indic_content

    indic_ratio = detect_indic_content(text)
    # Average: 3 chars/token base
    base_chars_per_token = 3

    # Adjust for Indic content
    chars_per_token = base_chars_per_token * (1 - indic_ratio * 0.3)

    # Compression affects token count
    compression_multiplier = {
        CompressionLevel.NONE: 1.0,
        CompressionLevel.LIGHT: 0.85,
        CompressionLevel.MEDIUM: 0.6,
        CompressionLevel.AGGRESSIVE: 0.4,
    }.get(compression, 1.0)

    if not text:
        return 0

    est_tokens = len(text) / chars_per_token * compression_multiplier
    return int(est_tokens)


def select_model_for_tier(tier: NetworkTier) -> tuple[str, CompressionLevel]:
    """
    Select model size and compression based on network tier.
    Returns (model_name, compression_level).
    """
    configs = {
        NetworkTier.WIFI: ("30B+", CompressionLevel.NONE),
        NetworkTier.TIER_4G: ("7B", CompressionLevel.LIGHT),
        NetworkTier.TIER_3G: ("3B", CompressionLevel.MEDIUM),
        NetworkTier.TIER_2G: ("1B", CompressionLevel.AGGRESSIVE),
    }
    return configs.get(tier, ("7B", CompressionLevel.LIGHT))


def calculate_quality_score(
    original_response: str,
    compressed_response: str,
    cache_hit: bool
) -> float:
    """
    Calculate quality score for adapted response.
    Cache hits are high quality. Compressed responses scored by length ratio.
    """
    if cache_hit:
        return 0.95  # Cache hits are reliable

    if not original_response:
        return 0.0

    if not compressed_response:
        return 0.0

    # Simple heuristic: if compressed is much shorter, quality likely lost
    ratio = len(compressed_response) / len(original_response)

    if ratio > 0.9:
        return 0.98  # Minimal compression
    elif ratio > 0.7:
        return 0.95  # Light compression
    elif ratio > 0.5:
        return 0.85  # Medium compression
    elif ratio > 0.3:
        return 0.75  # Aggressive compression
    else:
        return 0.60  # Very aggressive - quality penalty