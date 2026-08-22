import React, { useState, useEffect } from 'react';
import { Star, Plus, Trash2, TrendingUp, TrendingDown, ArrowRight } from 'lucide-react';
import { formatPrice } from '../utils/formatters';

const DEFAULT_WATCHLIST = ['RELIANCE', 'INFY', 'TCS', 'AAPL', 'BTC-USD'];

const MOCK_PRICES = {
  'RELIANCE': { price: 1313.20, change: 1.25 },
  'INFY': { price: 1482.50, change: 0.72 },
  'TCS': { price: 3421.10, change: -0.45 },
  'AAPL': { price: 224.30, change: 0.85 },
  'TSLA': { price: 212.50, change: -1.15 },
  'BTC-USD': { price: 94250.00, change: 1.45 },
};

export function Watchlist({ selectedSymbol, onSelectSymbol }) {
  const [watchlist, setWatchlist] = useState(DEFAULT_WATCHLIST);

  useEffect(() => {
    try {
      const saved = localStorage.getItem('stocksense_watchlist');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) setWatchlist(parsed);
      }
    } catch (err) {}
  }, []);

  const saveWatchlist = (newList) => {
    setWatchlist(newList);
    try {
      localStorage.setItem('stocksense_watchlist', JSON.stringify(newList));
    } catch (err) {}
  };

  const handleRemove = (sym, e) => {
    e.stopPropagation();
    const updated = watchlist.filter(s => s !== sym);
    saveWatchlist(updated);
  };

  return (
    <div className="glass-card" style={{ marginBottom: '24px', padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
        <h3 className="heading-font" style={{ fontSize: '1.05rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Star size={18} color="var(--accent-cyan)" fill="var(--accent-cyan)" /> My Watchlist
        </h3>
        <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
          {watchlist.length} Assets Tracked
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
        {watchlist.map(sym => {
          const info = MOCK_PRICES[sym] || { price: 1000.00, change: 0.50 };
          const isPos = info.change >= 0;
          const isSelected = selectedSymbol === sym;

          return (
            <div
              key={sym}
              onClick={() => onSelectSymbol(sym)}
              style={{
                background: isSelected ? 'rgba(0, 242, 254, 0.08)' : 'var(--bg-secondary)',
                border: `1px solid ${isSelected ? 'var(--accent-cyan)' : 'var(--border-color)'}`,
                borderRadius: '12px',
                padding: '12px 14px',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
              }}
              className="hover-card"
            >
              <div>
                <div style={{ fontWeight: 800, fontSize: '0.92rem', color: '#fff' }}>{sym}</div>
                <div className="mono-font" style={{ fontSize: '0.85rem', fontWeight: 700, marginTop: '2px' }}>
                  {formatPrice(info.price, sym)}
                </div>
              </div>

              <div style={{ textAlign: 'right', display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '4px' }}>
                <span 
                  className="mono-font" 
                  style={{ 
                    fontSize: '0.78rem', 
                    fontWeight: 700, 
                    color: isPos ? 'var(--up-green)' : 'var(--down-red)',
                    background: isPos ? 'var(--up-green-bg)' : 'var(--down-red-bg)',
                    padding: '2px 8px',
                    borderRadius: '6px'
                  }}
                >
                  {isPos ? '+' : ''}{info.change}%
                </span>
                
                <button
                  onClick={(e) => handleRemove(sym, e)}
                  title="Remove from watchlist"
                  style={{ background: 'transparent', border: 'none', color: 'var(--text-dim)', cursor: 'pointer', padding: '2px' }}
                >
                  <Trash2 size={12} />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
