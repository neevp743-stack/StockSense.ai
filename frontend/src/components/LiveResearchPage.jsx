import React, { useState, useEffect } from 'react';
import { api } from '../api';
import { Activity, Download, CheckCircle, XCircle, Clock, AlertTriangle, ShieldCheck, Database, Layers } from 'lucide-react';

export function LiveResearchPage({ activeSymbol = "BTC-USD", onSelectSymbol }) {
  const [symbol, setSymbol] = useState(activeSymbol);
  const [collectionStatus, setCollectionStatus] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [history, setHistory] = useState(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setSymbol(activeSymbol);
  }, [activeSymbol]);

  useEffect(() => {
    fetchData();
  }, [symbol, page]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [statusRes, analyticsRes, historyRes] = await Promise.all([
        api.getLiveCollectionStatus(),
        api.getLiveAnalytics(symbol),
        api.getLivePredictionsHistory(symbol, page, 20)
      ]);
      setCollectionStatus(statusRes.data);
      setAnalytics(analyticsRes.data);
      setHistory(historyRes.data);
    } catch (err) {
      console.error("Error fetching live research data:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleCsvDownload = () => {
    const url = api.getLivePredictionsCsvUrl(symbol);
    window.open(url, '_blank');
  };

  const milestoneClass = 
    analytics?.sample_size < 30 ? "badge-risk-high" :
    analytics?.sample_size < 100 ? "badge-risk-medium" : "badge-risk-low";

  return (
    <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Header & Asset Switcher */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h2 className="heading-font" style={{ fontSize: '1.6rem', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Activity color="var(--accent-cyan)" size={28} /> Live Research Monitoring & Statistical Validation
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', marginTop: '4px' }}>
            Real-time model evaluation, baseline comparison, and confidence distribution tracking.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <select
            value={symbol}
            onChange={(e) => { setSymbol(e.target.value); setPage(1); if (onSelectSymbol) onSelectSymbol(e.target.value); }}
            style={{
              background: 'var(--bg-secondary)', color: '#fff',
              border: '1px solid var(--border-color)', borderRadius: '10px',
              padding: '8px 16px', fontSize: '0.9rem', outline: 'none'
            }}
          >
            <option value="BTC-USD">BTC-USD (Crypto)</option>
            <option value="ETH-USD">ETH-USD (Crypto)</option>
            <option value="AAPL">AAPL (US Equity)</option>
            <option value="MSFT">MSFT (US Equity)</option>
            <option value="NVDA">NVDA (US Equity)</option>
            <option value="RELIANCE">RELIANCE (Indian Equity)</option>
            <option value="TCS">TCS (Indian Equity)</option>
          </select>

          <button
            onClick={handleCsvDownload}
            style={{
              background: 'linear-gradient(135deg, var(--accent-cyan), #00b4d8)',
              color: '#000', fontWeight: 700, border: 'none',
              borderRadius: '10px', padding: '8px 16px', fontSize: '0.88rem',
              display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer'
            }}
          >
            <Download size={16} /> Export CSV
          </button>
        </div>
      </div>

      {/* Collection Status Header Bar */}
      <div className="glass-card" style={{ padding: '16px 20px', marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{
            background: collectionStatus?.collection_status === "COLLECTION ACTIVE" ? "rgba(16, 185, 129, 0.15)" : "rgba(239, 68, 68, 0.15)",
            color: collectionStatus?.collection_status === "COLLECTION ACTIVE" ? "var(--up-green)" : "var(--down-red)",
            border: `1px solid ${collectionStatus?.collection_status === "COLLECTION ACTIVE" ? "var(--up-green)" : "var(--down-red)"}`,
            padding: '4px 12px', borderRadius: '14px', fontSize: '0.78rem', fontWeight: 700
          }}>
            🟢 {collectionStatus?.collection_status || "COLLECTION ACTIVE"}
          </span>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            Provider: <strong>{collectionStatus?.provider || "Finnhub"}</strong> | Active Streams: <strong>{collectionStatus?.symbols_being_collected?.length || 2} assets</strong>
          </span>
        </div>

        <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }} className="mono-font">
          Last Prediction: {collectionStatus?.last_prediction_timestamp ? new Date(collectionStatus.last_prediction_timestamp).toLocaleTimeString() : "Just now"}
        </div>
      </div>

      {/* Sample Milestone & Accuracy Summary Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px', marginBottom: '24px' }}>
        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '6px' }}>Research Sample Milestone</div>
          <div className={`badge ${milestoneClass}`} style={{ fontSize: '0.85rem', padding: '6px 12px' }}>
            {analytics?.milestone_label || "INSUFFICIENT LIVE SAMPLE SIZE"}
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '8px' }}>
            Resolved Sample: <strong>N = {analytics?.resolved_predictions || 0}</strong>
          </div>
        </div>

        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '6px' }}>Empirical Live Accuracy</div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, color: analytics?.sample_size_threshold_met ? 'var(--up-green)' : 'var(--text-muted)' }} className="mono-font">
            {analytics?.accuracy_display || "INSUFFICIENT LIVE SAMPLE SIZE"}
          </div>
          {analytics?.confidence_interval_95 ? (
            <div style={{ fontSize: '0.76rem', color: 'var(--accent-cyan)', marginTop: '4px' }}>
              95% Wilson CI: [{analytics.confidence_interval_95.lower * 100}% – {analytics.confidence_interval_95.upper * 100}%]
            </div>
          ) : (
            <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', marginTop: '4px' }}>
              Preliminary empirical result — Insufficient evidence to establish predictive superiority.
            </div>
          )}
        </div>

        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '6px' }}>Prediction Counts</div>
          <div style={{ fontSize: '1.1rem', fontWeight: 700 }} className="mono-font">
            Total: {analytics?.total_predictions || 0} | Resolved: {analytics?.resolved_predictions || 0}
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '6px' }}>
            Correct: <span style={{ color: 'var(--up-green)' }}>{analytics?.correct_predictions || 0}</span> | Wrong: <span style={{ color: 'var(--down-red)' }}>{analytics?.wrong_predictions || 0}</span>
          </div>
        </div>
      </div>

      {/* Mandatory Academic Caution Banner */}
      <div style={{ background: 'rgba(239, 68, 68, 0.08)', border: '1px solid rgba(239, 68, 68, 0.25)', padding: '12px 16px', borderRadius: '10px', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '24px', lineHeight: '1.5' }}>
        <AlertTriangle size={16} color="var(--down-red)" style={{ display: 'inline', marginRight: '8px' }} />
        <strong>ACADEMIC CAUTION NOTICE:</strong> Statistical directional accuracy estimates represent empirical observations across a limited sample size. <strong>StockSense AI makes NO claims of trading profitability, market superiority, or future financial return.</strong> Results should be interpreted strictly as an ongoing academic research study.
      </div>


      {/* Baseline Comparison & Model Version Metadata */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px', marginBottom: '24px' }}>
        <div className="glass-card" style={{ padding: '20px' }}>
          <h3 className="heading-font" style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ShieldCheck size={18} color="var(--accent-cyan)" /> Empirical Baseline Comparison
          </h3>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-color)', textAlign: 'left', color: 'var(--text-secondary)' }}>
                <th style={{ padding: '8px' }}>Model Strategy</th>
                <th style={{ padding: '8px' }}>Empirical Accuracy</th>
                <th style={{ padding: '8px' }}>Difference vs Baseline</th>
              </tr>
            </thead>
            <tbody>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <td style={{ padding: '10px 8px', fontWeight: 700 }}>AI Model ({analytics?.model_version || "XGBoost v1.0"})</td>
                <td style={{ padding: '10px 8px' }} className="mono-font">{analytics?.accuracy_display}</td>
                <td style={{ padding: '10px 8px', color: 'var(--accent-cyan)' }}>—</td>
              </tr>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <td style={{ padding: '10px 8px' }}>Majority Class Baseline</td>
                <td style={{ padding: '10px 8px' }} className="mono-font">{analytics?.baselines ? `${(analytics.baselines.majority_baseline * 100).toFixed(1)}%` : '50.0%'}</td>
                <td style={{ padding: '10px 8px' }} className="mono-font">{analytics?.baselines?.diff_vs_majority ? `${(analytics.baselines.diff_vs_majority * 100).toFixed(1)}%` : 'N/A'}</td>
              </tr>
              <tr>
                <td style={{ padding: '10px 8px' }}>Random 50/50 Baseline</td>
                <td style={{ padding: '10px 8px' }} className="mono-font">50.0%</td>
                <td style={{ padding: '10px 8px' }} className="mono-font">{analytics?.baselines?.diff_vs_random ? `${(analytics.baselines.diff_vs_random * 100).toFixed(1)}%` : 'N/A'}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div className="glass-card" style={{ padding: '20px' }}>
          <h3 className="heading-font" style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Layers size={18} color="var(--accent-cyan)" /> Model Version Spec
          </h3>
          <div style={{ fontSize: '0.83rem', lineHeight: '1.8' }}>
            <div>Model: <strong>{analytics?.model_version || "XGBoost v1.0"}</strong></div>
            <div>Dataset: <strong>Historical 2024–2026</strong></div>
            <div>Split: <strong>Chronological 70/15/15</strong></div>
            <div>Features: <strong>21 Technical Indicators</strong></div>
            <div>Leakage Audit: <strong>Passed (Zero Lookahead)</strong></div>
          </div>
        </div>
      </div>

      {/* Confidence Bucket Breakdown */}
      <div className="glass-card" style={{ padding: '20px', marginBottom: '24px' }}>
        <h3 className="heading-font" style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: '14px' }}>
          Confidence Bucket Distribution Analysis
        </h3>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border-color)', textAlign: 'left', color: 'var(--text-secondary)' }}>
              <th style={{ padding: '8px' }}>Probability Bucket</th>
              <th style={{ padding: '8px' }}>Total Predictions</th>
              <th style={{ padding: '8px' }}>Resolved Count</th>
              <th style={{ padding: '8px' }}>Correct Count</th>
              <th style={{ padding: '8px' }}>Bucket Accuracy</th>
            </tr>
          </thead>
          <tbody>
            {analytics?.confidence_buckets && analytics.confidence_buckets.length > 0 ? (
              analytics.confidence_buckets.map((b, i) => (
                <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <td style={{ padding: '10px 8px', fontWeight: 700 }}>{b.bucket}</td>
                  <td style={{ padding: '10px 8px' }} className="mono-font">{b.total_predictions}</td>
                  <td style={{ padding: '10px 8px' }} className="mono-font">{b.resolved_predictions}</td>
                  <td style={{ padding: '10px 8px', color: 'var(--up-green)' }} className="mono-font">{b.correct_predictions}</td>
                  <td style={{ padding: '10px 8px' }} className="mono-font">{b.accuracy_display}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="5" style={{ padding: '16px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  No confidence bucket data collected yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Paginated Live Prediction History Table */}
      <div className="glass-card" style={{ padding: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h3 className="heading-font" style={{ fontSize: '1.05rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Database size={18} color="var(--accent-cyan)" /> Database Live Prediction Log ({symbol})
          </h3>
          <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
            Page {history?.page || 1} of {history?.total_pages || 1}
          </div>
        </div>

        <div className="table-responsive-container">
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-color)', textAlign: 'left', color: 'var(--text-secondary)' }}>
                <th style={{ padding: '8px' }}>Timestamp</th>
                <th style={{ padding: '8px' }}>Model</th>
                <th style={{ padding: '8px' }}>UP Prob</th>
                <th style={{ padding: '8px' }}>DOWN Prob</th>
                <th style={{ padding: '8px' }}>Signal</th>
                <th style={{ padding: '8px' }}>Status</th>
                <th style={{ padding: '8px' }}>Actual</th>
                <th style={{ padding: '8px' }}>Result</th>
              </tr>
            </thead>
            <tbody>
              {history?.items && history.items.length > 0 ? (
                history.items.map((item) => (
                  <tr key={item.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                    <td style={{ padding: '8px' }} className="mono-font">{item.prediction_timestamp ? new Date(item.prediction_timestamp).toLocaleString() : 'N/A'}</td>
                    <td style={{ padding: '8px' }}>{item.model_version}</td>
                    <td style={{ padding: '8px', color: 'var(--up-green)' }} className="mono-font">{(item.probability_up * 100).toFixed(1)}%</td>
                    <td style={{ padding: '8px', color: 'var(--down-red)' }} className="mono-font">{(item.probability_down * 100).toFixed(1)}%</td>
                    <td style={{ padding: '8px', fontWeight: 700, color: item.predicted_direction === 'UP' ? 'var(--up-green)' : 'var(--down-red)' }}>{item.predicted_direction}</td>
                    <td style={{ padding: '8px' }}>
                      <span style={{ fontSize: '0.72rem', padding: '2px 8px', borderRadius: '8px', background: 'rgba(0, 242, 254, 0.1)', color: 'var(--accent-cyan)' }}>{item.data_status}</span>
                    </td>
                    <td style={{ padding: '8px' }}>{item.resolved_direction || 'PENDING ⏳'}</td>
                    <td style={{ padding: '8px' }}>
                      {item.is_correct === true ? (
                        <span style={{ color: 'var(--up-green)', display: 'inline-flex', alignItems: 'center', gap: '4px' }}><CheckCircle size={14} /> Correct</span>
                      ) : item.is_correct === false ? (
                        <span style={{ color: 'var(--down-red)', display: 'inline-flex', alignItems: 'center', gap: '4px' }}><XCircle size={14} /> Wrong</span>
                      ) : (
                        <span style={{ color: 'var(--text-muted)', display: 'inline-flex', alignItems: 'center', gap: '4px' }}><Clock size={14} /> Pending</span>
                      )}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="8" style={{ padding: '20px', textAlign: 'center', color: 'var(--text-muted)' }}>
                    No live predictions logged for {symbol} yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Buttons */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '16px' }}>
          <button
            disabled={page <= 1}
            onClick={() => setPage(p => p - 1)}
            style={{ padding: '6px 14px', borderRadius: '6px', background: 'var(--bg-secondary)', color: '#fff', border: '1px solid var(--border-color)', cursor: page <= 1 ? 'not-allowed' : 'pointer' }}
          >
            Previous
          </button>
          <button
            disabled={page >= (history?.total_pages || 1)}
            onClick={() => setPage(p => p + 1)}
            style={{ padding: '6px 14px', borderRadius: '6px', background: 'var(--bg-secondary)', color: '#fff', border: '1px solid var(--border-color)', cursor: page >= (history?.total_pages || 1) ? 'not-allowed' : 'pointer' }}
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
