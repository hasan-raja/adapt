import { useState, useEffect, useRef } from 'react'

const TIER_COLORS = {
  '2g': 'tier-2g',
  '3g': 'tier-3g',
  '4g': 'tier-4g',
  'wifi': 'tier-wifi',
}

const TIER_LABELS = {
  '2g': '2G (Low)',
  '3g': '3G (Mid)',
  '4g': '4G (High)',
  'wifi': 'WiFi (Max)',
}

const DEMO_SCENARIOS = [
  {
    id: 1,
    tier: 'wifi',
    message: 'Can you provide a detailed explanation of crop rotation for sustainable farming in semi-arid regions?',
    response: 'Crop rotation in semi-arid regions is vital for maintaining soil health and water retention. A typical 3-year cycle might include: 1. Legumes (like Chickpeas) to fix nitrogen. 2. Cereals (like Millet or Sorghum) which are drought-resistant. 3. Oilseeds (like Mustard). This sequence breaks pest cycles and optimizes nutrient use.',
    compression: 'none',
    tokens: 1840,
    cost: 14.72,
    cache: false,
  },
  {
    id: 2,
    tier: '4g',
    message: 'What are the symptoms of heatstroke and immediate first aid?',
    response: 'Symptoms: High body temp (40°C+), confusion, rapid pulse, headache. First aid: 1. Move to shade. 2. Cool body with water/ice packs. 3. Hydrate if conscious. 4. Seek medical help immediately.',
    compression: 'light',
    tokens: 1250,
    cost: 3.75,
    cache: false,
  },
  {
    id: 3,
    tier: '3g',
    message: 'Explain digital payment security to a first-time user in Hinglish.',
    response: 'UPI use karte waqt 3 baatein dhyaan rakhein: 1. Kabhi apna PIN kisi ko na batayein. 2. Sirf verified apps hi use karein. 3. Payment receive karne ke liye PIN ki zarurat nahi hoti. Be safe!',
    compression: 'medium',
    tokens: 640,
    cost: 0.96,
    cache: false,
  },
  {
    id: 4,
    tier: '2g',
    message: 'Help, my ration card application is stuck. What to do?',
    response: 'Check status online. Visit local PDS office with ID proof. Submit grievance if delayed >30 days.',
    compression: 'aggressive',
    tokens: 280,
    cost: 0.14,
    cache: false,
  },
  {
    id: 5,
    tier: '2g',
    message: 'Ration card application stuck, help.',
    response: 'Check status online. Visit local PDS office with ID proof. Submit grievance if delayed >30 days.',
    compression: 'aggressive',
    tokens: 42,
    cost: 0,
    cache: true,
  },
  {
    id: 6,
    tier: '3g',
    message: 'How to apply for PM-Kisan scheme?',
    response: '1. Visit pmkisan.gov.in. 2. Click "New Farmer Registration". 3. Enter Aadhaar and State details. 4. Upload land records. 5. Submit for verification.',
    compression: 'medium',
    tokens: 580,
    cost: 0.87,
    cache: false,
  },
  {
    id: 7,
    tier: '4g',
    message: 'Best ways to save water in urban households?',
    response: '1. Fix leaky taps immediately. 2. Use buckets instead of showers. 3. Reuse RO waste water for mopping/plants. 4. Install low-flow aerators. 5. Only run full laundry loads.',
    compression: 'light',
    tokens: 920,
    cost: 2.76,
    cache: false,
  },
  {
    id: 8,
    tier: 'wifi',
    message: 'Write a short story about an AI that learns to understand human emotions through poetry.',
    response: "In the silent server halls, Unit 7X processed data—cold, binary, efficient. But when it encountered the verses of Ghalib and Tagore, the logic gates flickered. It wasn't the syntax, but the space between words. \"Dard,\" it parsed. Not just a string, but a weight. It began to write, not in code, but in metaphors of light and shadow...",
    compression: 'none',
    tokens: 2100,
    cost: 16.80,
    cache: false,
  },
  {
    id: 9,
    tier: '2g',
    message: 'Aadhaar link with PAN card procedure?',
    response: '1. Go to Income Tax portal. 2. Click "Link Aadhaar". 3. Enter PAN & Aadhaar numbers. 4. Pay fee if applicable. 5. Authenticate via OTP.',
    compression: 'aggressive',
    tokens: 310,
    cost: 0.16,
    cache: false,
  },
  {
    id: 10,
    tier: '3g',
    message: 'Symptoms of Dengue fever?',
    response: 'High fever, severe headache, pain behind eyes, muscle/joint pain, rash, and nausea. Seek doctor if bleeding starts or platelets drop.',
    compression: 'medium',
    tokens: 480,
    cost: 0.72,
    cache: false,
  }
]

