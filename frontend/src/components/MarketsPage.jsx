import React, { useState, useEffect, useRef } from 'react';
import { Search, Globe, ChevronLeft, ChevronRight, TrendingUp, Filter, RefreshCw } from 'lucide-react';
import { api } from '../api';
import { formatPrice } from '../utils/formatters';

export function MarketsPage({ onSelectSymbol }) {
  const [query, setQuery] = useState('');
  const [assetClass, setAssetClass] = useState('');
  const [exchange, setExchange] = useState('');
  const [page, setPage] = useState(1);
  const [limit] = useState(24);

  const [marketsData, setMarketsData] = useState({ assets: [], total_assets: 0, total_pages: 1 });
  const [loading, setLoading] = useState(true);

  // Debounced search controller
  useEffect(() => {
    const controller = new AbortController();
    const { signal } = controller;

    setLoading(true);
    const timer = setTimeout(() => {
      if (query.trim()) {
        api.search(query, 50, { signal })
          .then(res => {
            setMarketsData({
              assets: res.data.assets || [],
              total_assets: res.data.count || 0,
              total_pages: 1
            });
            setLoading(false);
          })
          .catch(err => {
            if (err?.name !== 'CanceledError' && err?.name !== 'AbortError') {
              console.error("Search error:", err);
              setLoading(false);
            }
          });
      } else {
        api.getMarkets({ exchange, asset_class: assetClass, page, limit }, { signal })
          .then(res => {
            setMarketsData(res.data);
            setLoading(false);
          })
          .catch(err => {
            if (err?.name !== 'CanceledError' && err?.name !== 'AbortError') {
              console.error("Markets error:", err);
              setLoading(false);
            }
          });
      }
    }, 200);

    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [query, assetClass, exchange, page, limit]);

  return (
    <div style={{ marginBottom: '32px' }}>
      {/* Header & Filter Controls Bar */}
      <div 
        className="glass-card" 
        style={{ 
          padding: '24px', 
          marginBottom: '20px',
          background: 'linear-gradient(135deg, rgba(13, 19, 31, 0.95) 0%, rgba(19, 27, 44, 0.85) 100%)',
          border: '1px solid var(--border-color)'
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px', marginBottom: '20px' }}>
          <div>
            <h2 className="heading-font" style={{ fontSize: '1.6rem', fontWeight: 800, color: '#fff', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Globe color="var(--accent-cyan)" size={26} /> Supported Market Universe
            </h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', marginTop: '4px' }}>
              Search and explore live market assets supported by your configured market-data provider.
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'rgba(0, 242, 254, 0.08)', padding: '6px 14px', borderRadius: '12px', border: '1px solid rgba(0, 242, 254, 0.2)', fontSize: '0.8rem', color: 'var(--accent-cyan)', fontWeight: 700 }}>
            ● Provider Feed Active — On-Demand Data Enabled
          </div>
        </div>

        {/* Filters Row */}
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'center' }}>
          {/* Search Input */}
          <div style={{ position: 'relative', flexGrow: 1, minWidth: '260px' }}>
            <Search size={18} color="var(--accent-cyan)" style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)' }} />
            <input
              type="text"
              placeholder="Filter by symbol or company (e.g. RELIANCE, TCS, INFY, AAPL, NVDA, BTC)..."
              value={query}
              onChange={(e) => { setQuery(e.target.value); setPage(1); }}
              style={{
                width: '100%',
                background: 'var(--bg-primary)',
                border: '1px solid var(--border-color)',
                borderRadius: '10px',
                padding: '10px 14px 10px 42px',
                color: '#fff',
                fontSize: '0.88rem',
                outline: 'none'
              }}
            />
          </div>

          {/* Category Filter Pills */}
          <div style={{ display: 'flex', gap: '6px', overflowX: 'auto', paddingBottom: '2px' }}>
            {[
              { id: '', label: 'All Markets' },
              { id: 'INDIAN_EQUITY', label: '🇮🇳 NSE Indian' },
              { id: 'US_EQUITY', label: '🇺🇸 US Equities' },
              { id: 'CRYPTO', label: '🪙 Crypto (24/7)' },
              { id: 'FOREX', label: '💱 Forex' },
              { id: 'INDEX', label: '📈 Indices' },
            ].map(cat => (
              <button
                key={cat.id}
                onClick={() => { setAssetClass(cat.id); setQuery(''); setPage(1); }}
                className={`btn-secondary ${assetClass === cat.id && !query ? 'active' : ''}`}
                style={{ padding: '8px 14px', fontSize: '0.8rem', borderRadius: '8px', whiteSpace: 'nowrap' }}
              >
                {cat.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Market Asset Grid */}
      {loading ? (
        <div className="glass-card" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
          <RefreshCw size={24} className="spin" style={{ marginBottom: '10px' }} />
          <div>Loading market assets from provider universe...</div>
        </div>
      ) : marketsData.assets.length === 0 ? (
        <div className="glass-card" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
          <div>No supported market assets found for "{query}".</div>
        </div>
      ) : (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(min(100%, 260px), 1fr))', gap: '14px', marginBottom: '20px' }}>
            {marketsData.assets.map(ast => (
              <div
                key={ast.symbol}
                onClick={() => onSelectSymbol(ast.symbol)}
                className="glass-card glass-card-glow"
                style={{
                  padding: '16px',
                  cursor: 'pointer',
                  display: 'flex',
                  flexDirection: 'column',
                  justify: 'space-between',
                  height: '120px'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <span className="heading-font" style={{ fontSize: '1.1rem', fontWeight: 800, color: '#fff' }}>
                      {ast.symbol}
                    </span>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '2px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '170px' }}>
                      {ast.display_name}
                    </div>
                  </div>

                  <span style={{
                    fontSize: '0.68rem',
                    fontWeight: 700,
                    padding: '2px 8px',
                    borderRadius: '6px',
                    background: 'var(--bg-secondary)',
                    color: 'var(--accent-cyan)',
                    border: '1px solid var(--border-color)'
                  }}>
                    {ast.exchange || ast.asset_class}
                  </span>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '12px' }}>
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
                    Currency: <strong>{ast.currency_symbol || '$'} {ast.currency}</strong>
                  </span>

                  <span style={{ fontSize: '0.76rem', color: 'var(--up-green)', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <TrendingUp size={12} /> Live On-Demand
                  </span>
                </div>
              </div>
            ))}
          </div>

          {/* Pagination Controls */}
          {!query && marketsData.total_pages > 1 && (
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 4px' }}>
              <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                Showing page {marketsData.page} of {marketsData.total_pages} ({marketsData.total_assets} total assets)
              </div>

              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  disabled={page <= 1}
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  className="btn-secondary"
                  style={{ opacity: page <= 1 ? 0.5 : 1, padding: '6px 12px' }}
                >
                  <ChevronLeft size={16} /> Previous
                </button>
                <button
                  disabled={page >= marketsData.total_pages}
                  onClick={() => setPage(p => Math.min(marketsData.total_pages, p + 1))}
                  className="btn-secondary"
                  style={{ opacity: page >= marketsData.total_pages ? 0.5 : 1, padding: '6px 12px' }}
                >
                  Next <ChevronRight size={16} />
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
