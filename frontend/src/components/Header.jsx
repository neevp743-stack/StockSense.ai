import React from 'react';
import { Search, RefreshCw, Globe, AlertTriangle, User } from 'lucide-react';
import { Logo } from './Logo';

export function Header({ 
  assetClasses, selectedAssetClass, onSelectAssetClass,
  availableAssets, selectedAsset, onSelectAsset,
  onRefresh, isRefreshing, activeTab = 'dashboard', onSelectTab,
  onOpenSearch
}) {
  return (
    <header style={{ marginBottom: '20px' }}>
      {/* Top Navbar Row */}
      <div 
        style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center', 
          flexWrap: 'wrap', 
          gap: '16px', 
          marginBottom: '16px',
          background: 'rgba(13, 19, 31, 0.9)',
          padding: '14px 20px',
          borderRadius: '16px',
          border: '1px solid var(--border-color)',
          backdropFilter: 'blur(16px)'
        }}
      >
        {/* Brand Identity Logo */}
        <div style={{ cursor: 'pointer' }} onClick={() => onSelectTab && onSelectTab('dashboard')}>
          <Logo size={42} showText={true} />
        </div>

        {/* Center: Search Trigger & Asset Selectors */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          {/* Quick Stock Search Button */}
          <button
            onClick={onOpenSearch}
            style={{
              background: 'var(--bg-primary)',
              border: '1px solid var(--border-color)',
              borderRadius: '10px',
              padding: '7px 14px',
              color: 'var(--text-secondary)',
              fontSize: '0.82rem',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              cursor: 'pointer'
            }}
            title="Search all supported stocks (Press /)"
          >
            <Search size={14} color="var(--accent-cyan)" />
            <span>Search market universe...</span>
            <kbd style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', padding: '1px 5px', borderRadius: '4px', fontSize: '0.68rem', color: 'var(--text-muted)' }}>
              /
            </kbd>
          </button>

          {/* Asset Class Selector Dropdown */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'var(--bg-primary)', padding: '6px 12px', borderRadius: '10px', border: '1px solid var(--border-color)' }}>
            <Globe size={14} color="var(--accent-cyan)" />
            <select
              value={selectedAssetClass}
              onChange={(e) => onSelectAssetClass(e.target.value)}
              style={{
                background: 'transparent', color: '#fff', border: 'none',
                fontSize: '0.82rem', fontWeight: 600, outline: 'none', cursor: 'pointer'
              }}
            >
              <option value="INDIAN_EQUITY">Indian Stocks (NSE)</option>
              <option value="US_EQUITY">US Stocks (NASDAQ)</option>
              <option value="CRYPTO">Crypto (24/7)</option>
              <option value="FOREX">Forex Pairs</option>
              <option value="INDEX">Global Indices</option>
            </select>
          </div>

          {/* Quick Symbol Switcher Pill Buttons */}
          <div style={{ display: 'flex', gap: '4px', background: 'var(--bg-primary)', padding: '4px', borderRadius: '10px', border: '1px solid var(--border-color)' }}>
            {availableAssets.slice(0, 5).map(ast => (
              <button
                key={ast.symbol}
                className={`btn-secondary ${selectedAsset === ast.symbol ? 'active' : ''}`}
                onClick={() => onSelectAsset(ast.symbol)}
                style={{ padding: '4px 10px', fontSize: '0.78rem', fontWeight: 700, borderRadius: '6px' }}
              >
                {ast.symbol}
              </button>
            ))}
          </div>
        </div>

        {/* Right Actions: Refresh & User Profile */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button 
            className="btn-primary" 
            onClick={onRefresh} 
            disabled={isRefreshing}
            style={{ opacity: isRefreshing ? 0.6 : 1, padding: '8px 14px', fontSize: '0.82rem' }}
          >
            <RefreshCw size={14} className={isRefreshing ? 'spin' : ''} />
            {isRefreshing ? 'Refreshing...' : 'Refresh'}
          </button>

          <div 
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '10px',
              background: 'var(--bg-primary)',
              border: '1px solid var(--border-color)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--accent-cyan)',
              cursor: 'pointer'
            }}
            title="Neev — Quant Analyst Profile"
          >
            <User size={18} />
          </div>
        </div>
      </div>

      {/* Primary Navigation Bar (Desktop & Tablet) */}
      <div 
        style={{ 
          display: 'flex', 
          gap: '8px', 
          marginBottom: '16px', 
          background: 'var(--bg-secondary)', 
          padding: '6px', 
          borderRadius: '12px',
          border: '1px solid var(--border-color)',
          overflowX: 'auto',
          scrollbarWidth: 'none'
        }}
      >
        {[
          { id: 'dashboard', label: '📊 Stock Intelligence' },
          { id: 'intelligence', label: '🔥 Market Intel' },
          { id: 'markets', label: '🌐 Market Universe' },
          { id: 'live-research', label: '⚡ Live AI Research' },
          { id: 'ablation', label: '🧪 Feature Study' },
          { id: 'leaderboard', label: '🏆 Model Evaluation' },
          { id: 'tracking', label: '📜 Resolution Tracking' },
          { id: 'backtest', label: '⚡ Backtester' },
        ].map(tab => (
          <button 
            key={tab.id}
            className={`btn-secondary ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => onSelectTab && onSelectTab(tab.id)}
            style={{ 
              padding: '8px 16px', 
              fontSize: '0.84rem', 
              fontWeight: activeTab === tab.id ? 700 : 600,
              borderRadius: '8px',
              whiteSpace: 'nowrap'
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Disclaimer Banner */}
      <div className="disclaimer-banner">
        <AlertTriangle size={16} style={{ flexShrink: 0 }} />
        <div>
          <strong>ACADEMIC RESEARCH DISCLAIMER:</strong> StockSense AI is an educational machine-learning research platform. It is <strong>NOT</strong> financial advice. Directional predictions represent historical model probabilities, NOT certainty.
        </div>
      </div>
    </header>
  );
}
