import React, { useState, useEffect, useRef } from 'react';
import { Search, X, TrendingUp, Clock, ArrowRight } from 'lucide-react';
import { formatPrice } from '../utils/formatters';

const POPULAR_UNIVERSE = [
  { symbol: 'RELIANCE', name: 'Reliance Industries Ltd.', price: 1313.20, change: 1.25, assetClass: 'INDIAN_EQUITY' },
  { symbol: 'INFY', name: 'Infosys Limited', price: 1482.50, change: 0.72, assetClass: 'INDIAN_EQUITY' },
  { symbol: 'TCS', name: 'Tata Consultancy Services', price: 3421.10, change: -0.45, assetClass: 'INDIAN_EQUITY' },
  { symbol: 'AAPL', name: 'Apple Inc.', price: 224.30, change: 0.85, assetClass: 'US_EQUITY' },
  { symbol: 'TSLA', name: 'Tesla, Inc.', price: 212.50, change: -1.15, assetClass: 'US_EQUITY' },
  { symbol: 'NVDA', name: 'NVIDIA Corporation', price: 128.40, change: 2.10, assetClass: 'US_EQUITY' },
  { symbol: 'BTC-USD', name: 'Bitcoin / USD', price: 94250.00, change: 1.45, assetClass: 'CRYPTO' },
  { symbol: 'ETH-USD', name: 'Ethereum / USD', price: 3450.00, change: 0.90, assetClass: 'CRYPTO' },
];

