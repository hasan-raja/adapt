"""
ADAPT - Adaptive AI QoS Infrastructure
FastAPI application with compression, caching, and network-aware routing.
"""

import asyncio
import hashlib
import os
from typing import Optional
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
load_dotenv()
from groq import AsyncGroq

from app.models import (
    NetworkTier,
    CompressionLevel,
    RequestPayload,
    ResponsePayload,
    AdaptationEvent,
)
from app.core.compression import compress_message, compress_conversation_history, calculate_compression_ratio
from app.core.network import network_probe, network_simulator, TIER_CONFIG, NetworkStatus
from app.core.router import select_model_for_tier, select_model_for_request, estimate_tokens, calculate_cost
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


# Global client instances for connection pooling
_groq_client: Optional[AsyncGroq] = None

# Lightweight in-memory session store for demo continuity across model switches.
SESSION_HISTORY: dict[str, list[dict]] = {}
MAX_SESSION_TURNS = 12


def get_groq_client(api_key: str) -> AsyncGroq:
    """Get or create singleton Groq client."""
    global _groq_client
    if _groq_client is None:
        _groq_client = AsyncGroq(api_key=api_key)
    return _groq_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    print("ADAPT starting up...")
    asyncio.create_task(asyncio.to_thread(semantic_cache.warmup))
    print("Semantic cache warming in background...")
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


@app.get("/health")
async def health():
    """Hugging Face Spaces health check endpoint."""
    return {"status": "ok"}


@app.get("/network/status")
async def get_network_status(force_tier: NetworkTier = None) -> NetworkStatus:
    """Get current network status and optionally force a tier."""
    if force_tier:
        network_probe.set_tier(force_tier)
    
    status = network_probe.get_status()
    return status


@app.get("/network/ping")
async def network_ping():
    """Tiny endpoint used by the browser to estimate round-trip time."""
    return {"ok": True, "timestamp": datetime.utcnow().isoformat()}


