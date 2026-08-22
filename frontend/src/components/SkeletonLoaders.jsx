import React from 'react';

export function ChartSkeleton() {
  return (
    <div className="glass-card" style={{ height: '480px', width: '100%', display: 'flex', flexDirection: 'column', gap: '16px', padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div className="skeleton-shimmer" style={{ width: '140px', height: '24px', borderRadius: '6px' }} />
          <div className="skeleton-shimmer" style={{ width: '100px', height: '32px', borderRadius: '6px' }} />
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          {[1, 2, 3, 4, 5].map(i => (
            <div key={i} className="skeleton-shimmer" style={{ width: '40px', height: '28px', borderRadius: '6px' }} />
          ))}
        </div>
      </div>

      <div style={{ flexGrow: 1, width: '100%', position: 'relative', overflow: 'hidden' }}>
        <div className="skeleton-shimmer" style={{ width: '100%', height: '100%', borderRadius: '12px' }} />
      </div>
    </div>
  );
}

export function PredictionSkeleton() {
  return (
    <div className="glass-card" style={{ height: '100%', minHeight: '340px', padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        <div className="skeleton-shimmer" style={{ width: '180px', height: '20px', borderRadius: '6px' }} />
        <div className="skeleton-shimmer" style={{ width: '100px', height: '20px', borderRadius: '6px' }} />
      </div>

      <div className="skeleton-shimmer" style={{ height: '110px', borderRadius: '16px' }} />

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="skeleton-shimmer" style={{ height: '48px', borderRadius: '10px' }} />
        ))}
      </div>
    </div>
  );
}

export function TechnicalGaugeSkeleton() {
  return (
    <div className="glass-card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
      <div className="skeleton-shimmer" style={{ width: '220px', height: '20px', borderRadius: '6px' }} />
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '14px' }}>
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="skeleton-shimmer" style={{ height: '80px', borderRadius: '12px' }} />
        ))}
      </div>
    </div>
  );
}
