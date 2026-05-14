import React from 'react';
import Landing from './components/Landing';
import Navbar from './components/Navbar';
import NetworkControl from './components/NetworkControl';
import MetricsPanel from './components/MetricsPanel';
import CachePanel from './components/CachePanel';
import FeedPanel from './components/FeedPanel';
import { useAppLogic } from './hooks/useAppLogic';

function App() {
  const {
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
  } = useAppLogic();

  if (view === 'landing') {
    return <Landing onEnter={() => setView('dashboard')} />;
  }

  return (
    <div className="min-h-screen bg-primary text-slate-200">
      <Navbar 
        view={view}
        setView={setView}
        comparisonMode={comparisonMode}
        setComparisonMode={setComparisonMode}
        connectionStatus={connectionStatus}
      />

      <main className="max-w-7xl mx-auto p-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Network & Metrics */}
        <div className="lg:col-span-4 space-y-6">
          <NetworkControl 
            networkStatus={networkStatus}
            changeTier={changeTier}
            runActiveProbe={runActiveProbe}
            probeStatus={probeStatus}
          />

          <MetricsPanel 
            networkStatus={networkStatus}
            metrics={metrics}
          />

          <CachePanel cacheStats={cacheStats} />
        </div>

        {/* Right Column: Feed & Playground */}
        <div className="lg:col-span-8 space-y-6">
          <FeedPanel 
            comparisonMode={comparisonMode}
            loading={loading}
            networkStatus={networkStatus}
            response={response}
            standardLoading={standardLoading}
            standardResponse={standardResponse}
            conversations={conversations}
            message={message}
            setMessage={setMessage}
            sendMessage={sendMessage}
            runDemo={runDemo}
          />

          <section className="glass-card p-6 bg-gradient-to-br from-blue-900/10 to-purple-900/10 border-blue-500/20">
            <div className="flex items-start gap-4">
              <div>
                <h4 className="text-sm font-bold text-white mb-1">Infrastructure Signal</h4>
                <p className="text-xs text-slate-400 leading-relaxed">
                  ADAPT now supports active browser probing, request-boundary model switching, session memory, task-aware compression, and safe semantic-cache skips. Manual tier buttons remain as demo controls for repeatable interviews.
                </p>
              </div>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}

export default App;
