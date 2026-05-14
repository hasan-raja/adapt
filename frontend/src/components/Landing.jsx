import React from 'react';

const Landing = ({ onEnter }) => {
  return (
    <div className="min-h-screen hero-gradient flex flex-col items-center justify-center p-6">
      <div className="max-w-4xl w-full text-center space-y-8">
        <div className="space-y-4 animate-float">
          <div className="flex justify-center mb-6">
            <div className="w-20 h-20 bg-blue-600 rounded-2xl flex items-center justify-center text-3xl font-bold shadow-2xl shadow-blue-500/20">A</div>
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
            <div className="text-blue-400 mb-2">Survival Mode</div>
            <p className="text-sm text-slate-400">60-70% prompt compression for 2G network resilience.</p>
          </div>
          <div className="glass-card p-6">
            <div className="text-emerald-400 mb-2">Smart Routing</div>
            <p className="text-sm text-slate-400">Dynamic model selection (1B to 30B+) based on real-time QoS.</p>
          </div>
          <div className="glass-card p-6">
            <div className="text-amber-400 mb-2">Semantic Cache</div>
            <p className="text-sm text-slate-400">Zero-latency responses using MiniLM embedding similarity.</p>
          </div>
        </div>

        <button 
          onClick={onEnter}
          className="btn-primary text-lg px-12 py-4 shadow-xl shadow-blue-600/20 hover:scale-105 transition-transform"
        >
          Enter Dashboard
        </button>
      </div>
    </div>
  );
};

export default Landing;
