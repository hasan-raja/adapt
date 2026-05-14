import React from 'react';
import { TIER_LABELS, TIER_COLORS } from '../utils/constants';

const NetworkControl = ({ networkStatus, changeTier, runActiveProbe, probeStatus }) => {
  return (
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

      <button
        onClick={runActiveProbe}
        disabled={probeStatus.running}
        className="w-full btn-secondary py-2 text-xs"
      >
        {probeStatus.running ? 'Measuring network...' : 'Run Active Browser Probe'}
      </button>

      <div className="rounded-lg border border-glass-border bg-slate-950/60 p-3 text-xs text-slate-400">
        <div className="flex justify-between">
          <span>Probe source</span>
          <span className="font-mono text-slate-200">{probeStatus.source}</span>
        </div>
        <div className="mt-2 grid grid-cols-2 gap-2 font-mono">
          <span>{probeStatus.bandwidth ? `${probeStatus.bandwidth.toFixed(0)} kbps` : 'no bandwidth reading'}</span>
          <span>{probeStatus.latency ? `${probeStatus.latency.toFixed(0)} ms RTT` : 'no RTT reading'}</span>
        </div>
      </div>

      <div className="space-y-4 pt-4 border-t border-glass-border">
        <div className="space-y-1.5">
          <div className="flex justify-between text-[10px] uppercase tracking-widest text-slate-500 font-bold">
            <span>Bandwidth</span>
            <span className="text-slate-300">{networkStatus?.bandwidth_kbps?.toLocaleString() || 0} kbps</span>
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
            <span className="text-slate-300">{networkStatus?.latency_ms || 0} ms</span>
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
  );
};

export default NetworkControl;
