"""
ADAPT - Adaptive AI QoS Infrastructure
FastAPI application with compression, caching, and network-aware routing.
"""

import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.models import (
    NetworkTier,
    CompressionLevel,
    RequestPayload,
    ResponsePayload,
    AdaptationEvent,
)
from app.core.compression import compress_message, compress_conversation_history, calculate_compression_ratio
from app.core.network import network_probe, network_simulator, TIER_CONFIG, NetworkStatus
from app.core.router import select_model_for_tier, estimate_tokens, calculate_cost
from app.core.cache import semantic_cache
from app.core.metrics import metrics


# Demo responses for when no API key is available
DEMO_RESPONSES: dict[str, list[str]] = {
    NetworkTier.TIER_2G: [
        "Tiny model response - compressed for 2G. Working on mobile with limited bandwidth.",
        "2G optimized reply: Simplified but functional. Adapting to network constraints.",
    ],
    NetworkTier.TIER_3G: [
        "3G model response - moderate compression applied.",
        "Balanced response for medium bandwidth. Some details preserved.",
    ],
    NetworkTier.TIER_4G: [
        "4G response - light compression, good quality maintained.",
        "Full-ish response with minimal adaptation. Near-optimal quality.",
    ],
    NetworkTier.WIFI: [
        "Full quality response over WiFi. No compression, maximum detail.",
        "Peak quality response. All context preserved.",
    ],
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    print("ADAPT starting up...")
    print(f"Embeddings available: {semantic_cache._embedder is not None}")
    yield
    print("ADAPT shutting down...")


app = FastAPI(
    title="ADAPT",
    description="Adaptive AI QoS Infrastructure for degraded network conditions",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check."""
    return {
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0",
    }


@app.get("/network/status")
async def get_network_status(force_tier: NetworkTier = None) -> NetworkStatus:
    """Get current network status."""
    status = network_probe.get_status(force_tier=force_tier)
    return status


@app.post("/network/simulate")
async def start_simulation(sequence: list[dict]):
    """
    Start network simulation sequence.
    Each item: {"tier": "2g", "duration": 5}
    """
    parsed_sequence = []
    for item in sequence:
        tier = NetworkTier(item["tier"])
        duration = item.get("duration", 5)
        parsed_sequence.append((tier, duration))

    await network_simulator.start_simulation(parsed_sequence)

    return {"status": "simulation_started", "sequence": len(parsed_sequence)}


@app.post("/network/stop")
async def stop_simulation():
    """Stop any running simulation."""
    await network_simulator.stop_simulation()
    return {"status": "simulation_stopped"}


@app.post("/adapt")
async def adapt_request(payload: RequestPayload) -> ResponsePayload:
    """
    Main adaptation endpoint.
    Compresses prompt, checks cache, routes to appropriate model.
    """
    # Get network status
    network_status = network_probe.get_status(force_tier=payload.force_tier)
    tier = network_status.tier
    compression = network_status.compression_level

    # Record previous tier for adaptation event
    prev_tier = None
    for event in metrics.get_recent_events(1):
        prev_tier = NetworkTier(event["to_tier"]) if event.get("to_tier") else None

    # Compress message
    compressed_message = compress_message(payload.message, compression)

    # Estimate tokens
    original_tokens = estimate_tokens(payload.message, CompressionLevel.NONE)
    compressed_tokens = estimate_tokens(compressed_message, compression)

    # Check cache
    cache_key = compressed_message + str(tier)
    cached_response = semantic_cache.get(cache_key, compression)
    cache_hit = cached_response is not None

    # Get or generate response
    if cache_hit:
        response_text = cached_response
    else:
        # Select model based on tier
        model_size, _ = select_model_for_tier(tier)

        # Simulate API call with tier-appropriate response
        await asyncio.sleep(network_status.latency_ms / 1000)  # Simulate latency

        # Use API or demo response
        response_text = await call_model(
            compressed_message,
            payload.history,
            tier,
            model_size,
        )

        # Cache the response
        semantic_cache.put(cache_key, response_text)

    # Calculate metrics
    cost = calculate_cost(compressed_tokens, tier.value)
    compression_ratio = calculate_compression_ratio(payload.message, compressed_message)

    # Get quality score
    from app.core.router import calculate_quality_score
    quality = calculate_quality_score(payload.message, response_text, cache_hit)

    # Record metrics
    metrics.record_request(cost, compressed_tokens, cache_hit)

    if not cache_hit and prev_tier != tier:
        metrics.record_adaptation(
            from_tier=prev_tier,
            to_tier=tier,
            compression=compression,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            cache_hit=cache_hit,
        )

    adaptation_count = len(metrics.get_recent_events(20))

    return ResponsePayload(
        response=response_text,
        tier_used=tier,
        compression_ratio=compression_ratio,
        tokens_used=compressed_tokens,
        cost_rs=cost,
        cache_hit=cache_hit,
        adaptation_count=adaptation_count,
        quality_score=quality,
    )


async def call_model(
    message: str,
    history: list[dict],
    tier: NetworkTier,
    model_size: str,
) -> str:
    """
    Call the model API.
    Falls back to demo responses if no API key available.
    """
    # Try Sarvam API first
    sarvam_key = os.getenv("SARVAM_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if sarvam_key:
        # Sarvam API integration
        # (Full integration would require actual API endpoint)
        return await call_sarvam(message, history, tier, sarvam_key)

    if openai_key:
        # OpenAI fallback
        return await call_openai(message, history, tier, openai_key)

    # No API key - use demo response
    demo_responses = DEMO_RESPONSES.get(tier, DEMO_RESPONSES[NetworkTier.TIER_4G])
    return demo_responses[0]


async def call_sarvam(message: str, history: list[dict], tier: NetworkTier, api_key: str) -> str:
    """Call Sarvam API for model inference."""
    import httpx

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://api.sarvam.ai/inference",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "text": message,
                    "model": f"sarvam-m-{model_size_to_sarvam(tier)}",
                },
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("text", "Response received")
        except Exception as e:
            print(f"Sarvam API error: {e}")
            return get_demo_response(tier)


async def call_openai(message: str, history: list[dict], tier: NetworkTier, api_key: str) -> str:
    """Call OpenAI API as fallback."""
    import httpx

    model = tier_to_openai_model(tier)

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": message}],
                },
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return get_demo_response(tier)


def model_size_to_sarvam(tier: NetworkTier) -> str:
    """Map tier to Sarvam model name."""
    return {
        NetworkTier.TIER_2G: "1b",
        NetworkTier.TIER_3G: "3b",
        NetworkTier.TIER_4G: "7b",
        NetworkTier.WIFI: "30b",
    }.get(tier, "7b")


def tier_to_openai_model(tier: NetworkTier) -> str:
    """Map tier to OpenAI model name."""
    return {
        NetworkTier.TIER_2G: "gpt-3.5-turbo",
        NetworkTier.TIER_3G: "gpt-3.5-turbo",
        NetworkTier.TIER_4G: "gpt-4",
        NetworkTier.WIFI: "gpt-4-turbo-preview",
    }.get(tier, "gpt-3.5-turbo")


def get_demo_response(tier: NetworkTier) -> str:
    """Get a demo response for a tier."""
    responses = DEMO_RESPONSES.get(tier, DEMO_RESPONSES[NetworkTier.TIER_4G])
    return responses[0]


@app.get("/metrics")
async def get_metrics():
    """Get current metrics summary."""
    return metrics.get_summary()


@app.get("/metrics/events")
async def get_events(count: int = 10):
    """Get recent adaptation events."""
    return metrics.get_recent_events(count)


@app.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics."""
    return semantic_cache.get_stats()


@app.delete("/cache")
async def clear_cache():
    """Clear the semantic cache."""
    semantic_cache.clear()
    return {"status": "cache_cleared"}


# WebSocket for real-time updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Send periodic updates
            await asyncio.sleep(1)

            status = network_probe.get_status()
            metrics_summary = metrics.get_summary()
            cache_stats = semantic_cache.get_stats()

            await websocket.send_json({
                "type": "status_update",
                "network": status.model_dump(),
                "metrics": metrics_summary,
                "cache": cache_stats,
                "timestamp": datetime.utcnow().isoformat(),
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)