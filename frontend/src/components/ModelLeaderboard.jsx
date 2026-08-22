import React from 'react';
import { Award, AlertTriangle } from 'lucide-react';

export function ModelLeaderboard({ performanceData, symbol }) {
  if (!performanceData || !performanceData.stock_wise || !performanceData.stock_wise[symbol]) {
    return (
      <div className="glass-card" style={{ marginBottom: '24px' }}>
        <h3 className="heading-font" style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '12px' }}>
          Model Evaluation Matrix — {symbol}
        </h3>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
          No trained evaluation metrics available yet for {symbol}. Click "Refresh Data" to train models.
        </p>
      </div>
    );
  }

  const stockModels = performanceData.stock_wise[symbol];

  return (
    <div className="glass-card" style={{ marginBottom: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h3 className="heading-font" style={{ fontSize: '1.2rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Award size={20} color="var(--accent-cyan)" />
              Model Performance Leaderboard — {symbol}
            </h3>
            <span style={{ background: 'rgba(0, 242, 254, 0.12)', color: 'var(--accent-cyan)', border: '1px solid rgba(0, 242, 254, 0.3)', padding: '2px 8px', borderRadius: '10px', fontSize: '0.7rem', fontWeight: 700 }}>
              [STRICT OUT-OF-SAMPLE / HELD-OUT TEST SET EVALUATION]
            </span>
          </div>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
            Empirical evaluation metrics calculated strictly on held-out 15% test set (179 unseen trading days)
          </p>
        </div>
      </div>

      <div className="table-responsive-container" style={{ marginBottom: '16px' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem', textAlign: 'left' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-secondary)' }}>
              <th style={{ padding: '10px' }}>Model Name</th>
              <th style={{ padding: '10px' }}>Test-Set Accuracy</th>
              <th style={{ padding: '10px' }}>Precision</th>
              <th style={{ padding: '10px' }}>Recall</th>
              <th style={{ padding: '10px' }}>F1 Score</th>
              <th style={{ padding: '10px' }}>ROC-AUC</th>
              <th style={{ padding: '10px' }}>Brier Score</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(stockModels).map(([modelName, metrics], idx) => {
              const acc = (metrics.accuracy * 100).toFixed(2);
              const prec = (metrics.precision * 100).toFixed(2);
              const rec = (metrics.recall * 100).toFixed(2);
              const f1 = metrics.f1_score ? metrics.f1_score.toFixed(4) : 'N/A';
              const auc = metrics.roc_auc ? metrics.roc_auc.toFixed(4) : 'N/A';
              const brier = metrics.brier_score ? metrics.brier_score.toFixed(4) : 'N/A';

              const isBest = idx === 0;

              return (
                <tr key={modelName} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)', background: isBest ? 'rgba(0, 242, 254, 0.05)' : 'transparent' }}>
                  <td style={{ padding: '12px 10px', fontWeight: 600 }}>
                    {modelName} {isBest && <span style={{ fontSize: '0.7rem', color: 'var(--accent-cyan)', marginLeft: '6px' }}>★ TOP MODEL</span>}
                  </td>
                  <td className="mono-font" style={{ padding: '10px', fontWeight: 700, color: 'var(--accent-cyan)' }}>
                    {acc}%
                  </td>
                  <td className="mono-font" style={{ padding: '10px' }}>{prec}%</td>
                  <td className="mono-font" style={{ padding: '10px' }}>{rec}%</td>
                  <td className="mono-font" style={{ padding: '10px' }}>{f1}</td>
                  <td className="mono-font" style={{ padding: '10px' }}>{auc}</td>
                  <td className="mono-font" style={{ padding: '10px', color: 'var(--text-secondary)' }}>{brier}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', lineHeight: '1.4', background: 'rgba(255, 255, 255, 0.03)', padding: '10px 14px', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <AlertTriangle size={16} color="var(--down-red)" />
        <span>
          <strong>ACADEMIC PROFITABILITY NOTE:</strong> Classification accuracy in the range of 45%–55% reflects empirical real-world financial noise and does <strong>NOT</strong> demonstrate reliable trading profitability.
        </span>
      </div>
    </div>
  );
}
