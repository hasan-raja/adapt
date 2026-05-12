#!/usr/bin/env python3
"""
ADAPT Demo Script
Simulates the "Holy Shit" demo scenario from the pitch.
"""

import asyncio
import httpx
from datetime import datetime


BASE_URL = "http://localhost:8000"


async def clear_state():
    """Reset ADAPT to clean state."""
    async with httpx.AsyncClient() as client:
        await client.delete(f"{BASE_URL}/cache")
        print("✓ Cache cleared")


async def set_tier(tier: str):
    """Set network tier."""
    async with httpx.AsyncClient() as client:
        await client.get(f"{BASE_URL}/network/status?force_tier={tier}")
        status = await client.get(f"{BASE_URL}/network/status")
        data = status.json()
        print(f"  → Now on {tier.upper()} ({data['bandwidth_kbps']} kbps, {data['latency_ms']}ms latency)")


async def send_request(message: str, description: str = ""):
    """Send a request through ADAPT."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/adapt",
            json={"message": message, "history": []},
        )
        data = response.json()

        print(f"\n{'─' * 50}")
        print(f"Message: {message[:60]}{'...' if len(message) > 60 else ''}")
        if description:
            print(f"Scenario: {description}")
        print(f"{'─' * 50}")
        print(f"  Tier: {data['tier_used'].upper()}")
        print(f"  Model: {data['tier_used'].upper()}")
        print(f"  Compression: {(1 - data['compression_ratio']) * 100:.0f}% reduction")
        print(f"  Tokens: {data['tokens_used']}")
        print(f"  Cost: ₹{data['cost_rs']:.2f}")
        print(f"  Cache Hit: {'YES 🎯' if data['cache_hit'] else 'NO'}")
        print(f"  Quality Score: {data['quality_score']:.2f}")
        print(f"  Adaptation Events: {data['adaptation_count']}")
        print()
        print(f"Response: {data['response'][:100]}...")


async def main():
    print("\n" + "=" * 60)
    print("⚡ ADAPT - Adaptive AI QoS Infrastructure Demo")
    print("=" * 60)

    await clear_state()

    # Demo Part 1: Full quality on WiFi
    print("\n📶 STEP 1: User on WiFi - Full Quality")
    print("─" * 50)
    await set_tier("wifi")

    await send_request(
        "I need to transfer money from my savings account to my friend's account. What are the steps involved?",
        description="Full-quality request on WiFi"
    )

    await asyncio.sleep(1)

    # Demo Part 2: Network drops to 2G
    print("\n" + "=" * 60)
    print("📉 STEP 2: Network drops to 2G - ADAPT activates!")
    print("=" * 60)
    await set_tier("2g")

    await send_request(
        "How do I transfer money to another account?",
        description="Compressed request on 2G"
    )

    # Demo Part 3: Same question, cache hit
    print("\n" + "=" * 60)
    print("🔁 STEP 3: Similar question - Cache hit!")
    print("=" * 60)

    await send_request(
        "Transfer money to friend account",
        description="Cache hit - similar semantic content"
    )

    # Demo Part 4: Recovery
    print("\n" + "=" * 60)
    print("📈 STEP 4: User moves to 4G - Quality restored")
    print("=" * 60)
    await set_tier("4g")

    await send_request(
        "I want to send money to someone using UPI. Can you guide me?",
        description="Recovery on 4G"
    )

    # Final metrics
    print("\n" + "=" * 60)
    print("📊 FINAL METRICS")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        metrics = await client.get(f"{BASE_URL}/metrics")
        cache = await client.get(f"{BASE_URL}/cache/stats")

        m = metrics.json()
        c = cache.json()

        print(f"\n  Total Requests: {m['requests_served']}")
        print(f"  Total Cost: ₹{m['total_cost_rs']:.2f}")
        print(f"  Cached Responses: {m['cache_hit_rate'] * 100:.0f}%")
        print(f"  Adaptation Events: {m['adaptation_events']}")
        print(f"\n  Cache Efficiency:")
        print(f"    - Hits: {c['hits']}")
        print(f"    - Misses: {c['misses']}")
        print(f"    - Hit Rate: {c['hit_rate'] * 100:.0f}%")

    print("\n" + "=" * 60)
    print("✅ Demo complete! ADAPT handled 4 scenarios:")
    print("   1. Full quality on WiFi")
    print("   2. Graceful degradation on 2G")
    print("   3. Cache hit for repeated query")
    print("   4. Recovery on better network")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())