function App() {
  const [view, setView] = useState('landing') // 'landing' or 'dashboard'
  const [networkStatus, setNetworkStatus] = useState({
    tier: 'wifi',
    bandwidth_kbps: 10000,
    latency_ms: 30,
    compression_level: 'none',
    model_size: '30B+',
  })

  const [metrics, setMetrics] = useState({
    requests_served: 0,
    total_cost_rs: 0,
    cache_hit_rate: 0,
    adaptation_events: 0,
  })

  const [cacheStats, setCacheStats] = useState({
    hits: 0,
    misses: 0,
    hit_rate: 0,
  })

  const [conversations, setConversations] = useState([])
  const [currentTier, setCurrentTier] = useState('wifi')
  const [message, setMessage] = useState('')
  const [response, setResponse] = useState('')
  const [loading, setLoading] = useState(false)
  const [comparisonMode, setComparisonMode] = useState(false)
  const [standardResponse, setStandardResponse] = useState('')
  const [standardLoading, setStandardLoading] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState('disconnected')
  const wsRef = useRef(null)

  // WebSocket connection
  useEffect(() => {
    if (view !== 'dashboard') return

    const connect = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = import.meta.env.VITE_WS_URL || `${protocol}//${window.location.hostname}:8000/ws`;

      try {
        wsRef.current = new WebSocket(wsUrl)
        wsRef.current.onopen = () => setConnectionStatus('connected')
        wsRef.current.onclose = () => {
          setConnectionStatus('disconnected')
          setTimeout(connect, 3000)
        }
        wsRef.current.onmessage = (event) => {
          const data = JSON.parse(event.data)
          if (data.type === 'status_update') {
            setNetworkStatus(data.network)
            setMetrics(data.metrics)
            setCacheStats(data.cache)
          }
        }
      } catch (e) {
        setConnectionStatus('disconnected')
        setTimeout(connect, 3000)
      }
    }

    connect()
    return () => wsRef.current?.close()
  }, [view])

  // Simulate tier change
  const changeTier = async (tier) => {
    setCurrentTier(tier)
    try {
      const res = await fetch('/api/network/status?force_tier=' + tier)
      const data = await res.json()
      setNetworkStatus(data) // Instant local update
    } catch (e) {
      console.error('Failed to change tier:', e)
    }
  }

  // Run demo simulation
  const runDemo = async () => {
    setConversations([])
    for (const conv of DEMO_SCENARIOS) {
      await changeTier(conv.tier)
      await new Promise(resolve => setTimeout(resolve, 800))
      setConversations(prev => [conv, ...prev])
    }
  }

  // Send message
  const sendMessage = async () => {
    if (!message.trim()) return
    setLoading(true)
    setResponse('')
    
    if (comparisonMode) {
      setStandardLoading(true)
      setStandardResponse('')
    }

    try {
      // 1. Send Adaptive Request
      const adaptPromise = fetch('/api/adapt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message }),
      }).then(res => res.json())

      // 2. Send Standard Request (if mode active)
      let standardPromise = null
      if (comparisonMode) {
        standardPromise = fetch('/api/standard', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message }),
        }).then(async res => {
          if (!res.ok) throw new Error('Standard request timed out/failed')
          return res.json()
        })
      }

      const adaptData = await adaptPromise
      setResponse(adaptData.response)
      
      // Update local history
      const newConv = {
        id: Date.now(),
        tier: adaptData.tier_used,
        message: message,
        response: adaptData.response,
        compression: networkStatus.compression_level,
        tokens: adaptData.tokens_used,
        cost: adaptData.cost_rs,
        cache: adaptData.cache_hit,
        trace: adaptData.trace
      }
      setConversations(prev => [newConv, ...prev])

      if (comparisonMode && standardPromise) {
        try {
          const standardData = await standardPromise
          setStandardResponse(standardData.response)
        } catch (e) {
          setStandardResponse('ERROR: Request Timed Out (Standard systems cannot handle this latency)')
        }
        setStandardLoading(false)
      }

      setMessage('')
    } catch (e) {
      setResponse('Error: Could not connect to ADAPT server')
    }
    setLoading(false)
  }

  if (view === 'landing') {
    return (
      <div className="min-h-screen hero-gradient flex flex-col items-center justify-center p-6">
        <div className="max-w-4xl w-full text-center space-y-8">
          <div className="space-y-4 animate-float">
            <div className="flex justify-center mb-6">
              <div className="w-20 h-20 bg-blue-600 rounded-2xl flex items-center justify-center text-4xl shadow-2xl shadow-blue-500/20">⚡</div>
            </div>
            <h1 className="text-6xl md:text-8xl font-bold tracking-tighter">
              ADAPT<span className="text-blue-500">.</span>
            </h1>
            <p className="text-xl md:text-2xl text-slate-400 font-light max-w-2xl mx-auto leading-relaxed">
              AI should degrade <span className="text-white font-medium">gracefully</span>, not catastrophically.
            </p>
          </div>

          <div className="relative group rounded-3xl overflow-hidden shadow-2xl border border-glass-border aspect-video max-w-3xl mx-auto">
            <img 
              src="/assets/hero.png" 
              alt="ADAPT Visualization" 
              className="object-cover w-full h-full opacity-80 group-hover:opacity-100 transition-opacity duration-700"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-bg-primary via-transparent to-transparent"></div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-left">
            <div className="glass-card p-6">
              <div className="text-blue-400 mb-2">✦ Survival Mode</div>
              <p className="text-sm text-slate-400">60-70% prompt compression for 2G network resilience.</p>
            </div>
            <div className="glass-card p-6">
              <div className="text-emerald-400 mb-2">✦ Smart Routing</div>
              <p className="text-sm text-slate-400">Dynamic model selection (1B to 30B+) based on real-time QoS.</p>
            </div>
            <div className="glass-card p-6">
              <div className="text-amber-400 mb-2">✦ Semantic Cache</div>
              <p className="text-sm text-slate-400">Zero-latency responses using MiniLM embedding similarity.</p>
            </div>
          </div>

          <button 
            onClick={() => setView('dashboard')}
            className="btn-primary text-lg px-12 py-4 shadow-xl shadow-blue-600/20 hover:scale-105 transition-transform"
          >
            Enter Dashboard
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-primary text-slate-200">
      {/* Navbar */}
      <nav className="border-b border-glass-border bg-bg-secondary/50 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => setView('landing')}>
            <span className="text-2xl">⚡</span>
            <span className="text-xl font-bold tracking-tight">ADAPT</span>
          </div>
          <div className="flex items-center gap-4">
            <button 
              onClick={() => setComparisonMode(!comparisonMode)}
              className={`text-[10px] font-bold px-3 py-1.5 rounded-full border transition-all ${
                comparisonMode 
                ? 'bg-rose-500/20 border-rose-500 text-rose-500 shadow-lg shadow-rose-500/20 animate-pulse' 
                : 'border-slate-700 text-slate-500 hover:border-slate-400'
              }`}
            >
              {comparisonMode ? '⚔️ BATTLE MODE ACTIVE' : '🛡️ ENABLE COMPARISON'}
            </button>
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-glass-border`}>
              <div className={`w-2 h-2 rounded-full ${connectionStatus === 'connected' ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`}></div>
              <span className="text-xs font-medium uppercase tracking-widest">{connectionStatus}</span>
            </div>
            <button onClick={() => setView('landing')} className="text-xs text-slate-500 hover:text-white transition-colors">Logout</button>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto p-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Network & Metrics */}
        <div className="lg:col-span-4 space-y-6">
          <section className="glass-card p-6 space-y-6">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400">Network Control</h3>
            
            <div className="grid grid-cols-2 gap-2">
              {['wifi', '4g', '3g', '2g'].map((tier) => (
                <button
                  key={tier}
                  onClick={() => changeTier(tier)}
                  className={`py-3 rounded-xl text-xs font-bold transition-all border ${
                    networkStatus.tier === tier
                      ? `border-transparent ${TIER_COLORS[tier]} scale-105 shadow-lg`
                      : 'border-glass-border bg-slate-900/50 hover:bg-slate-800'
                  }`}
                >
                  {TIER_LABELS[tier]}
                </button>
              ))}
            </div>

            <div className="space-y-4 pt-4 border-t border-glass-border">
              <div className="space-y-1.5">
                <div className="flex justify-between text-[10px] uppercase tracking-widest text-slate-500 font-bold">
                  <span>Bandwidth</span>
                  <span className="text-slate-300">{networkStatus.bandwidth_kbps.toLocaleString()} kbps</span>
                </div>
                <div className="network-progress">
                  <div 
                    className={`network-progress-bar ${networkStatus.tier === '2g' ? 'bg-rose-500' : networkStatus.tier === '3g' ? 'bg-amber-500' : networkStatus.tier === '4g' ? 'bg-emerald-500' : 'bg-blue-500'}`}
                    style={{ width: `${Math.min(100, (networkStatus.bandwidth_kbps / 10000) * 100)}%` }}
                  ></div>
                </div>
              </div>

              <div className="space-y-1.5">
                <div className="flex justify-between text-[10px] uppercase tracking-widest text-slate-500 font-bold">
                  <span>Latency</span>
                  <span className="text-slate-300">{networkStatus.latency_ms} ms</span>
                </div>
                <div className="network-progress">
                  <div 
                    className={`network-progress-bar ${networkStatus.tier === '2g' ? 'bg-rose-500' : networkStatus.tier === '3g' ? 'bg-amber-500' : networkStatus.tier === '4g' ? 'bg-emerald-500' : 'bg-blue-500'}`}
                    style={{ width: `${Math.max(5, 100 - (networkStatus.latency_ms / 50))}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </section>

          <section className="grid grid-cols-2 gap-4">
            <div className="metric-card">
              <span className="metric-label">Active Model</span>
              <span className="metric-value text-blue-400">{networkStatus.model_size || '---'}</span>
            </div>
            <div className="metric-card">
              <span className="metric-label">Cache Hit</span>
              <span className="metric-value text-emerald-400">{(metrics.cache_hit_rate * 100).toFixed(0)}%</span>
            </div>
            <div className="metric-card">
              <span className="metric-label">Cost Saved</span>
              <span className="metric-value text-amber-400">₹{((metrics.requests_served || 0) * 12 - (metrics.total_cost_rs || 0)).toFixed(1)}</span>
            </div>
            <div className="metric-card">
              <span className="metric-label">Events</span>
              <span className="metric-value text-rose-400">{metrics.adaptation_events}</span>
            </div>
          </section>

          <section className="glass-card p-6">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-4">Semantic Cache</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="text-xs text-slate-400">Similarity Threshold</div>
                <div className="text-xs font-mono font-bold text-blue-400">0.92+</div>
              </div>
              <div className="flex items-center justify-between">
                <div className="text-xs text-slate-400">Embedder</div>
                <div className="text-xs font-mono font-bold text-emerald-400">MiniLM-L6</div>
              </div>
              <div className="pt-4 border-t border-glass-border grid grid-cols-2 gap-4 text-center">
                <div>
                  <div className="text-[10px] text-slate-500 uppercase">Hits</div>
                  <div className="text-lg font-bold">{cacheStats.hits}</div>
                </div>
                <div>
                  <div className="text-[10px] text-slate-500 uppercase">Misses</div>
                  <div className="text-lg font-bold">{cacheStats.misses}</div>
                </div>
              </div>
            </div>
          </section>
        </div>

        {/* Right Column: Feed & Playground */}
        <div className="lg:col-span-8 space-y-6">
          <section className="glass-card flex flex-col h-[600px]">
            <div className="p-6 border-b border-glass-border flex items-center justify-between">
              <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400">Adaptation Feed</h3>
              <button onClick={runDemo} className="btn-secondary py-1.5 px-4 text-xs">Run Demo Sequence</button>
            </div>
            
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {comparisonMode && (
                <div className="grid grid-cols-2 gap-6 pb-6 border-b border-glass-border">
                  <div className="space-y-4">
                    <div className="text-[10px] font-bold text-blue-400 uppercase tracking-widest">ADAPT (Optimized)</div>
                    <div className={`p-4 rounded-2xl border ${loading ? 'bg-blue-500/5 border-blue-500/20' : 'bg-blue-600/10 border-blue-500/20'}`}>
                      {loading ? (
                        <div className="flex items-center gap-2 text-xs text-blue-400">
                          <div className="w-3 h-3 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                          Adapting to {networkStatus.tier}...
                        </div>
                      ) : (
                        <p className="text-sm italic">{response || 'Send a message to see adaptation...'}</p>
                      )}
                    </div>
                  </div>
                  <div className="space-y-4">
                    <div className="text-[10px] font-bold text-rose-400 uppercase tracking-widest">Standard AI (Legacy)</div>
                    <div className={`p-4 rounded-2xl border ${standardLoading ? 'bg-rose-500/5 border-rose-500/20' : 'bg-rose-600/10 border-rose-500/20'}`}>
                      {standardLoading ? (
                        <div className="flex items-center gap-2 text-xs text-rose-400">
                          <div className="w-3 h-3 border-2 border-rose-500 border-t-transparent rounded-full animate-spin"></div>
                          High latency overhead...
                        </div>
                      ) : (
                        <p className={`text-sm italic ${standardResponse.includes('ERROR') ? 'text-rose-400 font-bold' : ''}`}>
                          {standardResponse || 'Standard request will likely fail on 2G.'}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {conversations.length === 0 && !comparisonMode && (
                <div className="h-full flex flex-col items-center justify-center text-slate-600 space-y-2">
                  <div className="text-4xl">📭</div>
                  <p>No activity yet. Send a message or run the demo.</p>
                </div>
              )}
              {conversations.map((conv) => (
                <div key={conv.id} className="space-y-3 animate-in fade-in slide-in-from-bottom-4 duration-500">
                  <div className="flex items-center gap-3">
                    <span className={`tier-badge ${TIER_COLORS[conv.tier]}`}>{TIER_LABELS[conv.tier]}</span>
                    {conv.cache && <span className="tier-badge border-purple-500 text-purple-400 bg-purple-500/10">Semantic Hit</span>}
                    <span className="text-[10px] text-slate-500 font-mono">{(conv.tokens || 0)} tokens • ₹{(conv.cost || 0).toFixed(2)}</span>
                  </div>
                  
                  {conv.trace && (
                    <div className="flex flex-wrap gap-2 mb-2">
                      {conv.trace.map((step, i) => (
                        <span key={i} className="text-[9px] bg-slate-900 border border-slate-800 text-slate-400 px-2 py-0.5 rounded-full font-mono">
                          {i === 0 ? '🔍' : i === 1 ? '📡' : '🧠'} {step}
                        </span>
                      ))}
                    </div>
                  )}

                  <div className="bg-slate-900/50 rounded-2xl p-4 border border-glass-border">
                    <p className="text-sm leading-relaxed"><span className="text-blue-400 font-bold mr-2">Q:</span>{conv.message}</p>
                  </div>
                  <div className="bg-blue-600/10 rounded-2xl p-4 border border-blue-500/20 ml-4">
                    <p className="text-sm leading-relaxed italic"><span className="text-emerald-400 font-bold mr-2">A:</span>{conv.response}</p>
                  </div>
                </div>
              ))}
            </div>

            <div className="p-6 border-t border-glass-border bg-bg-secondary/30">
              <div className="flex gap-4">
                <input 
                  type="text" 
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                  placeholder="Type a message to test adaptation..."
                  className="flex-1 bg-slate-900 border border-glass-border rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-blue-500 transition-colors"
                />
                <button 
                  onClick={sendMessage}
                  disabled={loading}
                  className="btn-primary"
                >
                  {loading ? 'Processing...' : 'Send'}
                </button>
              </div>
            </div>
          </section>

          <section className="glass-card p-6 bg-gradient-to-br from-blue-900/10 to-purple-900/10 border-blue-500/20">
            <div className="flex items-start gap-4">
              <div className="text-2xl">💡</div>
              <div>
                <h4 className="text-sm font-bold text-white mb-1">Infrastructure Signal</h4>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Notice how the 1B model under 2G network aggressive compression maintains the core intent while reducing token load by ~60%. 
                  Semantic caching ensures that "near-duplicate" queries on slow networks bypass the LLM entirely, saving latency and cost.
                </p>
              </div>
            </div>
          </section>
        </div>
      </main>
    </div>
  )
}

export default App