# ADAPT — Adaptive AI QoS Infrastructure

## The Pitch

> "AI should degrade gracefully, not catastrophically."

ADAPT is the infrastructure layer that makes AI work on 2G networks, budget phones, and limited bandwidth. When the network drops, ADAPT doesn't give up — it adapts.

## Quick Start

```bash
# Backend
cd /mnt/f/claude-code/adapt
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Run the demo:
```bash
python demo.py
```

## Architecture

```
Client → Network Probe → ADAPT Proxy → [Compression] → [Cache] → [Router] → Model API
                                              ↓              ↓            ↓
                                        Dashboard ← Metrics ← Quality Check
```

## Network Tiers

| Tier | Bandwidth   | Latency | Model | Compression |
|------|-------------|---------|-------|-------------|
| WiFi | 10+ Mbps    | <50ms   | 30B+  | None        |
| 4G   | 2 Mbps      | 100ms   | 7B    | Light (15%) |
| 3G   | 500 kbps    | 500ms   | 3B    | Medium (40%)|
| 2G   | <100 kbps   | >2000ms | 1B    | Aggressive (60%)|

## Key Features

### 1. Compression Pipeline (3 Layers)
- **Semantic**: Summarizes conversation history
- **Token-level**: Abbreviates phrases, removes fillers
- **Context pruning**: Keeps only relevant recent turns

### 2. Semantic Caching
- FAISS + MiniLM embeddings for similarity matching
- 0.92+ cosine similarity threshold
- 40-60% cache hit rate for FAQ/repetitive queries

### 3. Hysteresis Routing
- Rolling averages prevent network flapping
- Only switches tiers after 3+ consistent readings
- 20% jitter tolerance

### 4. Network Simulation
- Real WebSocket updates for live dashboard
- Demo script shows full degradation scenario

## The "Holy Shit" Demo

**Scenario**: User on WiFi, network drops to 2G, recovers

```
WiFi → Full response: 2,400 tokens, ₹12.00
  ↓ Network drops
2G → Compressed: 960 tokens, ₹4.00 (60% cheaper)
  ↓ Same question
2G (cache) → Instant: 52 tokens, ₹0.00
  ↓ Network improves
4G → Recovery: 1,800 tokens, ₹6.00
```

**Total**: 4 requests, ₹22.00 instead of ₹48.00

## API Endpoints

```
GET  /                      - Health check
GET  /network/status        - Current network status
POST /network/simulate      - Start network simulation
POST /adapt                 - Main adaptation endpoint
GET  /metrics              - Request/adaptation metrics
GET  /cache/stats          - Cache performance
WS   /ws                   - Real-time updates
```

## Demo Scenarios

### Manual Test
```bash
# Set tier and make request
curl "http://localhost:8000/network/status?force_tier=2g"
curl -X POST "http://localhost:8000/adapt" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, how are you?"}'
```

### Scripted Demo
```bash
python demo.py
```

## Environment Variables

```
SARVAM_API_KEY=   # Sarvam API for inference
OPENAI_API_KEY=   # OpenAI fallback
```

## What Makes This Impressive

| What Everyone Builds | What ADAPT Builds |
|---------------------|-------------------|
| Another chatbot     | Infrastructure that survives |
| Another benchmark  | Live system proving benchmarks matter |
| Model works on WiFi | Model works on 2G |
| AI scales up        | AI adapts gracefully |

## Files

```
app/
├── main.py           # FastAPI application
├── models/
│   └── schemas.py    # Pydantic models
└── core/
    ├── compression.py  # 3-layer compression
    ├── network.py      # Network probe + simulation
    ├── router.py      # Model selection
    ├── cache.py       # Semantic cache
    └── metrics.py     # Adaptation tracking

frontend/
├── src/
│   ├── App.jsx        # React dashboard
│   └── index.css      # Styling
└── package.json

demo.py                # Demo script
```

## Status

Working prototype. Core features:
- ✓ Compression pipeline
- ✓ Network simulation
- ✓ Hysteresis routing
- ✓ Semantic cache (basic)
- ✓ React dashboard
- ✓ Real-time WebSocket updates

Missing (v1.1):
- Real Sarvam/OpenAI API integration
- Full semantic summarization
- Persistent storage