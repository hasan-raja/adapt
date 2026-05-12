import { useState, useEffect, useRef, useCallback } from 'react'

const TIER_COLORS = {
  '2g': 'tier-2g',
  '3g': 'tier-3g',
  '4g': 'tier-4g',
  'wifi': 'tier-wifi',
}

const TIER_LABELS = {
  '2g': '2G',
  '3g': '3G',
  '4g': '4G',
  'wifi': 'WiFi',
}

const DEMO_MESSAGES = [
  {
    id: 1,
    tier: 'wifi',
    message: 'What is the meaning of life?',
    response: 'The meaning of life is a deeply personal philosophical question. Many philosophers, religions, and cultures have proposed various answers throughout human history. Some believe it is to seek happiness, others to fulfill a divine purpose, and some argue there is no inherent meaning at all.',
    compression: 'none',
    tokens: 2400,
    cost: 12.00,
    cache: false,
  },
  {
    id: 2,
    tier: '2g',
    message: 'What is life meaning?',
    response: 'Life meaning: personal philosophy. Many answers exist. Some seek happiness, others divine purpose, some say none.',
    compression: 'aggressive',
    tokens: 890,
    cost: 4.00,
    cache: false,
  },
  {
    id: 3,
    tier: '2g',
    message: 'What meaning of life?',
    response: 'Life meaning: personal philosophy. Many answers exist. Some seek happiness, others divine purpose, some say none.',
    compression: 'aggressive',
    tokens: 52,
    cost: 0,
    cache: true,
  },
]

