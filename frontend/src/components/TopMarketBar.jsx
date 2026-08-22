import React, { useEffect, useState } from 'react';
import { TrendingUp, TrendingDown, Radio } from 'lucide-react';

const INITIAL_INDICES = [
  { symbol: 'NIFTY 50', price: '24,820.40', change: '+0.42%', isPos: true },
  { symbol: 'SENSEX', price: '81,350.10', change: '+0.31%', isPos: true },
  { symbol: 'NASDAQ', price: '21,180.25', change: '-0.18%', isPos: false },
  { symbol: 'BTC/USD', price: '$94,250.00', change: '+1.21%', isPos: true },
  { symbol: 'S&P 500', price: '5,920.80', change: '+0.15%', isPos: true },
];

export function TopMarketBar({ onSelectTicker }) {
  const [indices, setIndices] = useState(INITIAL_INDICES);

  // Subtle real-time jitter simulation for non-WS indices to keep bar feeling alive
  useEffect(() => {
    const interval = setInterval(() => {
      setIndices(prev => prev.map(item => {
        if (Math.random() > 0.6) {
          const delta = (Math.random() * 0.04 - 0.02);
          const currentVal = parseFloat(item.change.replace(/[^\d.-]/g, ''));
          const newVal = (currentVal + delta).toFixed(2);
          const isPos = parseFloat(newVal) >= 0;
          return {
            ...item,
            change: `${isPos ? '+' : ''}${newVal}%`,
            isPos
          };
        }
        return item;
      }));
    }, 4000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div 
      style={{ 
        background: '#090d16', 
        borderBottom: '1px solid var(--border-color)',
        padding: '6px 20px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        overflowX: 'auto',
        whiteSpace: 'nowrap',
        fontSize: '0.78rem',
        scrollbarWidth: 'none',
        gap: '24px'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)', flexShrink: 0 }}>
        <Radio size={12} color="var(--up-green)" className="spin" />
        <span style={{ fontWeight: 700, letterSpacing: '0.05em', color: 'var(--text-secondary)' }}>MARKET TICKER</span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '20px', flexGrow: 1 }}>
        {indices.map((idx, i) => (
          <div 
            key={i} 
            onClick={() => onSelectTicker && onSelectTicker(idx.symbol.includes('BTC') ? 'BTC-USD' : (idx.symbol.includes('NIFTY') ? 'RELIANCE' : 'AAPL'))}
            style={{ 
              display: 'inline-flex', 
              alignItems: 'center', 
              gap: '6px',
              cursor: 'pointer',
              padding: '2px 8px',
              borderRadius: '6px',
              transition: 'background 0.2s'
            }}
            className="hover-bg"
          >
            <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{idx.symbol}</span>
            <span className="mono-font" style={{ color: 'var(--text-secondary)' }}>{idx.price}</span>
            <span 
              className="mono-font" 
              style={{ 
                color: idx.isPos ? 'var(--up-green)' : 'var(--down-red)',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '2px',
                fontWeight: 600
              }}
            >
              {idx.isPos ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
              {idx.change}
            </span>
          </div>
        ))}
      </div>

      <div style={{ color: 'var(--text-muted)', fontSize: '0.74rem', flexShrink: 0 }} className="mono-font">
        REALTIME ● FEED ACTIVE
      </div>
    </div>
  );
}
