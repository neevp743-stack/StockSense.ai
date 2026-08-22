import React from 'react';
import { AlertCircle, RefreshCw, Layers } from 'lucide-react';

export function EmptyState({ 
  title = "No Data Available", 
  message = "No records found matching your request.", 
  actionText = null, 
  onAction = null,
  icon: Icon = Layers
}) {
  return (
    <div 
      className="glass-card" 
      style={{ 
        padding: '40px 24px', 
        textAlign: 'center', 
        display: 'flex', 
        flexDirection: 'column', 
        alignItems: 'center', 
        justifyContent: 'center',
        gap: '12px'
      }}
    >
      <div 
        style={{ 
          width: '52px', 
          height: '52px', 
          borderRadius: '16px', 
          background: 'var(--bg-secondary)', 
          border: '1px solid var(--border-color)',
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          color: 'var(--accent-cyan)'
        }}
      >
        <Icon size={26} />
      </div>

      <h3 className="heading-font" style={{ fontSize: '1.15rem', fontWeight: 800, color: '#fff' }}>
        {title}
      </h3>
      <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', maxWidth: '380px', lineHeight: '1.45' }}>
        {message}
      </p>

      {actionText && onAction && (
        <button className="btn-primary" onClick={onAction} style={{ marginTop: '8px' }}>
          <RefreshCw size={14} /> {actionText}
        </button>
      )}
    </div>
  );
}

export function ErrorFallbackCard({ 
  title = "Unable to load live market data", 
  message = "Historical data remains available. Retry connecting to update realtime quote feeds.", 
  onRetry = null 
}) {
  return (
    <div 
      style={{ 
        background: 'rgba(239, 68, 68, 0.08)', 
        border: '1px solid rgba(239, 68, 68, 0.25)', 
        borderRadius: '12px', 
        padding: '16px 20px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '12px',
        margin: '12px 0'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <AlertCircle size={22} color="var(--down-red)" style={{ flexShrink: 0 }} />
        <div>
          <strong style={{ fontSize: '0.88rem', color: '#fff' }}>{title}</strong>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '2px' }}>{message}</p>
        </div>
      </div>

      {onRetry && (
        <button 
          onClick={onRetry}
          style={{
            background: 'var(--bg-secondary)',
            color: '#fff',
            border: '1px solid var(--border-color)',
            borderRadius: '8px',
            padding: '6px 14px',
            fontSize: '0.8rem',
            fontWeight: 600,
            cursor: 'pointer',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px'
          }}
        >
          <RefreshCw size={12} /> Reconnect
        </button>
      )}
    </div>
  );
}
