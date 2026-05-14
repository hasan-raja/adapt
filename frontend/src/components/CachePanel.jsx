import React from 'react';

const CachePanel = ({ cacheStats }) => {
  return (
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
  );
};

export default CachePanel;
