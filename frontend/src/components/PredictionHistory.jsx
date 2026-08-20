import React from 'react';
import { History, CheckCircle2, XCircle, Clock, AlertCircle } from 'lucide-react';

export function PredictionHistory({ predictions, symbol }) {
  if (!predictions || predictions.length === 0) {
    return (
      <div className="glass-card" style={{ marginBottom: '24px' }}>
        <h3 className="heading-font" style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '12px' }}>
          Prediction vs Reality — Historical Auto-Resolution Tracking
        </h3>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
          No logged predictions found yet. Generate predictions to start tracking automatic resolution against market close.
        </p>
      </div>
    );
  }

  // Calculate resolution stats
  const resolved = predictions.filter(p => p.actual_direction !== "PENDING");
  const correctCount = resolved.filter(p => p.is_correct === true).length;
  const wrongCount = resolved.filter(p => p.is_correct === false).length;
  const resolutionAccuracy = resolved.length > 0 ? ((correctCount / resolved.length) * 100).toFixed(1) : 'N/A';

  // Stock-wise breakdown
  const stockStats = {};
  resolved.forEach(p => {
    const sym = p.stock_symbol;
    if (!stockStats[sym]) stockStats[sym] = { correct: 0, total: 0 };
    stockStats[sym].total += 1;
    if (p.is_correct) stockStats[sym].correct += 1;
  });

  // Model-wise breakdown
  const modelStats = {};
  resolved.forEach(p => {
    const m = p.model_version || "XGBoost_v1.0.0";
    if (!modelStats[m]) modelStats[m] = { correct: 0, total: 0 };
    modelStats[m].total += 1;
    if (p.is_correct) modelStats[m].correct += 1;
  });

  return (
    <div className="glass-card" style={{ marginBottom: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h3 className="heading-font" style={{ fontSize: '1.2rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <History size={20} color="var(--accent-blue)" />
              Prediction vs Reality — Historical Tracking Log
            </h3>
            <span style={{ background: 'rgba(0, 242, 254, 0.12)', color: 'var(--accent-cyan)', border: '1px solid rgba(0, 242, 254, 0.3)', padding: '2px 8px', borderRadius: '10px', fontSize: '0.7rem', fontWeight: 700 }}>
              [STRICT OUT-OF-SAMPLE / HELD-OUT TEST SET EVALUATION]
            </span>
          </div>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
            Historical directional predictions logged at market close and automatically verified against next-day actual outcomes
          </p>
        </div>

        {/* Global Summary Metrics Badges */}
        <div style={{ display: 'flex', gap: '10px', fontSize: '0.82rem', flexWrap: 'wrap' }}>
          <div style={{ background: 'var(--bg-secondary)', padding: '6px 14px', borderRadius: '10px', border: '1px solid var(--border-color)' }}>
            Total Logged: <strong className="mono-font">{predictions.length}</strong>
          </div>
          <div style={{ background: 'var(--bg-secondary)', padding: '6px 14px', borderRadius: '10px', border: '1px solid var(--border-color)' }}>
            Correct: <strong className="mono-font" style={{ color: 'var(--up-green)' }}>{correctCount}</strong>
          </div>
          <div style={{ background: 'var(--bg-secondary)', padding: '6px 14px', borderRadius: '10px', border: '1px solid var(--border-color)' }}>
            Wrong: <strong className="mono-font" style={{ color: 'var(--down-red)' }}>{wrongCount}</strong>
          </div>
          <div style={{ background: 'var(--bg-secondary)', padding: '6px 14px', borderRadius: '10px', border: '1px solid var(--border-color)' }}>
            Resolution Accuracy: <strong className="mono-font" style={{ color: 'var(--accent-cyan)' }}>{resolutionAccuracy}%</strong>
          </div>
        </div>
      </div>

      {/* Stock-wise & Model-wise Accuracy Summary Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px', marginBottom: '20px' }}>
        {/* Stock-wise Accuracy */}
        <div style={{ background: 'var(--bg-secondary)', padding: '12px 16px', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '8px' }}>
            Stock-Wise Accuracy (Resolved Out-of-Sample Predictions)
          </div>
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            {Object.keys(stockStats).length === 0 ? (
              <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Pending resolution data</span>
            ) : (
              Object.entries(stockStats).map(([stk, s]) => {
                const acc = ((s.correct / s.total) * 100).toFixed(1);
                return (
                  <div key={stk} style={{ background: '#0a0d14', padding: '6px 12px', borderRadius: '8px', fontSize: '0.78rem', border: '1px solid var(--border-color)' }}>
                    <strong>{stk}</strong>: <span style={{ color: 'var(--accent-cyan)' }}>{acc}%</span> ({s.correct}/{s.total})
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Model-wise Accuracy */}
        <div style={{ background: 'var(--bg-secondary)', padding: '12px 16px', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '8px' }}>
            Model-Wise Accuracy Breakdown
          </div>
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            {Object.keys(modelStats).length === 0 ? (
              <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Pending resolution data</span>
            ) : (
              Object.entries(modelStats).map(([m, s]) => {
                const acc = ((s.correct / s.total) * 100).toFixed(1);
                const mName = m.replace('_v1.0.0', '');
                return (
                  <div key={m} style={{ background: '#0a0d14', padding: '6px 12px', borderRadius: '8px', fontSize: '0.78rem', border: '1px solid var(--border-color)' }}>
                    <strong>{mName}</strong>: <span style={{ color: 'var(--accent-cyan)' }}>{acc}%</span> ({s.correct}/{s.total})
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>

      {/* Main Resolution Table */}
      <div style={{ overflowX: 'auto', maxHeight: '340px' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem', textAlign: 'left' }}>
          <thead style={{ position: 'sticky', top: 0, background: '#121824', zIndex: 1 }}>
            <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-secondary)' }}>
              <th style={{ padding: '10px' }}>Stock</th>
              <th style={{ padding: '10px' }}>As of Date</th>
              <th style={{ padding: '10px' }}>Target Date</th>
              <th style={{ padding: '10px' }}>Predicted Direction</th>
              <th style={{ padding: '10px' }}>Prob UP</th>
              <th style={{ padding: '10px' }}>Risk Category</th>
              <th style={{ padding: '10px' }}>Actual Market Outcome</th>
              <th style={{ padding: '10px' }}>Prediction vs Reality</th>
            </tr>
          </thead>
          <tbody>
            {predictions.map((p) => {
              const isUp = p.predicted_direction === "UP";
              const isResolved = p.actual_direction !== "PENDING";
              const isCorrect = p.is_correct;

              return (
                <tr key={p.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                  <td style={{ padding: '10px', fontWeight: 600 }}>{p.stock_symbol}</td>
                  <td className="mono-font" style={{ padding: '10px', color: 'var(--text-secondary)' }}>{p.as_of_date}</td>
                  <td className="mono-font" style={{ padding: '10px' }}>{p.prediction_date}</td>
                  <td style={{ padding: '10px' }}>
                    <span className={`badge ${isUp ? 'badge-up' : 'badge-down'}`}>
                      {p.predicted_direction}
                    </span>
                  </td>
                  <td className="mono-font" style={{ padding: '10px' }}>{(p.probability_up * 100).toFixed(1)}%</td>
                  <td style={{ padding: '10px' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: 600, color: p.risk_category === 'HIGH' ? 'var(--risk-high)' : 'var(--text-secondary)' }}>
                      {p.risk_category}
                    </span>
                  </td>
                  <td style={{ padding: '10px' }}>
                    {isResolved ? (
                      <span className={`badge ${p.actual_direction === 'UP' ? 'badge-up' : 'badge-down'}`}>
                        {p.actual_direction}
                      </span>
                    ) : (
                      <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Pending Market Close</span>
                    )}
                  </td>
                  <td style={{ padding: '10px' }}>
                    {!isResolved ? (
                      <span style={{ color: '#f59e0b', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.8rem' }}>
                        <Clock size={14} /> Pending
                      </span>
                    ) : isCorrect ? (
                      <span style={{ color: 'var(--up-green)', display: 'flex', alignItems: 'center', gap: '4px', fontWeight: 600 }}>
                        <CheckCircle2 size={16} /> CORRECT
                      </span>
                    ) : (
                      <span style={{ color: 'var(--down-red)', display: 'flex', alignItems: 'center', gap: '4px', fontWeight: 600 }}>
                        <XCircle size={16} /> WRONG
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div style={{ marginTop: '16px', fontSize: '0.78rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '6px' }}>
        <AlertCircle size={14} />
        Research Disclaimer: Predictions are logged irrevocably upon creation and automatically verified against next-day market close price.
      </div>
    </div>
  );
}
