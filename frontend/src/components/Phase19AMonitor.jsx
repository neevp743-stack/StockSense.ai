import React, { useState, useEffect } from 'react';
import { api } from '../api';
import { Activity, Wifi, RefreshCw, Database, Server, AlertTriangle, CheckCircle2, XCircle, Info, Radio } from 'lucide-react';

export function Phase19AMonitor({ symbol: propSymbol = 'RELIANCE' }) {
  const [selectedSymbol, setSelectedSymbol] = useState(propSymbol);
  const [status, setStatus] = useState(null);
  const [symbolDiagnostics, setSymbolDiagnostics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [symbolError, setSymbolError] = useState(null);

  const availableSymbols = [
    'RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK',
    'AAPL', 'NVDA', 'BTC-USD'
  ];

  // Sync selected symbol with prop if updated upstream
  useEffect(() => {
    if (propSymbol) {
      setSelectedSymbol(propSymbol);
    }
  }, [propSymbol]);

  // Real-time polling every 10s for overall status
  useEffect(() => {
    let timerId = null;

    const fetchOverallStatus = async () => {
      const controller = new AbortController();
      try {
        const res = await api.getPhase19AStatus({ signal: controller.signal });
        if (res?.data) {
          setStatus(res.data);
          setError(null);
        }
      } catch (err) {
        if (err.name !== 'CanceledError' && err.name !== 'AbortError') {
          setError(err.message || 'Failed to fetch Phase 19A status telemetry');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchOverallStatus();
    timerId = setInterval(fetchOverallStatus, 10000);

    return () => {
      if (timerId) clearInterval(timerId);
    };
  }, []);

  // Symbol diagnostics fetch when selectedSymbol changes
  useEffect(() => {
    if (!selectedSymbol) return;

    const controller = new AbortController();

    const fetchSymbolDiagnostics = async () => {
      try {
        const res = await api.getPhase19ASymbolStatus(selectedSymbol, { signal: controller.signal });
        if (res?.data) {
          setSymbolDiagnostics(res.data);
          setSymbolError(null);
        }
      } catch (err) {
        if (err.name !== 'CanceledError' && err.name !== 'AbortError') {
          setSymbolError(err.message || `Failed to fetch diagnostics for ${selectedSymbol}`);
        }
      }
    };

    fetchSymbolDiagnostics();

    return () => {
      controller.abort();
    };
  }, [selectedSymbol]);

  const getStatusBadge = (val, healthyVals = ['CONNECTED', 'LIVE', 'HEALTHY', 'ACTIVE'], warningVals = ['CONNECTING', 'DELAYED', 'DEGRADED', 'STANDBY']) => {
    const valUpper = (val || 'UNAVAILABLE').toUpperCase();
    if (healthyVals.includes(valUpper)) {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <CheckCircle2 className="w-3 h-3 mr-1" />
          {valUpper}
        </span>
      );
    }
    if (warningVals.includes(valUpper)) {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
          <AlertTriangle className="w-3 h-3 mr-1" />
          {valUpper}
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">
        <XCircle className="w-3 h-3 mr-1" />
        {valUpper}
      </span>
    );
  };

  if (error) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 mb-8 text-white shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <Radio className="w-6 h-6 text-rose-400 animate-pulse" />
            <div>
              <h2 className="text-xl font-bold text-white">Phase 19A — Live Data Pipeline</h2>
              <p className="text-sm text-slate-400">Live market-data reliability & shadow observation diagnostics</p>
            </div>
          </div>
          <span className="px-3 py-1 bg-rose-500/10 text-rose-400 border border-rose-500/20 rounded-full text-xs font-semibold">
            LIVE DATA RELIABILITY
          </span>
        </div>
        <div className="bg-rose-500/10 border border-rose-500/20 rounded-lg p-4 flex items-start space-x-3">
          <AlertTriangle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-rose-300">Phase 19A monitoring unavailable</h3>
            <p className="text-sm text-rose-200/80 mt-1">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  const symCounts = status?.symbol_counts || {};
  const shadowPipe = status?.shadow_pipeline || {};
  const obsToday = shadowPipe.observations_today ?? 0;
  const pairedToday = shadowPipe.paired_observations ?? 0;
  const failedToday = shadowPipe.failed_observations ?? 0;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 mb-8 text-white shadow-xl">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-slate-800 gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-blue-500/10 border border-blue-500/20 rounded-lg text-blue-400">
            <Radio className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-xl font-bold text-white">Phase 19A — Live Data Pipeline</h2>
              <span className="px-2.5 py-0.5 text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded-full">
                LIVE DATA RELIABILITY
              </span>
            </div>
            <p className="text-sm text-slate-400 mt-0.5">Live market-data reliability & shadow observation diagnostics</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          {loading && <RefreshCw className="w-4 h-4 text-blue-400 animate-spin mr-2" />}
          {getStatusBadge(shadowPipe.pipeline_status || 'HEALTHY')}
        </div>
      </div>

      {/* Main Telemetry Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 my-6">
        {/* Provider Telemetry */}
        <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-4">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium mb-2">
            <span>DATA PROVIDER</span>
            <Server className="w-4 h-4 text-slate-500" />
          </div>
          <div className="text-lg font-bold text-white mb-2">{status?.provider || 'FINNHUB'}</div>
          <div className="space-y-1.5 text-xs">
            <div className="flex justify-between items-center text-slate-300">
              <span>WebSocket:</span>
              {getStatusBadge(status?.websocket_status)}
            </div>
            <div className="flex justify-between items-center text-slate-300">
              <span>REST Fallback:</span>
              {getStatusBadge(status?.rest_fallback_status, ['ACTIVE', 'STANDBY'], ['STANDBY'])}
            </div>
          </div>
        </div>

        {/* Data Freshness */}
        <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-4">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium mb-2">
            <span>DATA FRESHNESS</span>
            <Wifi className="w-4 h-4 text-slate-500" />
          </div>
          <div className="text-lg font-bold text-white mb-2">
            {status?.latest_valid_tick_age_seconds != null
              ? `${status.latest_valid_tick_age_seconds.toFixed(1)}s age`
              : 'N/A'}
          </div>
          <div className="flex justify-between items-center text-xs text-slate-300">
            <span>Data Status:</span>
            {getStatusBadge(status?.data_status, ['LIVE'], ['DELAYED'])}
          </div>
        </div>

        {/* Symbol Distribution */}
        <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-4">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium mb-2">
            <span>SYMBOL UNIVERSE ({symCounts.total_symbols || 0})</span>
            <Activity className="w-4 h-4 text-slate-500" />
          </div>
          <div className="grid grid-cols-2 gap-1 text-xs">
            <div className="text-emerald-400">Live: <span className="font-semibold">{symCounts.live_symbols || 0}</span></div>
            <div className="text-amber-400">Delayed: <span className="font-semibold">{symCounts.delayed_symbols || 0}</span></div>
            <div className="text-orange-400">Stale: <span className="font-semibold">{symCounts.stale_symbols || 0}</span></div>
            <div className="text-rose-400">Unavailable: <span className="font-semibold">{symCounts.unavailable_symbols || 0}</span></div>
          </div>
        </div>

        {/* Shadow Pipeline */}
        <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-4">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium mb-2">
            <span>SHADOW PIPELINE</span>
            <Database className="w-4 h-4 text-slate-500" />
          </div>
          <div className="text-xs space-y-1">
            <div className="flex justify-between">
              <span className="text-slate-400">Observations Today:</span>
              <span className="font-semibold text-white">{obsToday}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Paired Observations:</span>
              <span className="font-semibold text-white">{pairedToday}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Failed Observations:</span>
              <span className={`font-semibold ${failedToday > 0 ? 'text-rose-400' : 'text-slate-400'}`}>{failedToday}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Zero Observations Warning */}
      {obsToday === 0 && (
        <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-3 my-4 flex items-center space-x-2 text-xs text-amber-300">
          <Info className="w-4 h-4 flex-shrink-0" />
          <span>Waiting for valid live observations. Shadow prediction tracker is active in background.</span>
        </div>
      )}

      {/* Symbol Diagnostics Section */}
      <div className="mt-6 pt-6 border-t border-slate-800">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-4 gap-2">
          <h3 className="text-md font-semibold text-white flex items-center">
            <Activity className="w-4 h-4 mr-2 text-blue-400" />
            Symbol Telemetry & Shadow Diagnostics
          </h3>
          <div className="flex items-center space-x-2">
            <label htmlFor="phase19a-symbol-select" className="text-xs text-slate-400">Symbol:</label>
            <select
              id="phase19a-symbol-select"
              value={selectedSymbol}
              onChange={(e) => setSelectedSymbol(e.target.value)}
              className="bg-slate-950 border border-slate-700 text-xs text-white rounded-md px-3 py-1.5 focus:outline-none focus:border-blue-500"
            >
              {availableSymbols.map((sym) => (
                <option key={sym} value={sym}>{sym}</option>
              ))}
            </select>
          </div>
        </div>

        {symbolError ? (
          <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-4 text-xs text-rose-400">
            {symbolError}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 bg-slate-950/40 border border-slate-800 rounded-lg p-4 text-xs">
            {/* Live Data Diagnostics */}
            <div>
              <div className="font-semibold text-slate-300 mb-2 border-b border-slate-800 pb-1">LIVE DATA</div>
              <div className="space-y-1 text-slate-400">
                <div className="flex justify-between">
                  <span>Provider:</span>
                  <span className="text-white font-medium">{symbolDiagnostics?.live_data?.provider || 'FINNHUB'}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span>WebSocket:</span>
                  {getStatusBadge(symbolDiagnostics?.live_data?.websocket_status)}
                </div>
                <div className="flex justify-between items-center">
                  <span>REST Fallback:</span>
                  {getStatusBadge(symbolDiagnostics?.live_data?.rest_fallback_status, ['ACTIVE', 'STANDBY'], ['STANDBY'])}
                </div>
                <div className="flex justify-between">
                  <span>Latest Price:</span>
                  <span className="text-white font-medium">
                    {symbolDiagnostics?.live_data?.latest_price != null ? `$${symbolDiagnostics.live_data.latest_price.toFixed(2)}` : 'N/A'}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span>Data Status:</span>
                  {getStatusBadge(symbolDiagnostics?.live_data?.data_status, ['LIVE'], ['DELAYED'])}
                </div>
              </div>
            </div>

            {/* Prediction Pipeline Diagnostics */}
            <div>
              <div className="font-semibold text-slate-300 mb-2 border-b border-slate-800 pb-1">PREDICTION PIPELINE</div>
              <div className="space-y-1 text-slate-400">
                <div className="flex justify-between items-center">
                  <span>Champion Status:</span>
                  {getStatusBadge(symbolDiagnostics?.prediction_pipeline?.champion_status)}
                </div>
                <div className="flex justify-between items-center">
                  <span>Challenger Status:</span>
                  {getStatusBadge(symbolDiagnostics?.prediction_pipeline?.challenger_status)}
                </div>
                <div className="flex justify-between">
                  <span>Last Observation:</span>
                  <span className="text-slate-300 text-[10px]">
                    {symbolDiagnostics?.prediction_pipeline?.last_observation
                      ? new Date(symbolDiagnostics.prediction_pipeline.last_observation).toLocaleTimeString()
                      : 'None'}
                  </span>
                </div>
              </div>
            </div>

            {/* Database Diagnostics */}
            <div>
              <div className="font-semibold text-slate-300 mb-2 border-b border-slate-800 pb-1">DATABASE RECORDS</div>
              <div className="space-y-1 text-slate-400">
                <div className="flex justify-between">
                  <span>Observations:</span>
                  <span className="text-white font-medium">{symbolDiagnostics?.database?.observations ?? 0}</span>
                </div>
                <div className="flex justify-between">
                  <span>Paired Resolved:</span>
                  <span className="text-white font-medium">{symbolDiagnostics?.database?.paired_observations ?? 0}</span>
                </div>
              </div>
            </div>

            {/* Actual Backend Diagnostic Message */}
            <div>
              <div className="font-semibold text-slate-300 mb-2 border-b border-slate-800 pb-1">DIAGNOSTIC STATUS</div>
              <div className="text-slate-400">
                {symbolDiagnostics?.diagnostics?.error_reason ? (
                  <p className="text-amber-300 bg-amber-500/10 border border-amber-500/20 rounded p-2 text-[11px] leading-tight">
                    {symbolDiagnostics.diagnostics.error_reason}
                  </p>
                ) : (
                  <p className="text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 rounded p-2 text-[11px] leading-tight">
                    Pipeline nominal. Provider telemetry and shadow records operational.
                  </p>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