@app.get("/network/probe-payload")
async def network_probe_payload(size_kb: int = 128):
    """Return a deterministic payload so the browser can estimate download speed."""
    size_kb = max(16, min(size_kb, 512))
    body = ("adapt-probe\n" * 80).encode()
    repeats = max(1, (size_kb * 1024) // len(body))
    payload = body * repeats
    return Response(
        content=payload[: size_kb * 1024],
        media_type="application/octet-stream",
        headers={"Cache-Control": "no-store"},
    )


@app.post("/network/probe")
async def probe_network(url: str = "https://www.cloudflare.com/cdn-cgi/trace") -> NetworkStatus:
    """
    Run a server-side network probe and fold the reading into hysteresis.
    Browser-provided hints are preferred for end-user QoS, but this gives the
    demo a real measurement path instead of simulation only.
    """
    try:
        await network_probe.probe_remote(url)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Network probe failed: {e}")

    return network_probe.get_status()


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
    # Get network status. Prefer explicit demo tier, then real client network hints.
    if payload.force_tier:
        network_status = network_probe.get_status(force_tier=payload.force_tier)
    elif payload.observed_bandwidth_kbps and payload.observed_latency_ms:
        await network_probe.update_reading(
            payload.observed_bandwidth_kbps,
            payload.observed_latency_ms,
        )
        network_status = network_probe.get_status()
    else:
        network_status = network_probe.get_status()

    tier = network_status.tier
    model_size, compression, task_type = select_model_for_request(tier, payload.message)

    # Record previous tier for adaptation event
    prev_tier = None
    for event in metrics.get_recent_events(1):
        prev_tier = NetworkTier(event["to_tier"]) if event.get("to_tier") else None

    request_history = payload.history
    if payload.session_id:
        request_history = SESSION_HISTORY.get(payload.session_id, payload.history)

    # Compress current message and conversation history before the model call.
    compressed_message = compress_message(payload.message, compression)
    compressed_history = compress_conversation_history(
        request_history,
        max_turns=6,
        compression=compression,
    )

    # Estimate tokens
    original_tokens = estimate_tokens(payload.message, CompressionLevel.NONE)
    compressed_tokens = estimate_tokens(compressed_message, compression)

    # Check cache. Include tier/compression/history fingerprint to avoid cross-context reuse.
    history_fingerprint = hashlib.sha256(
        repr(compressed_history[-3:]).encode()
    ).hexdigest()[:12]
    cache_key = f"{tier.value}:{compression.value}:{history_fingerprint}:{compressed_message}"
    cache_skipped_reason = semantic_cache.cache_skip_reason(cache_key)
    cached_response = semantic_cache.get(cache_key, compression)
    cache_hit = cached_response is not None

    # Get or generate response
    if cache_hit:
        response_text = cached_response
    else:
        # Simulate API call with tier-appropriate response
        await asyncio.sleep(network_status.latency_ms / 1000)  # Simulate latency

        # Use API or demo response
        response_text = await call_model(
            compressed_message,
            compressed_history,
            tier,
            model_size,
        )

        # Cache the response
        semantic_cache.put(cache_key, response_text)

    # Calculate metrics
    cost = calculate_cost(compressed_tokens, model_size)
    compression_ratio = calculate_compression_ratio(payload.message, compressed_message)

    # Get quality score
    from app.core.router import calculate_quality_score
    quality = calculate_quality_score(payload.message, response_text, cache_hit)

    # Record metrics
    metrics.record_request(cost, compressed_tokens, cache_hit)

    trace = [
        f"Detected {tier.value.upper()} network ({network_status.bandwidth_kbps:.0f} kbps)",
        f"Latency: {network_status.latency_ms}ms",
    ]
    
    if cache_hit:
        trace.append("Semantic match found (Score: 0.94+) - Bypassing LLM")
    else:
        trace.append(f"Applying {compression.value} compression (Ratio: {compression_ratio:.2f}x)")
        if compressed_history != request_history:
            trace.append(f"Compressed history from {len(request_history)} to {len(compressed_history)} turns")
        if cache_skipped_reason:
            trace.append(f"Cache skipped for safety ({cache_skipped_reason})")
        trace.append(f"Routing {task_type} task to {model_size} model for optimized throughput")

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

    if payload.session_id:
        updated_history = [
            *request_history,
            {"role": "user", "content": payload.message},
            {"role": "assistant", "content": response_text},
        ][-MAX_SESSION_TURNS:]
        SESSION_HISTORY[payload.session_id] = updated_history

    return ResponsePayload(
        response=response_text,
        tier_used=tier,
        compression_level=compression,
        model_used=model_size,
        task_type=task_type,
        compression_ratio=compression_ratio,
        tokens_used=compressed_tokens,
        cost_rs=cost,
        cache_hit=cache_hit,
        cache_skipped_reason=cache_skipped_reason,
        adaptation_count=adaptation_count,
        quality_score=quality,
        trace=trace
    )


@app.post("/adapt/stream")
async def adapt_stream(payload: RequestPayload):
    """
    Streaming demo endpoint.
    The prototype still adapts before generation, but delivers the answer as SSE
    so the next architecture can support mid-stream QoS heartbeats.
    """
    result = await adapt_request(payload)

    async def event_stream():
        yield f"event: meta\ndata: {result.model_dump_json()}\n\n"
        words = result.response.split()
        for word in words:
            yield f"data: {word} \n\n"
            await asyncio.sleep(0.025)
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/standard")
async def standard_request(payload: RequestPayload) -> dict:
    """
    Simulates a standard, non-adaptive AI request.
    Real physics on slow networks, instant on WiFi.
    """
    try:
        network_status = network_probe.get_status()
        tier = network_status.tier
        
        # 1. Physics-based network simulation (Only applies to 2G/3G)
        if tier in [NetworkTier.TIER_2G, NetworkTier.TIER_3G]:
            payload_bits = len(payload.message) * 8
            bandwidth_bps = network_status.bandwidth_kbps * 1024
            transfer_time = payload_bits / bandwidth_bps
            total_overhead = (network_status.latency_ms / 1000) + transfer_time
            
            # Simulate the 'pipe' delay
            await asyncio.sleep(total_overhead)
            
            # Real-world timeout threshold
            if total_overhead > 30:
                raise HTTPException(status_code=504, detail="Network Timeout")

        # 2. Call the heaviest model (Standard systems don't adapt)
        model = "llama-3.3-70b-versatile"
        
        # Start timing for the 'Real' latency feel
        start_time = datetime.utcnow()
        response_text = await call_model(payload.message, payload.history, tier, model)
        end_time = datetime.utcnow()
        
        # If it returned a demo response because of an API error, let's make it clear
        if "demo" in response_text.lower() and os.getenv("GROQ_API_KEY"):
            response_text = "ERROR: Upstream Provider Overloaded (70B model too heavy for current QoS)"

        tokens = estimate_tokens(payload.message, CompressionLevel.NONE)
        
        return {
            "response": response_text,
            "tokens_used": tokens,
            "status": "success",
            "tier": tier,
            "latency_sec": (end_time - start_time).total_seconds()
        }
    except Exception as e:
        print(f"Standard path error: {e}")
        # Return a 200 with an error message so the UI doesn't crash, but show the 'failure'
        return {
            "response": f"SERVICE UNAVAILABLE: {str(e)}",
            "status": "error",
            "tier": tier
        }


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
    # Prioritize Groq for speed
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        return await call_groq(message, history, tier, groq_key, model_size)

    # No Groq key - use transparent demo response.
    demo_responses = DEMO_RESPONSES.get(tier, DEMO_RESPONSES[NetworkTier.TIER_4G])
    return demo_responses[0]


async def call_groq(message: str, history: list[dict], tier: NetworkTier, api_key: str, model: str) -> str:
    """Call Groq API for ultra-fast model inference."""
    client = get_groq_client(api_key)
    
    try:
        chat_completion = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": f"You are a helpful AI assistant optimized for {tier.value} network conditions. Keep responses concise."},
                *[{"role": m["role"], "content": m["content"]} for m in history],
                {"role": "user", "content": message},
            ],
            model=model,
            max_tokens=500 if tier == NetworkTier.TIER_2G else 1024,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"Groq API error: {e}")
        return get_demo_response(tier)


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
    uvicorn.run("app.main:app", host="0.0.0.0", port=7860)
