# ADAPT Benchmark Snapshot

These are prototype benchmark targets and sample demo observations. They are meant to be rerun with `eval_prompts.json` before interviews and clearly separate ADAPT behavior from the standard baseline.

## Current Demo Measurements

| Tier | Standard behavior | ADAPT behavior | Expected token reduction | Cache policy |
| --- | --- | --- | ---: | --- |
| WiFi | Full prompt, largest model | No compression, high-quality route | 0-5% | Cache allowed for general prompts |
| 4G | Full prompt, largest model | Light compression, mid/large model | 10-20% | Cache allowed for general prompts |
| 3G | High latency on standard path | Medium compression, faster model | 30-45% | Cache skipped for sensitive prompts |
| 2G | Timeout-prone standard path | Aggressive/general or medium/sensitive compression | 45-65% | Cache skipped for health/finance/identity |
| Repeat general query | Repeated LLM call | Semantic cache hit | 90%+ | Only when non-sensitive |

## Interview Benchmark Plan

Run each prompt in `eval_prompts.json` through:

1. `/standard`
2. `/adapt`
3. `/adapt` again for cache behavior

Record:

- end-to-end latency
- tokens used
- cost estimate
- selected tier/model/compression
- cache hit or safety skip
- manual answer quality rating from 1-5

## Claim Boundary

ADAPT currently proves request-boundary QoS adaptation. Mid-stream network switching is represented by the new `/adapt/stream` endpoint as a foundation, but active mid-generation cancellation and continuation routing are future work.
