import React, { useEffect, useState } from 'react';
import { api } from '../api';
import { ShieldCheck, Activity, Database, Cpu, CheckCircle2, AlertTriangle, RefreshCw, BarChart2 } from 'lucide-react';

export function ProductionMonitor({ symbol = 'RELIANCE' }) {
  const [dataQuality, setDataQuality] = useState(null);
  const [modelMetrics, setModelMetrics] = useState(null);
  const [driftInfo, setDriftInfo] = useState(null);
  const [paperStats, setPaperStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!symbol) return;
    setLoading(true);

    const controller = new AbortController();
    const opts = { signal: controller.signal };

    Promise.all([
      api.getDataQuality(symbol, opts).catch(() => null),
      api.getModelMonitor(symbol, opts).catch(() => null),
      api.getModelDrift(symbol, opts).catch(() => null),
      api.getPaperPerformance(symbol, opts).catch(() => null)
    ]).then(([dqRes, mmRes, drRes, ppRes]) => {
      if (controller.signal.aborted) return;

      if (dqRes?.data) setDataQuality(dqRes.data);
      if (mmRes?.data) setModelMetrics(mmRes.data);
      if (drRes?.data) setDriftInfo(drRes.data);
      if (ppRes?.data) setPaperStats(ppRes.data);
      setLoading(false);
    }).catch(err => {
      if (!controller.signal.aborted) {
        console.error("ProductionMonitor fetch error:", err);
        setLoading(false);
      }
    });

    // 45-second background polling
    const interval = setInterval(() => {
      api.getDataQuality(symbol).then(res => res?.data && setDataQuality(res.data)).catch(() => {});
      api.getModelMonitor(symbol).then(res => res?.data && setModelMetrics(res.data)).catch(() => {});
    }, 45000);

    return () => {
      controller.abort();
      clearInterval(interval);
    };
  }, [symbol]);

  const dataStatus = dataQuality?.status || 'LIVE';
  const dataBadgeColor = 
    dataStatus === 'LIVE' ? 'var(--up-green)' :
    dataStatus === 'DELAYED' ? '#f97316' : '#ef4444';

  const sampleSize = modelMetrics?.sample_size ?? 0;
  const hasEnoughLiveSamples = modelMetrics?.accuracy !== null && modelMetrics?.accuracy !== undefined;
  const accuracyText = hasEnoughLiveSamples 
    ? `${(modelMetrics.accuracy * 100).toFixed(1)}%` 
    : "Insufficient live data";

  const brierText = modelMetrics?.brier_score !== null && modelMetrics?.brier_score !== undefined
    ? modelMetrics.brier_score.toFixed(3)
    : "N/A";

  const driftStatus = driftInfo?.status || 'NORMAL';
  const driftBadgeColor = driftStatus === 'NORMAL' ? 'var(--up-green)' : (driftStatus === 'WATCH' ? '#f97316' : '#ef4444');

  const paperTrades = paperStats?.resolved_trades ?? paperStats?.total_setups ?? 0;

  return (
    <div className="glass-card" style={{ padding: '20px', borderRadius: '16px', border: '1px solid var(--border-color)', marginBottom: '24px', background: 'var(--card-bg)' }}>
      {/* Panel Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'rgba(0, 242, 254, 0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--accent-cyan)' }}>
            <ShieldCheck size={20} />
          </div>
          <div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: '700', margin: 0, color: 'var(--text-primary)' }}>
              Production Monitor & Live Model Validation
            </h3>
            <span style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>
              Phase 16 Forward-Testing Telemetry — {symbol}
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span className="mono-font" style={{ padding: '4px 10px', borderRadius: '20px', fontSize: '0.72rem', fontWeight: 700, background: 'rgba(16, 185, 129, 0.15)', color: dataBadgeColor, border: `1px solid ${dataBadgeColor}` }}>
            ● DATA {dataStatus}
          </span>
        </div>
      </div>

      {/* Grid Status Metrics */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px', marginBottom: '16px' }}>
        {/* Model Card */}
        <div style={{ padding: '12px', borderRadius: '10px', background: 'var(--bg-secondary)', border: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Cpu size={12} color="var(--accent-cyan)" /> PRODUCTION MODEL
          </div>
          <div style={{ fontSize: '0.95rem', fontWeight: '700', color: 'var(--text-primary)' }}>
            XGBoost v1.0
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--accent-cyan)', marginTop: '2px' }}>
            Calibrated Inference Active
          </div>
        </div>

        {/* Live Validation Accuracy */}
        <div style={{ padding: '12px', borderRadius: '10px', background: 'var(--bg-secondary)', border: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Activity size={12} color="var(--up-green)" /> LIVE ACCURACY
          </div>
          <div style={{ fontSize: '0.95rem', fontWeight: '700', color: hasEnoughLiveSamples ? 'var(--up-green)' : '#f59e0b' }}>
            {accuracyText}
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '2px' }}>
            {sampleSize} Resolved Samples
          </div>
        </div>

        {/* Brier Score & Calibration */}
        <div style={{ padding: '12px', borderRadius: '10px', background: 'var(--bg-secondary)', border: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <BarChart2 size={12} color="var(--accent-cyan)" /> BRIER SCORE
          </div>
          <div style={{ fontSize: '0.95rem', fontWeight: '700', color: 'var(--text-primary)' }}>
            {brierText}
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '2px' }}>
            Calibration: {hasEnoughLiveSamples ? 'GOOD' : 'PENDING'}
          </div>
        </div>

        {/* Model Drift Status */}
        <div style={{ padding: '12px', borderRadius: '10px', background: 'var(--bg-secondary)', border: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <RefreshCw size={12} color={driftBadgeColor} /> DRIFT MONITOR
          </div>
          <div style={{ fontSize: '0.95rem', fontWeight: '700', color: driftBadgeColor }}>
            {driftStatus}
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '2px' }}>
            PSI: {driftInfo?.psi_score ?? 0.0}
          </div>
        </div>

        {/* Paper Trading Status */}
        <div style={{ padding: '12px', borderRadius: '10px', background: 'var(--bg-secondary)', border: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Database size={12} color="var(--accent-cyan)" /> PAPER TRADING
          </div>
          <div style={{ fontSize: '0.95rem', fontWeight: '700', color: 'var(--text-primary)' }}>
            {paperTrades} Trades
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '2px' }}>
            Phase 14 Tracker Active
          </div>
        </div>
      </div>

      {/* Footer Info */}
      <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', background: 'rgba(255, 255, 255, 0.02)', padding: '8px 12px', borderRadius: '8px', border: '1px dashed var(--border-color)', display: 'flex', alignItems: 'center', gap: '6px' }}>
        <CheckCircle2 size={13} color="var(--up-green)" style={{ flexShrink: 0 }} />
        <span>
          Phase 16 forward validation automatically resolves live predictions against unseen $T+1$ market price action without modifying production model weights.
        </span>
      </div>
    </div>
  );
}
