import React from 'react';
import { HelpCircle, Info } from 'lucide-react';

export function ExplanationCard({ explanations }) {
  if (!explanations || !explanations.factors || explanations.factors.length === 0) {
    return (
      <div className="glass-card" style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <p style={{ color: 'var(--text-muted)' }}>Explanations unavailable for this model.</p>
      </div>
    );
  }

  const factors = explanations.factors;
  const maxImpact = Math.max(...factors.map(f => Math.abs(f.impact_value)), 0.0001);

  return (
    <div className="glass-card" style={{ height: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <h3 className="heading-font" style={{ fontSize: '1.1rem', fontWeight: 700 }}>
            Model Explainability & Contributing Factors
          </h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Calculated via dynamic <span className="mono-font">{explanations.method}</span>
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          <Info size={14} /> Zero hardcoded values
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {factors.map((factor, idx) => {
          const impact = factor.impact_value;
          const isPositive = impact >= 0;
          const barWidth = Math.min(100, Math.max(10, (Math.abs(impact) / maxImpact) * 100));

          return (
            <div key={idx} style={{ background: 'var(--bg-secondary)', padding: '10px 14px', borderRadius: '10px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', marginBottom: '6px' }}>
                <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                  {factor.description}
                </span>
                <span className="mono-font" style={{ fontWeight: 600, color: isPositive ? 'var(--up-green)' : 'var(--down-red)' }}>
                  {isPositive ? '+' : ''}{impact.toFixed(4)} SHAP
                </span>
              </div>

              {/* Progress Bar showing SHAP impact */}
              <div style={{ height: '6px', background: 'rgba(255,255,255,0.05)', borderRadius: '3px', overflow: 'hidden' }}>
                <div 
                  style={{ 
                    width: `${barWidth}%`, 
                    background: isPositive ? 'var(--up-green)' : 'var(--down-red)',
                    height: '100%',
                    borderRadius: '3px'
                  }} 
                />
              </div>
            </div>
          );
        })}
      </div>

      <div style={{ marginTop: '16px', fontSize: '0.75rem', color: 'var(--text-muted)', lineHeight: '1.4' }}>
        * Positive SHAP values increase UP prediction probability, while negative values push toward DOWN prediction.
      </div>
    </div>
  );
}
