import React from 'react';

const Navbar = ({ view, setView, comparisonMode, setComparisonMode, connectionStatus }) => {
  return (
    <nav className="border-b border-glass-border bg-bg-secondary/50 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3 cursor-pointer" onClick={() => setView('landing')}>
          <span className="text-lg font-bold text-blue-400">A</span>
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
            {comparisonMode ? 'COMPARISON ACTIVE' : 'ENABLE COMPARISON'}
          </button>
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-glass-border`}>
            <div className={`w-2 h-2 rounded-full ${connectionStatus === 'connected' ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`}></div>
            <span className="text-xs font-medium uppercase tracking-widest">{connectionStatus}</span>
          </div>
          <button onClick={() => setView('landing')} className="text-xs text-slate-500 hover:text-white transition-colors">Logout</button>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
