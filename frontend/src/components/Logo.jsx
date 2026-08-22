import React from 'react';

export function Logo({ size = 32, showText = true, animated = false }) {
  return (
    <div style={{ display: 'inline-flex', alignItems: 'center', gap: '10px', userSelect: 'none' }}>
      <div 
        style={{ 
          width: size, 
          height: size, 
          borderRadius: Math.max(8, Math.floor(size * 0.28)), 
          background: 'linear-gradient(135deg, #070a11 0%, #111827 100%)',
          border: '1px solid rgba(0, 242, 254, 0.35)',
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          boxShadow: animated ? '0 0 20px rgba(0, 242, 254, 0.4)' : '0 4px 14px rgba(0, 0, 0, 0.4)',
          position: 'relative',
          overflow: 'hidden',
          flexShrink: 0
        }}
        className={animated ? "pulse-glow" : ""}
      >
        {/* SVG Emblem: Candlestick + Neural Node Network */}
        <svg viewBox="0 0 100 100" style={{ width: '70%', height: '70%' }}>
          <defs>
            <linearGradient id="logoCyan" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#00f2fe" />
              <stop offset="100%" stopColor="#38bdf8" />
            </linearGradient>
          </defs>

          {/* Neural Line Trend */}
          <path d="M 15,75 L 38,52 L 55,62 L 85,25" fill="none" stroke="url(#logoCyan)" strokeWidth="7" strokeLinecap="round" strokeLinejoin="round"/>
          <path d="M 15,75 L 38,52 L 55,62 L 85,25" fill="none" stroke="#ffffff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" opacity="0.9"/>

          {/* Candlestick Wicks & Bars */}
          <line x1="38" y1="42" x2="38" y2="62" stroke="#10b981" strokeWidth="3"/>
          <rect x="34" y="47" width="8" height="10" fill="#10b981" rx="1"/>

          <line x1="85" y1="18" x2="85" y2="35" stroke="#10b981" strokeWidth="3"/>
          <rect x="81" y="22" width="8" height="9" fill="#10b981" rx="1"/>

          {/* Nodes */}
          <circle cx="15" cy="75" r="5" fill="#00f2fe"/>
          <circle cx="38" cy="52" r="5" fill="#38bdf8"/>
          <circle cx="55" cy="62" r="5" fill="#a855f7"/>
          <circle cx="85" cy="25" r="7" fill="#10b981"/>
          <circle cx="85" cy="25" r="3" fill="#ffffff"/>
        </svg>
      </div>

      {showText && (
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <span 
            className="heading-font" 
            style={{ 
              fontSize: `${Math.max(1, size * 0.5)}px`, 
              fontWeight: 800, 
              background: 'linear-gradient(90deg, #ffffff 0%, #cbd5e1 100%)', 
              WebkitBackgroundClip: 'text', 
              WebkitTextFillColor: 'transparent',
              lineHeight: 1.1
            }}
          >
            StockSense<span style={{ color: 'var(--accent-cyan)' }}>AI</span>
          </span>
          <span style={{ fontSize: `${Math.max(0.6, size * 0.22)}px`, color: 'var(--text-muted)', fontWeight: 600, letterSpacing: '0.05em', textTransform: 'uppercase' }}>
            Market Intelligence
          </span>
        </div>
      )}
    </div>
  );
}
