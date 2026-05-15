# ADAPT — Adaptive AI QoS Infrastructure

## Quick Start
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Architecture
```

Client → Network Probe → ADAPT Proxy → [Compression] → [Cache] → [Router] → Model API
                          ↓               ↓            ↓
                     Dashboard ← Metrics ← Quality Check
```

## Key Files
- `app/main.py` - FastAPI application root
- `app/core/compression.py` - 3-layer compression pipeline
- `app/core/router.py` - Network-aware model selection
- `app/core/cache.py` - Semantic caching with embeddings
- `app/core/network.py` - Network detection and simulation
- `frontend/` - React dashboard

## Network Tiers
| Tier | Bandwidth | Latency | Model | Compression |
|------|-----------|---------|-------|-------------|
| 2G   | <100kbps  | >2000ms | 1B    | aggressive  |
| 3G   | <500kbps  | >500ms  | 3B    | medium      |
| 4G   | <2Mbps    | >100ms  | 7B    | light       |
| WiFi | 10Mbps+   | <50ms   | 30B+  | none        |

## Environment Variables
```
GROQ_API_KEY=your_key_here
```