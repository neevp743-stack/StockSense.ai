import React from 'react';
import { Search, Sparkles, Activity, ShieldCheck, Zap } from 'lucide-react';

export function DashboardHero({ onOpenSearch, selectedSymbol, onSelectSymbol }) {
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  };

  return (
    <div 
      className="glass-card" 
      style={{ 
        marginBottom: '24px', 
        position: 'relative', 
        overflow: 'hidden',
        background: 'linear-gradient(135deg, rgba(13, 19, 31, 0.95) 0%, rgba(19, 27, 44, 0.8) 100%)',
        border: '1px solid rgba(0, 242, 254, 0.15)',
        padding: '28px 32px'
      }}
    >
      {/* Background Accent Glow */}
      <div 
        style={{
          position: 'absolute',
          top: '-40px',
          right: '-40px',
          width: '300px',
          height: '300px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(0, 242, 254, 0.12) 0%, rgba(0, 0, 0, 0) 70%)',
          pointerEvents: 'none'
        }}
      />

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '20px', position: 'relative', zIndex: 1 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
            <span style={{ background: 'rgba(0, 242, 254, 0.12)', color: 'var(--accent-cyan)', border: '1px solid rgba(0, 242, 254, 0.3)', padding: '2px 10px', borderRadius: '12px', fontSize: '0.74rem', fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
              <Zap size={12} /> BLOOMBERG-GRADE INTELLIGENCE
            </span>
            <span style={{ background: 'rgba(16, 185, 129, 0.15)', color: 'var(--up-green)', border: '1px solid var(--up-green-border)', padding: '2px 10px', borderRadius: '12px', fontSize: '0.74rem', fontWeight: 700 }}>
              ● Markets Open
            </span>
          </div>

          <h2 className="heading-font" style={{ fontSize: '1.85rem', fontWeight: 800, color: '#fff', letterSpacing: '-0.02em' }}>
            {getGreeting()}, Neev
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem', marginTop: '4px', maxWidth: '540px' }}>
            AI-powered market intelligence & XGBoost probability model analysis for your watchlist.
          </p>
        </div>

        {/* Quick Search Input Trigger */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button
            onClick={onOpenSearch}
            style={{
              background: 'var(--bg-primary)',
              border: '1px solid var(--border-color)',
              borderRadius: '14px',
              padding: '12px 20px',
              color: 'var(--text-muted)',
              fontSize: '0.9rem',
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              cursor: 'pointer',
              minWidth: '280px',
              boxShadow: '0 4px 16px rgba(0, 0, 0, 0.3)',
              transition: 'border-color 0.2s'
            }}
            className="hover-border-glow"
          >
            <Search size={18} color="var(--accent-cyan)" />
            <span style={{ color: 'var(--text-secondary)', flexGrow: 1, textAlign: 'left' }}>Search stocks...</span>
            <kbd style={{ background: 'var(--bg-secondary)', color: 'var(--text-muted)', border: '1px solid var(--border-color)', padding: '2px 8px', borderRadius: '6px', fontSize: '0.72rem', fontWeight: 700 }}>
              /
            </kbd>
          </button>
        </div>
      </div>
    </div>
  );
}