function App() {
  const [networkStatus, setNetworkStatus] = useState({
    tier: 'wifi',
    bandwidth_kbps: 10000,
    latency_ms: 30,
    compression_level: 'none',
    model_size: '30B+',
  })

  const [metrics, setMetrics] = useState({
    requests_served: 3,
    total_cost_rs: 16.00,
    cache_hit_rate: 0.33,
    adaptation_events: 2,
  })

  const [cacheStats, setCacheStats] = useState({
    hits: 1,
    misses: 2,
    hit_rate: 0.33,
  })

  const [conversations, setConversations] = useState(DEMO_MESSAGES)
  const [currentTier, setCurrentTier] = useState('wifi')
  const [message, setMessage] = useState('')
  const [response, setResponse] = useState('')
  const [loading, setLoading] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState('disconnected')
  const wsRef = useRef(null)

  // WebSocket connection
  useEffect(() => {
    const connect = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsUrl = `${protocol}//${window.location.host}/ws`

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
  }, [])

  // Simulate tier change
  const changeTier = async (tier) => {
    setCurrentTier(tier)

    // Call the API
    try {
      await fetch('/api/network/status?force_tier=' + tier, { method: 'GET' })
    } catch (e) {
      console.error('Failed to change tier:', e)
    }
  }

  // Run demo simulation
  const runDemo = async () => {
    setConversations([])

    for (const conv of DEMO_MESSAGES) {
      await new Promise(resolve => setTimeout(resolve, 1500))
      setConversations(prev => [...prev, conv])
      setCurrentTier(conv.tier)
    }
  }

  // Send message
  const sendMessage = async () => {
    if (!message.trim()) return

    setLoading(true)
    setResponse('')

    try {
      const res = await fetch('/api/adapt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message }),
      })
      const data = await res.json()
      setResponse(data.response)
    } catch (e) {
      setResponse('Error: Could not connect to ADAPT server')
    }

    setLoading(false)
  }

  const compressionPercentage = {
    'none': 0,
    'light': 15,
    'medium': 40,
    'aggressive': 60,
  }[networkStatus.compression_level] || 0

  return (
    <div className="min-h-screen p-6 space-y-6">
      {/* Header */}
      <header className="flex items-center justify-between border-b border-adapt-border pb-4">
        <div className="flex items-center gap-3">
          <span className="text-4xl">⚡</span>
          <div>
            <h1 className="text-2xl font-bold">ADAPT</h1>
            <p className="text-xs text-gray-500">Adaptive AI QoS Infrastructure</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className={`tier-indicator ${TIER_COLORS[networkStatus.tier]}`}>
            {TIER_LABELS[networkStatus.tier]}
          </span>
          <span className={`text-xs ${connectionStatus === 'connected' ? 'text-green-500' : 'text-red-500'}`}>
            {connectionStatus === 'connected' ? '● LIVE' : '○ RECONNECTING'}
          </span>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Network Control */}
        <div className="lg:col-span-2 space-y-6">
          <div className="card">
            <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
              <span>📡</span> Network Control
            </h2>

            {/* Tier Selection */}
            <div className="grid grid-cols-4 gap-2 mb-4">
              {['wifi', '4g', '3g', '2g'].map((tier) => (
                <button
                  key={tier}
                  onClick={() => changeTier(tier)}
                  className={`py-3 rounded-lg font-medium transition-all ${
                    currentTier === tier
                      ? `${TIER_COLORS[tier]} ring-2 ring-white ring-opacity-50`
                      : 'bg-adapt-border hover:bg-gray-700'
                  }`}
                >
                  {TIER_LABELS[tier]}
                </button>
              ))}
            </div>

            {/* Speed Visualization */}
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Bandwidth</span>
                <span>{networkStatus.bandwidth_kbps.toLocaleString()} kbps</span>
              </div>
              <div className="w-full bg-adapt-border rounded-full h-2">
                <div
                  className={`network-bar ${
                    {'wifi': 'wifi', '4g': '4g', '3g': '3g', '2g': '2g'}[networkStatus.tier]
                  }`}
                  style={{
                    width: `${Math.min(100, (networkStatus.bandwidth_kbps / 10000) * 100)}%`
                  }}
                />
              </div>

              <div className="flex justify-between text-sm mt-4">
                <span>Latency</span>
                <span>{networkStatus.latency_ms} ms</span>
              </div>
              <div className="w-full bg-adapt-border rounded-full h-2">
                <div
                  className={`network-bar ${
                    {'wifi': 'wifi', '4g': '4g', '3g': '3g', '2g': '2g'}[networkStatus.tier]
                  }`}
                  style={{
                    width: `${Math.max(5, 100 - (networkStatus.latency_ms / 50))}%`
                  }}
                />
              </div>
            </div>
          </div>

          {/* Compression Stats */}
          <div className="card">
            <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
              <span>📦</span> Compression
            </h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="metric-label">Compression Level</div>
                <div className={`metric-value ${
                  networkStatus.compression_level === 'aggressive' ? 'text-red-400' :
                  networkStatus.compression_level === 'medium' ? 'text-orange-400' :
                  networkStatus.compression_level === 'light' ? 'text-green-400' :
                  'text-blue-400'
                }`}>
                  {networkStatus.compression_level || 'none'}
                </div>
              </div>
              <div>
                <div className="metric-label">Reduction</div>
                <div className="metric-value text-yellow-400">
                  -{compressionPercentage}%
                </div>
              </div>
            </div>
          </div>

          {/* Metrics */}
          <div className="card">
            <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
              <span>📊</span> Performance Metrics
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <div className="metric-label">Requests</div>
                <div className="metric-value text-white">{metrics.requests_served}</div>
              </div>
              <div>
                <div className="metric-label">Total Cost</div>
                <div className="metric-value text-green-400">₹{metrics.total_cost_rs.toFixed(2)}</div>
              </div>
              <div>
                <div className="metric-label">Cache Hit</div>
                <div className="metric-value text-blue-400">{(metrics.cache_hit_rate * 100).toFixed(0)}%</div>
              </div>
              <div>
                <div className="metric-label">Adaptations</div>
                <div className="metric-value text-yellow-400">{metrics.adaptation_events}</div>
              </div>
            </div>
          </div>

          {/* Conversation Feed */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold flex items-center gap-2">
                <span>💬</span> Conversation Feed
              </h2>
              <button
                onClick={runDemo}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium transition-colors"
              >
                Run Demo
              </button>
            </div>

            <div className="space-y-4 max-h-96 overflow-y-auto">
              {conversations.length === 0 && (
                <p className="text-gray-500 text-center py-8">
                  Click "Run Demo" to see ADAPT in action
                </p>
              )}
              {conversations.map((conv) => (
                <div key={conv.id} className="border-b border-adapt-border pb-4 last:border-0">
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`tier-indicator ${TIER_COLORS[conv.tier]}`} style={{ fontSize: '0.65rem' }}>
                      {TIER_LABELS[conv.tier]}
                    </span>
                    <span className="text-xs text-gray-500">
                      {conv.compression !== 'none' ? `${conv.compression} compression` : 'no compression'}
                    </span>
                    {conv.cache && (
                      <span className="text-xs bg-purple-600 px-2 py-0.5 rounded-full">CACHED</span>
                    )}
                  </div>
                  <p className="text-sm text-gray-300 mb-2">
                    <span className="text-blue-400">Q:</span> {conv.message}
                  </p>
                  <p className="text-sm">
                    <span className="text-green-400">A:</span> {conv.response}
                  </p>
                  <div className="flex gap-4 text-xs text-gray-500 mt-2">
                    <span>{conv.tokens} tokens</span>
                    <span>₹{conv.cost.toFixed(2)}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column */}
        <div className="space-y-6">
          {/* Model Status */}
          <div className="card">
            <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
              <span>🤖</span> Model
            </h2>
            <div className="text-center">
              <div className={`text-4xl font-bold mb-2 ${
                networkStatus.model_size === '1B' ? 'text-red-400' :
                networkStatus.model_size === '3B' ? 'text-orange-400' :
                networkStatus.model_size === '7B' ? 'text-green-400' :
                'text-blue-400'
              }`}>
                {networkStatus.model_size}
              </div>
              <p className="text-xs text-gray-500">Active Model Size</p>
            </div>
          </div>

          {/* Cache Status */}
          <div className="card">
            <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
              <span>🗄️</span> Semantic Cache
            </h2>
            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>Hit Rate</span>
                  <span className="font-bold">{(cacheStats.hit_rate * 100).toFixed(0)}%</span>
                </div>
                <div className="w-full bg-adapt-border rounded-full h-2">
                  <div
                    className="bg-purple-500 h-2 rounded-full transition-all"
                    style={{ width: `${cacheStats.hit_rate * 100}%` }}
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 text-sm">
                <div>
                  <div className="text-gray-500">Hits</div>
                  <div className="text-green-400 font-bold">{cacheStats.hits}</div>
                </div>
                <div>
                  <div className="text-gray-500">Misses</div>
                  <div className="text-red-400 font-bold">{cacheStats.misses}</div>
                </div>
              </div>
            </div>
          </div>

          {/* Quick Test */}
          <div className="card">
            <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
              <span>🔬</span> Quick Test
            </h2>
            <div className="space-y-3">
              <input
                type="text"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                placeholder="Enter message..."
                className="w-full px-3 py-2 bg-adapt-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={sendMessage}
                disabled={loading}
                className="w-full py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 rounded-lg font-medium transition-colors"
              >
                {loading ? 'Sending...' : 'Send via ADAPT'}
              </button>
              {response && (
                <div className="mt-3 p-3 bg-adapt-border rounded-lg text-sm">
                  <div className="text-gray-500 mb-1">Response:</div>
                  <div>{response}</div>
                </div>
              )}
            </div>
          </div>

          {/* Philosophy */}
          <div className="card bg-gradient-to-br from-blue-900/30 to-purple-900/30">
            <h2 className="text-lg font-bold mb-2 flex items-center gap-2">
              <span>💡</span> Philosophy
            </h2>
            <p className="text-sm text-gray-300 leading-relaxed">
              "AI should degrade gracefully, not catastrophically."
            </p>
            <p className="text-xs text-gray-500 mt-3">
              When the network drops, ADAPT doesn't give up. It compresses,
              switches models, returns cached responses, and maintains context.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App