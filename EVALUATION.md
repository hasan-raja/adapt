# ADAPT Prototype Evaluation Notes

ADAPT is a working prototype of an adaptive AI QoS layer. It is intentionally built to demonstrate the product and infrastructure idea quickly, while keeping the implementation boundaries clear.

## What is real today

- FastAPI gateway that accepts chat requests through `/adapt`.
- Network tier selection from forced demo tiers, browser network hints, or server-side probe readings.
- Hysteresis-based tier stabilization in `NetworkProbe`.
- Prompt compression by compression level.
- Conversation history compression before model calls.
- Model routing by network tier.
- FAISS + MiniLM semantic cache with exact-match fallback.
- Cache safety guard that avoids reuse for sensitive medical, financial, identity, and credential-related prompts.
- React dashboard with live WebSocket metrics and live backend-driven demo sequence.

## What is simulated

- Manual tier switching in the dashboard is still a demo control.
- Network presets such as 2G, 3G, 4G, and WiFi use representative bandwidth and latency values.
- If no provider API key is configured, the model response falls back to tier-specific demo text.
- The `/standard` endpoint is a comparison baseline, not a production competitor benchmark.

## What should be benchmarked next

| Area | Next measurement |
| --- | --- |
| Latency | p50/p95 end-to-end latency per tier with and without ADAPT |
| Cost | input/output token cost per request across repeated workflows |
| Quality | answer similarity and human rating after compression |
| Cache safety | false cache-hit rate on personalized and time-sensitive prompts |
| Routing | quality/cost tradeoff by task type, model, and network tier |

## Next production steps

- Replace browser network hints with an active client probe for upload, download, RTT, and packet loss.
- Add task-aware routing so medical, legal, coding, and summarization prompts have different quality floors.
- Add streaming responses and partial-output fallback for unstable connections.
- Use provider-native tokenizers for accurate token and cost accounting.
- Store cache entries with policy metadata: user scope, freshness TTL, domain, and sensitivity.
- Add automated evals for Hinglish and Indic-language prompts.
