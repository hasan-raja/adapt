from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal
from datetime import datetime
from enum import Enum


class NetworkTier(str, Enum):
    WIFI = "wifi"
    TIER_4G = "4g"
    TIER_3G = "3g"
    TIER_2G = "2g"


class CompressionLevel(str, Enum):
    NONE = "none"
    LIGHT = "light"
    MEDIUM = "medium"
    AGGRESSIVE = "aggressive"


class AdaptationEvent(BaseModel):
    id: int
    timestamp: datetime
    from_tier: Optional[NetworkTier]
    to_tier: NetworkTier
    compression_applied: CompressionLevel
    original_tokens: int
    compressed_tokens: int
    cache_hit: bool


class NetworkStatus(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    tier: NetworkTier
    bandwidth_kbps: float
    latency_ms: float
    compression_level: CompressionLevel
    model_size: str
    rolling_avg_bandwidth: float = 0
    rolling_avg_latency: float = 0


class RequestPayload(BaseModel):
    message: str
    history: list[dict] = Field(default_factory=list)
    force_tier: Optional[NetworkTier] = None


class ResponsePayload(BaseModel):
    response: str
    tier_used: NetworkTier
    compression_ratio: float
    tokens_used: int
    cost_rs: float
    cache_hit: bool
    adaptation_count: int
    quality_score: float
    trace: list[str] = Field(default_factory=list)