import React, { useState, useEffect, useRef } from 'react';
import { Search, X, Clock, RefreshCw, ArrowRight, ShieldCheck } from 'lucide-react';
import { api } from '../api';

export function SearchModal({ isOpen, onClose, onSelectAsset }) {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [searchResults, setSearchResults] = useState([]);
  const [recentSearches, setRecentSearches] = useState([]);
  const [loading, setLoading] = useState(false);
  const inputRef = useRef(null);

  useEffect(() => {
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
      fetchInitialPopular();
    }
  }, [isOpen]);

  const fetchInitialPopular = () => {
    setLoading(true);
    api.search('', 20)
      .then(res => {
        setSearchResults(res.data.assets || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  // Debounced search query via API
  useEffect(() => {
    if (!isOpen) return;

    const controller = new AbortController();
    const { signal } = controller;

    setLoading(true);
    const timer = setTimeout(() => {
      api.search(query, 25, { signal })
        .then(res => {
          setSearchResults(res.data.assets || []);
          setSelectedIndex(0);
          setLoading(false);
        })
        .catch(err => {
          if (err?.name !== 'CanceledError' && err?.name !== 'AbortError') {
            console.error("Search API error:", err);
            setLoading(false);
          }
        });
    }, 200);

    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [query, isOpen]);

  const handleSelect = (symbol) => {
    const cleanSym = symbol.upper ? symbol.upper().strip() : symbol;
    const updated = [cleanSym, ...recentSearches.filter(s => s !== cleanSym)].slice(0, 6);
    setRecentSearches(updated);
    try {
      localStorage.setItem('stocksense_recent_searches', JSON.stringify(updated));
    } catch (err) {}

    onSelectAsset(cleanSym);
    onClose();
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      onClose();
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex(prev => (prev + 1) % (searchResults.length || 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex(prev => (prev - 1 + searchResults.length) % (searchResults.length || 1));
    } else if (e.key === 'Enter' && searchResults[selectedIndex]) {
      e.preventDefault();
      handleSelect(searchResults[selectedIndex].symbol);
    } else if (e.key === 'Enter' && query.trim()) {
      e.preventDefault();
      handleSelect(query.trim().toUpperCase());
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
          {loading ? <RefreshCw size={20} color="var(--accent-cyan)" className="spin" /> : <Search size={20} color="var(--accent-cyan)" />}
          <input
            ref={inputRef}
            type="text"
            placeholder="Search stock, symbol, or crypto (e.g. RELIANCE, TCS, INFY, HDFCBANK, AAPL, NVDA, BTC)..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
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
            <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', fontWeight: 700, marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
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

        {/* Search Results List */}
        <div style={{ overflowY: 'auto', flexGrow: 1, padding: '8px 0' }}>
          {searchResults.length === 0 ? (
            <div style={{ padding: '30px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
              {loading ? "Searching market universe..." : `No stocks found matching "${query}". Press Enter to open on-demand.`}
            </div>
          ) : (
            searchResults.map((item, idx) => {
              const isSelected = idx === selectedIndex;

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
                      <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{item.display_name}</div>
                    </div>
                  </div>

                  <div style={{ textAlign: 'right' }}>
                    <span style={{ fontSize: '0.74rem', background: 'var(--bg-secondary)', padding: '3px 8px', borderRadius: '6px', color: 'var(--accent-cyan)', fontWeight: 600 }}>
                      {item.exchange || item.asset_class}
                    </span>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer Shortcut Hint */}
        <div style={{ padding: '10px 20px', background: '#090d16', borderTop: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.74rem', color: 'var(--text-muted)' }}>
          <div>Dynamic market search powered by provider feeds</div>
          <div><kbd style={{ background: 'var(--bg-secondary)', padding: '2px 6px', borderRadius: '4px', border: '1px solid var(--border-color)' }}>ESC</kbd> to close</div>
        </div>
      </div>
    </div>
  );
}
