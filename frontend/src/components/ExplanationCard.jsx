import React, { useState } from 'react';
import { Info, HelpCircle, ChevronDown, ChevronUp, Layers } from 'lucide-react';

export function ExplanationCard({ explanations }) {
  const [isExpanded, setIsExpanded] = useState(true);

  if (!explanations || !explanations.factors || explanations.factors.length === 0) {
    return (
      <div className="glass-card" style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '30px' }}>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Explanations unavailable for this model.</p>
      </div>
    );
  }

  const factors = explanations.factors;
  const maxImpact = Math.max(...factors.map(f => Math.abs(f.impact_value)), 0.0001);

  return (
    <div className="glass-card" style={{ height: '100%', padding: '24px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <h3 className="heading-font" style={{ fontSize: '1.15rem', fontWeight: 800, color: '#fff' }}>
              Why is StockSense AI saying this?
            </h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '2px' }}>
              Key indicators driving current prediction
            </p>
          </div>

          <button 
            onClick={() => setIsExpanded(!isExpanded)}
            style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: '8px', color: 'var(--text-secondary)', padding: '4px 8px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.78rem' }}
          >
            {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            {isExpanded ? 'Collapse' : 'Expand'}
          </button>
        </div>

        {isExpanded && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {(() => {
              const sumWeights = factors.reduce((sum, f) => sum + Math.abs(f.impact_value), 0) || 1;
              return factors.map((factor, idx) => {
                const impact = factor.impact_value;
                const isPositive = impact >= 0;
                const barWidth = Math.min(100, Math.max(10, (Math.abs(impact) / maxImpact) * 100));
                const pct = ((Math.abs(impact) / sumWeights) * 100).toFixed(1);

                return (
                  <div key={idx} style={{ background: 'var(--bg-secondary)', padding: '12px 14px', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.84rem', marginBottom: '6px' }}>
                      <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                        {isPositive ? '▲ ' : '▼ '}{factor.description}
                      </span>
                      <span className="mono-font" style={{ fontWeight: 700, color: isPositive ? 'var(--up-green)' : 'var(--down-red)' }}>
                        {pct}% Influence
                      </span>
                    </div>

                    {/* Progress bar showing feature contribution */}
                    <div style={{ height: '6px', background: 'rgba(255,255,255,0.05)', borderRadius: '3px', overflow: 'hidden' }}>
                      <div 
                        style={{ 
                          width: `${barWidth}%`, 
                          background: isPositive ? 'var(--up-green)' : 'var(--down-red)',
                          height: '100%',
                          borderRadius: '3px',
                          transition: 'width 0.5s'
                        }} 
                      />
                    </div>
                  </div>
                );
              });
            })()}
          </div>
        )}
      </div>

      <div style={{ marginTop: '16px', fontSize: '0.74rem', color: 'var(--text-muted)', lineHeight: '1.4', display: 'flex', alignItems: 'center', gap: '6px' }}>
        <Info size={14} color="var(--accent-cyan)" />
        <span>Positive factors support an upward price expectation; negative factors support a downward price expectation.</span>
      </div>
    </div>
  );
}
