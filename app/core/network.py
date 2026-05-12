"""
Network detection and simulation.
Handles actual network probing + simulated network tiers for demo.
"""

import asyncio
import random
import time
from collections import deque
from typing import Optional
from app.models import NetworkTier, NetworkStatus, CompressionLevel


# Network tier configuration
TIER_CONFIG: dict[NetworkTier, dict] = {
    NetworkTier.WIFI: {
        "bandwidth_kbps": 10000,
        "latency_ms": 30,
        "model_size": "30B+",
        "compression": CompressionLevel.NONE,
    },
    NetworkTier.TIER_4G: {
        "bandwidth_kbps": 2000,
        "latency_ms": 100,
        "model_size": "7B",
        "compression": CompressionLevel.LIGHT,
    },
    NetworkTier.TIER_3G: {
        "bandwidth_kbps": 500,
        "latency_ms": 500,
        "model_size": "3B",
        "compression": CompressionLevel.MEDIUM,
    },
    NetworkTier.TIER_2G: {
        "bandwidth_kbps": 50,
        "latency_ms": 2000,
        "model_size": "1B",
        "compression": CompressionLevel.AGGRESSIVE,
    },
}


class NetworkProbe:
    """
    Manages network state with rolling averages to prevent flapping.
    Uses hysteresis: don't switch tiers until deviation persists.
    """

    def __init__(self):
        self._current_tier = NetworkTier.WIFI
        self._target_tier = NetworkTier.WIFI
        self._bandwidth_history = deque(maxlen=10)
        self._latency_history = deque(maxlen=10)
        self._tier_stability_counter = 0
        self._stability_threshold = 3  # Need 3 consistent readings to switch
        self._jitter_buffer = 0.2  # 20% jitter tolerance

    def _add_reading(self, bandwidth: float, latency: float) -> None:
        """Add a bandwidth/latency reading to history."""
        self._bandwidth_history.append(bandwidth)
        self._latency_history.append(latency)

    def _get_rolling_avg(self, values: deque) -> float:
        if not values:
            return 0.0
        return sum(values) / len(values)

    def _determine_tier(self, bandwidth: float, latency: float) -> NetworkTier:
        """
        Determine tier from bandwidth/latency with hysteresis.
        """
        # Use rolling averages if we have enough data
        avg_bandwidth = self._get_rolling_avg(self._bandwidth_history)
        avg_latency = self._get_rolling_avg(self._latency_history)

        # Apply jitter buffer for stability
        effective_bandwidth = bandwidth * (1 + random.uniform(-self._jitter_buffer, self._jitter_buffer))
        effective_latency = latency * (1 + random.uniform(-self._jitter_buffer, self._jitter_buffer))

        # Tiers ordered from worst to best
        if effective_bandwidth < 100 or effective_latency > 2000:
            return NetworkTier.TIER_2G
        elif effective_bandwidth < 500 or effective_latency > 500:
            return NetworkTier.TIER_3G
        elif effective_bandwidth < 2000 or effective_latency > 100:
            return NetworkTier.TIER_4G
        else:
            return NetworkTier.WIFI

    async def update_reading(self, bandwidth: float, latency: float) -> NetworkTier:
        """
        Update with new reading and return stable tier.
        """
        # Add to history
        self._add_reading(bandwidth, latency)

        # Determine raw tier
        detected_tier = self._determine_tier(bandwidth, latency)

        # Hysteresis: only switch if tier is consistent
        if detected_tier == self._target_tier:
            self._tier_stability_counter += 1
        else:
            self._tier_stability_counter = 1
            self._target_tier = detected_tier

        # Switch only if stable
        if self._tier_stability_counter >= self._stability_threshold:
            if self._current_tier != self._target_tier:
                self._current_tier = self._target_tier
            self._tier_stability_counter = 0

        return self._current_tier

    def get_status(self, force_tier: Optional[NetworkTier] = None) -> NetworkStatus:
        """Get current network status."""
        tier = force_tier or self._current_tier
        config = TIER_CONFIG[tier]

        return NetworkStatus(
            tier=tier,
            bandwidth_kbps=config["bandwidth_kbps"],
            latency_ms=config["latency_ms"],
            compression_level=config["compression"],
            model_size=config["model_size"],
            rolling_avg_bandwidth=self._get_rolling_avg(self._bandwidth_history),
            rolling_avg_latency=self._get_rolling_avg(self._latency_history),
        )

    def set_tier(self, tier: NetworkTier) -> None:
        """Force a specific tier (for simulation)."""
        self._current_tier = tier
        self._target_tier = tier
        self._tier_stability_counter = 0


class NetworkSimulator:
    """
    Simulates network conditions for demo/testing.
    """

    def __init__(self):
        self.probe = NetworkProbe()
        self._simulating = False
        self._simulation_task: Optional[asyncio.Task] = None

    async def start_simulation(self, sequence: list[tuple[NetworkTier, int]]) -> None:
        """
        Start network simulation sequence.
        Each tuple is (tier, duration_seconds).
        """
        self._simulating = True
        self._simulation_task = asyncio.create_task(self._run_simulation(sequence))

    async def _run_simulation(self, sequence: list[tuple[NetworkTier, int]]) -> None:
        """Run the simulation sequence."""
        for tier, duration in sequence:
            if not self._simulating:
                break
            self.probe.set_tier(tier)
            await asyncio.sleep(duration)

        # Return to WiFi by default
        self.probe.set_tier(NetworkTier.WIFI)
        self._simulating = False

    async def stop_simulation(self) -> None:
        """Stop the simulation."""
        self._simulating = False
        if self._simulation_task:
            self._simulation_task.cancel()
            try:
                await self._simulation_task
            except asyncio.CancelledError:
                pass

    async def simulate_reading(self, tier: NetworkTier) -> tuple[float, float]:
        """Simulate a single network reading for given tier."""
        config = TIER_CONFIG[tier]
        # Add realistic variance
        variance = random.uniform(0.8, 1.2)
        bandwidth = config["bandwidth_kbps"] * variance
        latency = config["latency_ms"] * variance
        return bandwidth, latency


# Global network probe instance
network_probe = NetworkProbe()
network_simulator = NetworkSimulator()