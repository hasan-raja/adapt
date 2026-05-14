import React from 'react';
import { TIER_LABELS, TIER_COLORS } from '../utils/constants';

const FeedPanel = ({
  comparisonMode,
  loading,
  networkStatus,
  response,
  standardLoading,
  standardResponse,
  conversations,
  message,
  setMessage,
  sendMessage,
  runDemo
}) => {
  return (
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
            <div className="text-4xl font-display text-slate-500">ADAPT</div>
            <p>No activity yet. Send a message or run the demo.</p>
          </div>
        )}
        {conversations.map((conv) => (
          <div key={conv.id} className="space-y-3 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex items-center gap-3">
              <span className={`tier-badge ${TIER_COLORS[conv.tier]}`}>{TIER_LABELS[conv.tier]}</span>
              {conv.cache && <span className="tier-badge border-purple-500 text-purple-400 bg-purple-500/10">Semantic Hit</span>}
              <span className="text-[10px] text-slate-500 font-mono">{(conv.tokens || 0)} tokens / Rs {(conv.cost || 0).toFixed(2)}</span>
              {conv.model && <span className="text-[10px] text-blue-300 font-mono bg-blue-500/10 border border-blue-500/20 rounded-full px-2 py-1">{conv.model}</span>}
              {conv.task && <span className="text-[10px] text-slate-300 font-mono bg-slate-900 border border-slate-800 rounded-full px-2 py-1">{conv.task}</span>}
            </div>
            
            {conv.trace && (
              <div className="flex flex-wrap gap-2 mb-2">
                {conv.trace.map((step, i) => (
                  <span key={i} className="text-[9px] bg-slate-900 border border-slate-800 text-slate-400 px-2 py-0.5 rounded-full font-mono">
                    {step}
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
            {conv.cacheReason && (
              <div className="ml-4 text-[10px] text-amber-300 font-mono">
                Cache reuse disabled: {conv.cacheReason}
              </div>
            )}
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
            onClick={() => sendMessage()}
            disabled={loading}
            className="btn-primary"
          >
            {loading ? 'Processing...' : 'Send'}
          </button>
        </div>
      </div>
    </section>
  );
};

export default FeedPanel;