export function SearchModal({ isOpen, onClose, onSelectAsset }) {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [recentSearches, setRecentSearches] = useState([]);
  const inputRef = useRef(null);

  useEffect(() => {
    // Load recent searches from localStorage
    try {
      const saved = localStorage.getItem('stocksense_recent_searches');
      if (saved) setRecentSearches(JSON.parse(saved));
    } catch (err) {}
  }, []);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
      setQuery('');
      setSelectedIndex(0);
    }
  }, [isOpen]);

  const filteredAssets = POPULAR_UNIVERSE.filter(item => 
    item.symbol.toLowerCase().includes(query.toLowerCase()) ||
    item.name.toLowerCase().includes(query.toLowerCase())
  );

  const handleSelect = (symbol) => {
    // Save to recent
    const updated = [symbol, ...recentSearches.filter(s => s !== symbol)].slice(0, 5);
    setRecentSearches(updated);
    try {
      localStorage.setItem('stocksense_recent_searches', JSON.stringify(updated));
    } catch (err) {}

    onSelectAsset(symbol);
    onClose();
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      onClose();
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex(prev => (prev + 1) % (filteredAssets.length || 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex(prev => (prev - 1 + filteredAssets.length) % (filteredAssets.length || 1));
    } else if (e.key === 'Enter' && filteredAssets[selectedIndex]) {
      e.preventDefault();
      handleSelect(filteredAssets[selectedIndex].symbol);
    }
  };

  if (!isOpen) return null;

  return (
    <div 
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 999,
        background: 'rgba(5, 7, 12, 0.85)',
        backdropFilter: 'blur(16px)',
        display: 'flex',
        justifyContent: 'center',
        paddingTop: '80px',
        paddingLeft: '16px',
        paddingRight: '16px'
      }}
      onClick={onClose}
    >
      <div 
        style={{
          width: '100%',
          maxWidth: '640px',
          background: '#0d131f',
          border: '1px solid rgba(0, 242, 254, 0.3)',
          borderRadius: '16px',
          boxShadow: '0 20px 60px rgba(0, 0, 0, 0.7), 0 0 30px rgba(0, 242, 254, 0.15)',
          overflow: 'hidden',
          maxHeight: '520px',
          display: 'flex',
          flexDirection: 'column'
        }}
        onClick={(e) => e.stopPropagation()}
        onKeyDown={handleKeyDown}
      >
        {/* Search Header Input */}
        <div style={{ display: 'flex', alignItems: 'center', padding: '16px 20px', borderBottom: '1px solid var(--border-color)', gap: '12px' }}>
          <Search size={22} color="var(--accent-cyan)" />
          <input
            ref={inputRef}
            type="text"
            placeholder="Search stock, symbol, or crypto (e.g. RELIANCE, AAPL, BTC)..."
            value={query}
            onChange={(e) => { setQuery(e.target.value); setSelectedIndex(0); }}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#fff',
              fontSize: '1.05rem',
              outline: 'none',
              width: '100%',
              fontFamily: 'var(--font-body)'
            }}
          />
          <button 
            onClick={onClose}
            style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', display: 'flex', alignItems: 'center' }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Recent Searches Header */}
        {!query && recentSearches.length > 0 && (
          <div style={{ padding: '12px 20px', borderBottom: '1px solid var(--border-subtle)', background: 'rgba(255,255,255,0.02)' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 700, marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Clock size={12} /> RECENT SEARCHES
            </div>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              {recentSearches.map(sym => (
                <button
                  key={sym}
                  onClick={() => handleSelect(sym)}
                  style={{
                    background: 'var(--bg-secondary)',
                    color: 'var(--text-primary)',
                    border: '1px solid var(--border-color)',
                    padding: '4px 10px',
                    borderRadius: '8px',
                    fontSize: '0.8rem',
                    cursor: 'pointer',
                    fontWeight: 600
                  }}
                >
                  {sym}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Results List */}
        <div style={{ overflowY: 'auto', flexGrow: 1, padding: '8px 0' }}>
          {filteredAssets.length === 0 ? (
            <div style={{ padding: '30px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
              No stocks found matching "{query}"
            </div>
          ) : (
            filteredAssets.map((item, idx) => {
              const isSelected = idx === selectedIndex;
              const isPos = item.change >= 0;

              return (
                <div
                  key={item.symbol}
                  onClick={() => handleSelect(item.symbol)}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  style={{
                    padding: '12px 20px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    cursor: 'pointer',
                    background: isSelected ? 'rgba(0, 242, 254, 0.08)' : 'transparent',
                    borderLeft: `3px solid ${isSelected ? 'var(--accent-cyan)' : 'transparent'}`,
                    transition: 'background 0.15s'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                    <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: '0.82rem', color: 'var(--accent-cyan)' }}>
                      {item.symbol.substring(0, 3)}
                    </div>
                    <div>
                      <div style={{ fontWeight: 700, fontSize: '0.95rem', color: '#fff' }}>{item.symbol}</div>
                      <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{item.name}</div>
                    </div>
                  </div>

                  <div style={{ textAlign: 'right' }}>
                    <div className="mono-font" style={{ fontWeight: 700, fontSize: '0.95rem', color: '#fff' }}>
                      {formatPrice(item.price, item.symbol)}
                    </div>
                    <div className="mono-font" style={{ fontSize: '0.78rem', fontWeight: 600, color: isPos ? 'var(--up-green)' : 'var(--down-red)' }}>
                      {isPos ? '+' : ''}{item.change}%
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Keyboard Shortcut Hint Footer */}
        <div style={{ padding: '10px 20px', background: '#090d16', borderTop: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.74rem', color: 'var(--text-muted)' }}>
          <div>Use <kbd style={{ background: 'var(--bg-secondary)', padding: '2px 6px', borderRadius: '4px', border: '1px solid var(--border-color)' }}>↑</kbd> <kbd style={{ background: 'var(--bg-secondary)', padding: '2px 6px', borderRadius: '4px', border: '1px solid var(--border-color)' }}>↓</kbd> to navigate</div>
          <div><kbd style={{ background: 'var(--bg-secondary)', padding: '2px 6px', borderRadius: '4px', border: '1px solid var(--border-color)' }}>ESC</kbd> to close</div>
        </div>
      </div>
    </div>
  );
}
