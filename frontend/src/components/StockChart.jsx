import React, { useState } from 'react';
import { 
  ResponsiveContainer, ComposedChart, Line, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Legend 
} from 'recharts';
import { Activity } from 'lucide-react';
import { formatPrice } from '../utils/formatters';

export function StockChart({ historyData, symbol }) {


  const [showIndicators, setShowIndicators] = useState({
    sma10: true,
    sma20: true,
    ema10: false,
    bollinger: false,
    volume: true
  });

  if (!historyData || historyData.length === 0) {
    return (
      <div className="glass-card" style={{ height: '380px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <p style={{ color: 'var(--text-muted)' }}>Market data unavailable — configure the data provider.</p>
      </div>
    );
  }

  // Format data for chart
  const formattedData = historyData.map(d => ({
    date: d.date,
    close: d.close,
    open: d.open,
    high: d.high,
    low: d.low,
    volume: d.volume,
    sma10: d.sma_10 || null,
    sma20: d.sma_20 || null,
    ema10: d.ema_10 || null,
    bbUpper: d.bb_upper || null,
    bbLower: d.bb_lower || null
  }));

  const latestClose = formattedData[formattedData.length - 1]?.close || 0;
  const prevClose = formattedData[formattedData.length - 2]?.close || latestClose;
  const change = latestClose - prevClose;
  const changePct = prevClose > 0 ? (change / prevClose) * 100 : 0;

  return (
    <div className="glass-card" style={{ marginBottom: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h2 className="heading-font" style={{ fontSize: '1.25rem', fontWeight: 700 }}>
              {symbol} Historical OHLCV Price Chart
            </h2>
            <span style={{ fontSize: '1.1rem', fontWeight: 700, color: change >= 0 ? 'var(--up-green)' : 'var(--down-red)' }}>
              {formatPrice(latestClose, symbol)} ({change >= 0 ? '+' : ''}{changePct.toFixed(2)}%)
            </span>

          </div>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            Real historical data retrieved from NSE via Yahoo Finance
          </p>
        </div>

        {/* Indicator Toggles */}
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          <button
            className={`btn-secondary ${showIndicators.sma10 ? 'active' : ''}`}
            onClick={() => setShowIndicators(p => ({ ...p, sma10: !p.sma10 }))}
          >
            SMA 10
          </button>
          <button
            className={`btn-secondary ${showIndicators.sma20 ? 'active' : ''}`}
            onClick={() => setShowIndicators(p => ({ ...p, sma20: !p.sma20 }))}
          >
            SMA 20
          </button>
          <button
            className={`btn-secondary ${showIndicators.ema10 ? 'active' : ''}`}
            onClick={() => setShowIndicators(p => ({ ...p, ema10: !p.ema10 }))}
          >
            EMA 10
          </button>
          <button
            className={`btn-secondary ${showIndicators.bollinger ? 'active' : ''}`}
            onClick={() => setShowIndicators(p => ({ ...p, bollinger: !p.bollinger }))}
          >
            Bollinger Bands
          </button>
          <button
            className={`btn-secondary ${showIndicators.volume ? 'active' : ''}`}
            onClick={() => setShowIndicators(p => ({ ...p, volume: !p.volume }))}
          >
            Volume
          </button>
        </div>
      </div>

      <div style={{ height: '360px', width: '100%' }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={formattedData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
            <XAxis dataKey="date" stroke="var(--text-muted)" fontSize={11} tickLine={false} />
            <YAxis yAxisId="price" domain={['auto', 'auto']} stroke="var(--text-muted)" fontSize={11} tickFormatter={v => `₹${v}`} />
            {showIndicators.volume && (
              <YAxis yAxisId="volume" orientation="right" domain={[0, 'auto']} hide />
            )}
            <Tooltip
              contentStyle={{ background: '#121824', borderColor: 'var(--border-color)', borderRadius: '8px', color: '#fff' }}
              formatter={(val, name) => [typeof val === 'number' ? val.toFixed(2) : val, name.toUpperCase()]}
            />
            <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />

            {showIndicators.volume && (
              <Bar yAxisId="volume" dataKey="volume" fill="rgba(79, 172, 254, 0.2)" name="Volume" barSize={4} />
            )}

            <Line yAxisId="price" type="monotone" dataKey="close" stroke="#00f2fe" strokeWidth={2} dot={false} name="Close Price" />

            {showIndicators.sma10 && (
              <Line yAxisId="price" type="monotone" dataKey="sma10" stroke="#f59e0b" strokeWidth={1.5} dot={false} name="SMA 10" />
            )}
            {showIndicators.sma20 && (
              <Line yAxisId="price" type="monotone" dataKey="sma20" stroke="#3b82f6" strokeWidth={1.5} dot={false} name="SMA 20" />
            )}
            {showIndicators.ema10 && (
              <Line yAxisId="price" type="monotone" dataKey="ema10" stroke="#ec4899" strokeWidth={1.5} dot={false} name="EMA 10" />
            )}

            {showIndicators.bollinger && (
              <>
                <Line yAxisId="price" type="monotone" dataKey="bbUpper" stroke="rgba(16, 185, 129, 0.6)" strokeDasharray="4 4" dot={false} name="BB Upper" />
                <Line yAxisId="price" type="monotone" dataKey="bbLower" stroke="rgba(239, 68, 68, 0.6)" strokeDasharray="4 4" dot={false} name="BB Lower" />
              </>
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
