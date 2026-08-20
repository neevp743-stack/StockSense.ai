import React from 'react';
import { ArrowUpRight, ArrowDownRight, AlertTriangle, ShieldCheck, Activity, Cpu, Layers } from 'lucide-react';

export function ChartAnalysisPanel({ symbol, prediction, indicators, supportResistance }) {
  const latestPrice = prediction?.latest_price || "N/A";
  const isUp = prediction?.predicted_direction === "UP";
  const probUpPct = prediction?.probability_up ? (prediction.probability_up * 100).toFixed(1) : "N/A";
  const probDownPct = prediction?.probability_down ? (prediction.probability_down * 100).toFixed(1) : "N/A";

  const rsiVal = indicators?.rsi_14 !== undefined ? indicators.rsi_14 : "N/A";
  const macdVal = indicators?.macd !== undefined ? indicators.macd : "N/A";
  const macdSig = indicators?.macd_signal !== undefined ? indicators.macd_signal : "N/A";

  const rsiStatus = rsiVal > 70 ? "Overbought" : (rsiVal < 30 ? "Oversold" : "Neutral");
  const macdStatus = macdVal > macdSig ? "Bullish Crossover" : "Bearish Crossover";

  const sups = supportResistance?.support_levels || [];
  const reses = supportResistance?.resistance_levels || [];

  return (
    <div className="glass-card" style={{ padding: '20px', height: '100%', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <div>
        <h3 className="heading-font" style={{ fontSize: '1.1rem', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
          <Activity size={18} color="var(--accent-cyan)" /> Terminal Market Analysis ({symbol})
        </h3>

        {/* Section 1: AI Model Prediction Output */}
        <div style={{ background: 'var(--bg-secondary)', padding: '14px', borderRadius: '12px', marginBottom: '14px', border: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Empirical Model Research Prediction
          </div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '4px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: isUp ? 'var(--up-green)' : 'var(--down-red)', fontWeight: 800, fontSize: '1.25rem' }}>
              {isUp ? <ArrowUpRight size={22} /> : <ArrowDownRight size={22} />}
              <span>{prediction?.predicted_direction || "N/A"}</span>
            </div>
            <div className="mono-font" style={{ fontSize: '0.9rem', fontWeight: 700 }}>
              <span style={{ color: 'var(--up-green)' }}>UP {probUpPct}%</span> / <span style={{ color: 'var(--down-red)' }}>DOWN {probDownPct}%</span>
            </div>
          </div>

          <div style={{ marginTop: '8px', fontSize: '0.76rem', color: 'var(--text-muted)', display: 'flex', justifyContent: 'space-between' }}>
            <span>Model: {prediction?.model?.name || "XGBoost v1.0"}</span>
            <span>Status: {prediction?.quote_info?.data_status || "HISTORICAL"}</span>
          </div>
        </div>

        {/* Section 2: Technical Indicators Observations */}
        <div style={{ background: 'var(--bg-secondary)', padding: '14px', borderRadius: '12px', marginBottom: '14px', border: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Technical Indicator Observations
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '0.82rem' }}>
            <div>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>RSI (14)</div>
              <strong className="mono-font">{rsiVal}</strong> <span style={{ fontSize: '0.72rem', color: rsiVal > 70 ? 'var(--down-red)' : (rsiVal < 30 ? 'var(--up-green)' : 'var(--text-muted)') }}>({rsiStatus})</span>
            </div>

            <div>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>MACD Signal</div>
              <strong className="mono-font">{macdVal}</strong> <span style={{ fontSize: '0.72rem', color: macdVal > macdSig ? 'var(--up-green)' : 'var(--down-red)' }}>({macdStatus})</span>
            </div>

            <div>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>SMA (20/50)</div>
              <strong className="mono-font">{indicators?.sma_20 ? `$${indicators.sma_20}` : 'N/A'}</strong>
            </div>

            <div>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>Bollinger Bands</div>
              <strong className="mono-font">{indicators?.bollinger_upper ? `$${indicators.bollinger_upper}` : 'N/A'}</strong>
            </div>
          </div>
        </div>

        {/* Section 3: Automatic Support & Resistance */}
        <div style={{ background: 'var(--bg-secondary)', padding: '14px', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.5px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Layers size={14} color="var(--accent-cyan)" /> Automatic Support & Resistance
          </div>

          <div style={{ fontSize: '0.82rem' }}>
            <div style={{ marginBottom: '4px' }}>
              <span style={{ color: 'var(--down-red)', fontWeight: 700 }}>AUTOMATIC RESISTANCE: </span>
              <span className="mono-font">{reses.length > 0 ? reses.map(r => `$${r}`).join(', ') : 'None detected'}</span>
            </div>
            <div>
              <span style={{ color: 'var(--up-green)', fontWeight: 700 }}>AUTOMATIC SUPPORT: </span>
              <span className="mono-font">{sups.length > 0 ? sups.map(s => `$${s}`).join(', ') : 'None detected'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Mandatory Disclaimer */}
      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', lineHeight: '1.4', background: 'rgba(239, 68, 68, 0.08)', padding: '8px 10px', borderRadius: '8px', marginTop: 'auto' }}>
        <AlertTriangle size={12} color="var(--down-red)" style={{ display: 'inline', marginRight: '4px' }} />
        Technical observations and AI predictions are empirical estimates only. NOT guaranteed signals or financial advice.
      </div>
    </div>
  );
}
