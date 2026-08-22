import React from 'react';
import { Gauge, TrendingUp, TrendingDown, Activity, Layers } from 'lucide-react';
import { formatPrice } from '../utils/formatters';

export function TechnicalAnalysisCard({ indicators, symbol, latestPrice }) {
  if (!indicators) {
    return (
      <div className="glass-card" style={{ padding: '20px' }}>
        <h3 className="heading-font" style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: '12px' }}>
          Technical Indicators & Oscillators
        </h3>
        <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
          Computing technical indicators for {symbol}...
        </p>
      </div>
    );
  }

  const rsi = indicators.rsi_14 ? parseFloat(indicators.rsi_14.toFixed(1)) : 50.0;
  const rsiCategory = rsi >= 70 ? 'OVERBOUGHT' : (rsi <= 30 ? 'OVERSOLD' : 'NEUTRAL');
  const rsiColor = rsi >= 70 ? 'var(--down-red)' : (rsi <= 30 ? 'var(--up-green)' : 'var(--accent-cyan)');

  const macdVal = indicators.macd_val ? parseFloat(indicators.macd_val.toFixed(2)) : 0;
  const macdSig = indicators.macd_sig ? parseFloat(indicators.macd_sig.toFixed(2)) : 0;
  const isMacdBullish = macdVal >= macdSig;

  const sma20 = indicators.sma_20 || latestPrice;
  const priceVsSma = latestPrice >= sma20;

  return (
    <div className="glass-card" style={{ padding: '20px', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h3 className="heading-font" style={{ fontSize: '1.05rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Gauge size={18} color="var(--accent-cyan)" /> Technical Signal Gauges — {symbol}
          </h3>
          <span style={{ fontSize: '0.72rem', background: 'var(--bg-secondary)', padding: '3px 8px', borderRadius: '6px', color: 'var(--text-muted)' }}>
            Real-time Technicals
          </span>
        </div>

        {/* Indicator Gauges Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '14px' }}>
          {/* RSI Visual Gauge */}
          <div style={{ background: 'var(--bg-secondary)', padding: '14px', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 700 }}>RSI (14)</span>
              <span className="mono-font" style={{ fontSize: '0.85rem', fontWeight: 700, color: rsiColor }}>{rsi}</span>
            </div>

            <div style={{ height: '6px', background: 'rgba(255,255,255,0.06)', borderRadius: '3px', overflow: 'hidden', marginBottom: '6px' }}>
              <div style={{ width: `${Math.min(100, Math.max(0, rsi))}%`, background: rsiColor, height: '100%', borderRadius: '3px', transition: 'width 0.5s' }} />
            </div>

            <div style={{ fontSize: '0.72rem', fontWeight: 700, color: rsiColor }}>
              ● {rsiCategory}
            </div>
          </div>

          {/* MACD Crossover Signal */}
          <div style={{ background: 'var(--bg-secondary)', padding: '14px', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 700 }}>MACD</span>
              <span className="mono-font" style={{ fontSize: '0.85rem', fontWeight: 700, color: isMacdBullish ? 'var(--up-green)' : 'var(--down-red)' }}>
                {macdVal} / {macdSig}
              </span>
            </div>
            <div style={{ fontSize: '0.78rem', fontWeight: 700, color: isMacdBullish ? 'var(--up-green)' : 'var(--down-red)', display: 'flex', alignItems: 'center', gap: '4px', marginTop: '8px' }}>
              {isMacdBullish ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
              {isMacdBullish ? 'Bullish Crossover' : 'Bearish Crossover'}
            </div>
          </div>

          {/* SMA 20 vs Current Price */}
          <div style={{ background: 'var(--bg-secondary)', padding: '14px', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 700 }}>SMA 20</span>
              <span className="mono-font" style={{ fontSize: '0.85rem', fontWeight: 700 }}>{formatPrice(sma20, symbol)}</span>
            </div>
            <div style={{ fontSize: '0.78rem', fontWeight: 700, color: priceVsSma ? 'var(--up-green)' : 'var(--down-red)', display: 'flex', alignItems: 'center', gap: '4px', marginTop: '8px' }}>
              {priceVsSma ? '● Price Above Trend' : '● Price Below Trend'}
            </div>
          </div>

          {/* Volatility Indicator */}
          <div style={{ background: 'var(--bg-secondary)', padding: '14px', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 700 }}>VOLATILITY</span>
              <span className="mono-font" style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--accent-blue)' }}>MODERATE</span>
            </div>
            <div style={{ fontSize: '0.74rem', color: 'var(--text-secondary)', marginTop: '8px' }}>
              Normal trading band width
            </div>
          </div>
        </div>
      </div>

      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '14px' }}>
        * Indicators calculated from 100-bar rolling OHLCV window.
      </div>
    </div>
  );
}
