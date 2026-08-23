import React from 'react';
import { Activity, ShieldAlert, CheckCircle2, AlertTriangle, Layers, BarChart2 } from 'lucide-react';

export function PatternAnalysisCard({ symbol }) {
  return (
    <div className="glass-card shadow-sm" style={{ padding: '20px', borderRadius: '16px', border: '1px solid var(--border-color)', background: 'var(--card-bg)' }}>
      {/* Card Header with Experimental Badge */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'rgba(99, 102, 241, 0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#6366F1' }}>
            <Layers size={20} />
          </div>
          <div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: '600', margin: 0, color: 'var(--text-main)' }}>
              Candlestick & Price Action Analysis
            </h3>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Phase 15 Statistical Feature Research — {symbol}
            </span>
          </div>
        </div>

        <span style={{
          padding: '4px 10px',
          borderRadius: '20px',
          fontSize: '0.7rem',
          fontWeight: '700',
          letterSpacing: '0.5px',
          background: 'rgba(234, 179, 8, 0.15)',
          color: '#EAB308',
          border: '1px solid rgba(234, 179, 8, 0.3)',
          display: 'inline-flex',
          alignItems: 'center',
          gap: '4px'
        }}>
          <ShieldAlert size={12} />
          RESEARCH EXPERIMENTAL
        </span>
      </div>

      {/* Feature Analysis Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px', marginBottom: '16px' }}>
        {/* Pattern Geometry */}
        <div style={{ padding: '12px', borderRadius: '10px', background: 'var(--bg-secondary)', border: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Body Ratio & Range</div>
          <div style={{ fontSize: '1rem', fontWeight: '700', color: 'var(--text-main)' }}>Standard Expansion</div>
          <div style={{ fontSize: '0.72rem', color: '#10B981', marginTop: '2px' }}>Close in upper 65% range</div>
        </div>

        {/* Pattern Detection */}
        <div style={{ padding: '12px', borderRadius: '10px', background: 'var(--bg-secondary)', border: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Detected Pattern</div>
          <div style={{ fontSize: '1rem', fontWeight: '700', color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <CheckCircle2 size={16} color="#10B981" /> Bullish Engulfing
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '2px' }}>Volume Ratio: 1.42x</div>
        </div>

        {/* Price Action Streaks */}
        <div style={{ padding: '12px', borderRadius: '10px', background: 'var(--bg-secondary)', border: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Price Action Structure</div>
          <div style={{ fontSize: '1rem', fontWeight: '700', color: 'var(--text-main)' }}>Higher High / Higher Low</div>
          <div style={{ fontSize: '0.72rem', color: '#6366F1', marginTop: '2px' }}>2 consecutive up candles</div>
        </div>

        {/* Support/Resistance */}
        <div style={{ padding: '12px', borderRadius: '10px', background: 'var(--bg-secondary)', border: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Structure & Breakout</div>
          <div style={{ fontSize: '1rem', fontWeight: '700', color: 'var(--text-main)' }}>Testing Resistance</div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '2px' }}>Distance to 20d High: +0.85%</div>
        </div>
      </div>

      {/* Footer Disclaimer */}
      <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', background: 'rgba(255, 255, 255, 0.03)', padding: '10px 12px', borderRadius: '8px', border: '1px dashed var(--border-color)', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <AlertTriangle size={14} style={{ flexShrink: 0, color: '#EAB308' }} />
        <span>
          Phase 15 features evaluate structural price action. Production predictions remain powered by Phase 12 Calibrated XGBoost v1.0.
        </span>
      </div>
    </div>
  );
}
