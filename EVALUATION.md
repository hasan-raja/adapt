# ADAPT Prototype Evaluation Notes

ADAPT is a working prototype of an adaptive AI QoS layer. It is intentionally built to demonstrate the product and infrastructure idea quickly, while keeping the implementation boundaries clear.

## What is real today

- FastAPI gateway that accepts chat requests through `/adapt`.
- Network tier selection from forced demo tiers, browser network hints, active browser probes, or server-side probe readings.
- Hysteresis-based tier stabilization in `NetworkProbe`.
- Prompt compression by compression level.
- Conversation history compression before model calls.
- Model routing by network tier and task type.
- Session memory with `session_id`, so model switches preserve conversation state at the application layer.
- FAISS + MiniLM semantic cache with exact-match fallback.
- Cache safety guard that avoids reuse for sensitive medical, financial, identity, and credential-related prompts.
- React dashboard with active probe controls, live WebSocket metrics, and live backend-driven demo sequence.
- `/adapt/stream` SSE foundation for streaming-first adaptation work.

## What is simulated

- Manual tier switching in the dashboard is still a demo control.
- Network presets such as 2G, 3G, 4G, and WiFi use representative bandwidth and latency values.
- If no provider API key is configured, the model response falls back to tier-specific demo text.
- The `/standard` endpoint is a comparison baseline, not a production competitor benchmark.
- Mid-response network switching is not complete yet; current adaptation happens at request boundaries.

## What should be benchmarked next

| Area | Next measurement |
| --- | --- |
| Latency | p50/p95 end-to-end latency per tier with and without ADAPT |
| Cost | input/output token cost per request across repeated workflows |
| Quality | answer similarity and human rating after compression |
| Cache safety | false cache-hit rate on personalized and time-sensitive prompts |
| Routing | quality/cost tradeoff by task type, model, and network tier |

## Next production steps

- Extend the active probe with upload and packet-loss measurements.
- Add full streaming cancellation, compressed continuation, and partial-output fallback for unstable connections.
- Use provider-native tokenizers for accurate token and cost accounting.
- Store cache entries with policy metadata: user scope, freshness TTL, domain, and sensitivity.
- Add automated evals for Hinglish and Indic-language prompts.
