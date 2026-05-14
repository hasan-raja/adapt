import React from 'react';

const MetricsPanel = ({ networkStatus, metrics }) => {
  return (
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
        <span className="metric-value text-amber-400">Rs {((metrics.requests_served || 0) * 12 - (metrics.total_cost_rs || 0)).toFixed(1)}</span>
      </div>
      <div className="metric-card">
        <span className="metric-label">Events</span>
        <span className="metric-value text-rose-400">{metrics.adaptation_events}</span>
      </div>
    </section>
  );
};

export default MetricsPanel;
