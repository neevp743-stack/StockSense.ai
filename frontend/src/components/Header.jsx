import React from 'react';
import { TrendingUp, RefreshCw, AlertTriangle, Globe } from 'lucide-react';

export function Header({ 
  assetClasses, selectedAssetClass, onSelectAssetClass,
  availableAssets, selectedAsset, onSelectAsset,
  onRefresh, isRefreshing, activeTab = 'dashboard', onSelectTab
}) {
  return (
    <header style={{ marginBottom: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px', marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ 
            width: '44px', height: '44px', borderRadius: '12px', 
            background: 'linear-gradient(135deg, #00f2fe 0%, #4facfe 100%)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#000', boxShadow: '0 4px 20px rgba(0, 242, 254, 0.4)'
          }}>
            <TrendingUp size={26} strokeWidth={2.5} />
          </div>
          <div>
            <h1 className="heading-font" style={{ fontSize: '1.6rem', fontWeight: 800, background: 'linear-gradient(90deg, #fff, #94a3b8)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              StockSense AI
            </h1>
            <p style={{ color: 'var(--accent-cyan)', fontSize: '0.82rem', fontWeight: 600, letterSpacing: '0.5px' }}>
              Predict. Explain. Verify. — Multi-Asset AI Market Research Platform
            </p>
          </div>
        </div>

        {/* Two-Tier Market Selector & Refresh Button */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          {/* Tier 1: Asset Class Selector */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'var(--bg-secondary)', padding: '6px 12px', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
            <Globe size={16} color="var(--accent-cyan)" />
            <select
              value={selectedAssetClass}
              onChange={(e) => onSelectAssetClass(e.target.value)}
              style={{
                background: 'transparent', color: '#fff', border: 'none',
                fontSize: '0.85rem', fontWeight: 600, outline: 'none', cursor: 'pointer'
              }}
            >
              <option value="INDIAN_EQUITY">Indian Stocks (NSE)</option>
              <option value="US_EQUITY">US Stocks (NASDAQ/NYSE)</option>
              <option value="CRYPTO">Crypto (24/7)</option>
              <option value="FOREX">Forex Pairs</option>
              <option value="INDEX">Global Indices</option>
            </select>
          </div>

          {/* Tier 2: Dynamic Symbol Selector */}
          <div style={{ display: 'flex', gap: '4px', background: 'var(--bg-secondary)', padding: '4px', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
            {availableAssets.map(ast => (
              <button
                key={ast.symbol}
                className={`btn-secondary ${selectedAsset === ast.symbol ? 'active' : ''}`}
                onClick={() => onSelectAsset(ast.symbol)}
                style={{ padding: '6px 12px', fontSize: '0.82rem', fontWeight: 600 }}
              >
                {ast.symbol}
              </button>
            ))}
          </div>

          <button 
            className="btn-primary" 
            onClick={onRefresh} 
            disabled={isRefreshing}
            style={{ opacity: isRefreshing ? 0.6 : 1 }}
          >
            <RefreshCw size={16} className={isRefreshing ? 'spin' : ''} />
            {isRefreshing ? 'Refreshing...' : 'Refresh Data'}
          </button>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', flexWrap: 'wrap' }}>
        <button 
          className={`btn-secondary ${activeTab === 'dashboard' ? 'active' : ''}`}
          onClick={() => onSelectTab && onSelectTab('dashboard')}
          style={{ padding: '8px 16px', fontSize: '0.85rem', fontWeight: 600 }}
        >
          📊 Dashboard & Predictions
        </button>
        <button 
          className={`btn-secondary ${activeTab === 'live-research' ? 'active' : ''}`}
          onClick={() => onSelectTab && onSelectTab('live-research')}
          style={{ padding: '8px 16px', fontSize: '0.85rem', fontWeight: 600 }}
        >
          ⚡ Live Research & Analytics
        </button>
        <button 
          className={`btn-secondary ${activeTab === 'ablation' ? 'active' : ''}`}
          onClick={() => onSelectTab && onSelectTab('ablation')}
          style={{ padding: '8px 16px', fontSize: '0.85rem', fontWeight: 600 }}
        >
          🧪 Feature Study & Ablation
        </button>
      </div>



      {/* Mandatory Research Disclaimer Banner */}
      <div className="disclaimer-banner">
        <AlertTriangle size={18} style={{ flexShrink: 0 }} />
        <div>
          <strong>ACADEMIC RESEARCH DISCLAIMER:</strong> StockSense AI is an educational machine-learning research platform. It is <strong>NOT</strong> financial advice and does not guarantee trading returns or prediction accuracy. Predictions represent historical model probabilities, NOT certainty.
        </div>
      </div>
    </header>
  );
}
