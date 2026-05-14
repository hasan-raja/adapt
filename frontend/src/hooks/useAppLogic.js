import { useState, useEffect, useRef } from 'react';
import { DEMO_SCENARIOS } from '../utils/constants';

export const useAppLogic = () => {
  const [view, setView] = useState('landing');
  const [networkStatus, setNetworkStatus] = useState({
    tier: 'wifi',
    bandwidth_kbps: 10000,
    latency_ms: 30,
    compression_level: 'none',
    model_size: '30B+',
  });

  const [metrics, setMetrics] = useState({
    requests_served: 0,
    total_cost_rs: 0,
    cache_hit_rate: 0,
    adaptation_events: 0,
  });

  const [cacheStats, setCacheStats] = useState({
    hits: 0,
    misses: 0,
    hit_rate: 0,
  });

  const [conversations, setConversations] = useState([]);
  const [currentTier, setCurrentTier] = useState('wifi');
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);
  const [comparisonMode, setComparisonMode] = useState(false);
  const [standardResponse, setStandardResponse] = useState('');
  const [standardLoading, setStandardLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [sessionId] = useState(() => `session-${Date.now()}-${Math.random().toString(16).slice(2)}`);
  const [probeStatus, setProbeStatus] = useState({
    source: 'simulator',
    bandwidth: null,
    latency: null,
    running: false,
  });
  
  const wsRef = useRef(null);

  // WebSocket connection
  useEffect(() => {
    if (view !== 'dashboard') return;

    const connect = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = import.meta.env.VITE_WS_URL || `${protocol}//${window.location.hostname}:8000/ws`;

      try {
        wsRef.current = new WebSocket(wsUrl);
        wsRef.current.onopen = () => setConnectionStatus('connected');
        wsRef.current.onclose = () => {
          setConnectionStatus('disconnected');
          setTimeout(connect, 3000);
        };
        wsRef.current.onmessage = (event) => {
          const data = JSON.parse(event.data);
          if (data.type === 'status_update') {
            setNetworkStatus(data.network);
            setMetrics(data.metrics);
            setCacheStats(data.cache);
          }
        };
      } catch (e) {
        setConnectionStatus('disconnected');
        setTimeout(connect, 3000);
      }
    };

    connect();
    return () => wsRef.current?.close();
  }, [view]);

  const changeTier = async (tier) => {
    setCurrentTier(tier);
    try {
      const res = await fetch('/api/network/status?force_tier=' + tier);
      const data = await res.json();
      setNetworkStatus(data);
    } catch (e) {
      console.error('Failed to change tier:', e);
    }
  };

  const getNetworkHints = () => {
    const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
    if (!connection) return {};

    const hints = {};
    if (connection.downlink) hints.observed_bandwidth_kbps = connection.downlink * 1000;
    if (connection.rtt) hints.observed_latency_ms = connection.rtt;
    return hints;
  };

  const runActiveProbe = async () => {
    setProbeStatus(prev => ({ ...prev, running: true }));
    try {
      const pingStart = performance.now();
      await fetch('/api/network/ping', { cache: 'no-store' });
      const latency = performance.now() - pingStart;

      const payloadStart = performance.now();
      const response = await fetch(`/api/network/probe-payload?size_kb=128&t=${Date.now()}`, { cache: 'no-store' });
      const blob = await response.blob();
      const elapsedSec = Math.max((performance.now() - payloadStart) / 1000, 0.001);
      const bandwidth = ((blob.size * 8) / 1000) / elapsedSec;

      setProbeStatus({
        source: 'active probe',
        bandwidth,
        latency,
        running: false,
      });

      return {
        observed_bandwidth_kbps: bandwidth,
        observed_latency_ms: latency,
      };
    } catch (e) {
      setProbeStatus(prev => ({ ...prev, running: false, source: 'probe failed' }));
      return getNetworkHints();
    }
  };

  const sendMessage = async (options = {}) => {
    const outgoingMessage = options.message ?? message;
    const shouldCompare = comparisonMode && !options.skipComparison;

    if (!outgoingMessage.trim()) return;
    setLoading(true);
    setResponse('');
    
    if (shouldCompare) {
      setStandardLoading(true);
      setStandardResponse('');
    }

    try {
      const payload = {
        message: outgoingMessage,
        session_id: sessionId,
        ...getNetworkHints(),
      };
      if (probeStatus.bandwidth && probeStatus.latency && !options.forceTier) {
        payload.observed_bandwidth_kbps = probeStatus.bandwidth;
        payload.observed_latency_ms = probeStatus.latency;
      }
      if (options.forceTier) payload.force_tier = options.forceTier;

      const adaptPromise = fetch('/api/adapt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      }).then(res => res.json());

      let standardPromise = null;
      if (shouldCompare) {
        standardPromise = fetch('/api/standard', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        }).then(async res => {
          if (!res.ok) throw new Error('Standard request timed out/failed');
          return res.json();
        });
      }

      const adaptData = await adaptPromise;
      setResponse(adaptData.response);
      
      const newConv = {
        id: Date.now(),
        tier: adaptData.tier_used,
        message: outgoingMessage,
        response: adaptData.response,
        compression: adaptData.compression_level,
        model: adaptData.model_used,
        task: adaptData.task_type,
        cacheReason: adaptData.cache_skipped_reason,
        tokens: adaptData.tokens_used,
        cost: adaptData.cost_rs,
        cache: adaptData.cache_hit,
        trace: adaptData.trace
      };
      setConversations(prev => [newConv, ...prev]);

      if (shouldCompare && standardPromise) {
        try {
          const standardData = await standardPromise;
          setStandardResponse(standardData.response);
        } catch (e) {
          setStandardResponse('ERROR: Request Timed Out (Standard systems cannot handle this latency)');
        }
        setStandardLoading(false);
      }

      if (!options.message) setMessage('');
    } catch (e) {
      setResponse('Error: Could not connect to ADAPT server');
    }
    setLoading(false);
  };

  const runDemo = async () => {
    setConversations([]);
    for (const conv of DEMO_SCENARIOS) {
      await changeTier(conv.tier);
      await new Promise(resolve => setTimeout(resolve, 800));
      await sendMessage({ message: conv.message, forceTier: conv.tier, skipComparison: true });
    }
  };

  return {
    view,
    setView,
    networkStatus,
    metrics,
    cacheStats,
    conversations,
    message,
    setMessage,
    response,
    loading,
    comparisonMode,
    setComparisonMode,
    standardResponse,
    standardLoading,
    connectionStatus,
    probeStatus,
    changeTier,
    runActiveProbe,
    sendMessage,
    runDemo
  };
};
