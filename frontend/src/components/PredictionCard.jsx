import React from 'react';
import { ArrowUpRight, ArrowDownRight, ShieldAlert, Cpu, AlertTriangle, Radio, CheckCircle, XCircle, Clock } from 'lucide-react';
import { api, getWebSocketUrl } from '../api';

export function PredictionCard({ prediction, symbol, selectedModel, onSelectModel }) {
  const [liveTick, setLiveTick] = React.useState(null);
  const [isPulsing, setIsPulsing] = React.useState(false);
  const [trackerStats, setTrackerStats] = React.useState(null);

  React.useEffect(() => {
    if (!symbol) return;
    setLiveTick(null); // Clear stale tick from previous symbol
    const wsUrl = getWebSocketUrl(symbol);
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data && data.price && (!data.symbol || data.symbol.toUpperCase() === symbol.toUpperCase())) {
          setLiveTick(data);
          setIsPulsing(true);
          setTimeout(() => setIsPulsing(false), 800);
        }
      } catch (err) {
        console.error("Error parsing WebSocket tick:", err);
      }
    };

    // Fetch real tracker stats from DB API
    api.getPredictionTrackerStats(symbol)
      .then(res => setTrackerStats(res.data))
      .catch(() => setTrackerStats(null));

    return () => {
      ws.close();
    };
  }, [symbol]);

  if (!prediction) {
    return (
      <div className="glass-card" style={{ height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', textAlign: 'center', padding: '30px' }}>
        <Cpu size={36} color="var(--accent-cyan)" className="spin" style={{ marginBottom: '12px' }} />
        <h3 className="heading-font" style={{ fontSize: '1.1rem', marginBottom: '6px' }}>Analyzing {symbol}...</h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.82rem' }}>Computing feature matrix & XGBoost prediction model...</p>
      </div>
    );
  }

  if (prediction.status === "Model not trained") {
    return (
      <div className="glass-card" style={{ height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', textAlign: 'center', padding: '30px' }}>
        <Cpu size={40} color="var(--text-muted)" style={{ marginBottom: '12px' }} />
        <h3 className="heading-font" style={{ fontSize: '1.15rem', marginBottom: '6px' }}>Model Not Trained</h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', maxWidth: '320px' }}>
          No trained model found for asset symbol <strong>{symbol}</strong>. Select a trained asset or train models first.
        </p>
        <div style={{ marginTop: '16px', background: 'var(--bg-secondary)', padding: '6px 14px', borderRadius: '8px', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
          Status: MODEL NOT TRAINED
        </div>
      </div>
    );
  }

  const isUp = prediction.predicted_direction === "UP";
  const probUpPct = (prediction.probability_up * 100).toFixed(1);
  const probDownPct = (prediction.probability_down * 100).toFixed(1);
  const riskCategory = prediction.risk?.risk_category || "MEDIUM";

  const validLiveTick = (liveTick && liveTick.symbol && liveTick.symbol.toUpperCase() === symbol.toUpperCase()) ? liveTick : null;
  const currentPriceVal = validLiveTick?.price ? validLiveTick.price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : (prediction.latest_price ? prediction.latest_price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : 'N/A');

  const quoteInfo = prediction.quote_info || {};
  const dataStatus = liveTick?.data_status || quoteInfo.data_status || "HISTORICAL";
  const lastUpdated = liveTick?.timestamp ? new Date(liveTick.timestamp).toLocaleTimeString() : (quoteInfo.last_updated || new Date().toLocaleTimeString());
  const providerName = liveTick?.provider || quoteInfo.provider || "Finnhub";

  const statusBadgeStyle = 
    dataStatus === "LIVE" ? { bg: 'rgba(16, 185, 129, 0.15)', color: 'var(--up-green)', label: `🟢 LIVE (${providerName})` } :
    dataStatus === "DELAYED" ? { bg: 'rgba(245, 158, 11, 0.15)', color: '#f59e0b', label: '🟡 DELAYED QUOTE' } :
    dataStatus === "STALE" ? { bg: 'rgba(239, 68, 68, 0.15)', color: 'var(--down-red)', label: '🔴 STALE TICK' } :
    dataStatus === "RECONNECTING" ? { bg: 'rgba(249, 115, 22, 0.15)', color: '#f97316', label: '🟠 RECONNECTING' } :
    dataStatus === "UNAVAILABLE" ? { bg: 'rgba(239, 68, 68, 0.15)', color: 'var(--down-red)', label: '🔴 DATA UNAVAILABLE' } :
    { bg: 'rgba(148, 163, 184, 0.15)', color: '#94a3b8', label: '⚪ HISTORICAL BAR' };

  // Real database tracker stats (zero hardcoded values)
  const totalPreds = trackerStats ? trackerStats.total_predictions : 0;
  const correctPreds = trackerStats ? trackerStats.correct_count : 0;
  const wrongPreds = trackerStats ? trackerStats.wrong_count : 0;
  const resolvedDisplay = trackerStats ? trackerStats.resolved_display : "No resolved predictions yet";
  const accuracyDisplay = trackerStats ? trackerStats.accuracy_display : "INSUFFICIENT LIVE SAMPLE SIZE";

  return (
    <div className="glass-card" style={{ height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
      <div>
        {/* Out of Sample Pill Tag & Data Freshness Tag */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
          <span style={{ background: 'rgba(0, 242, 254, 0.12)', color: 'var(--accent-cyan)', border: '1px solid rgba(0, 242, 254, 0.3)', padding: '3px 10px', borderRadius: '12px', fontSize: '0.72rem', fontWeight: 700, letterSpacing: '0.5px' }}>
            [STRICT OUT-OF-SAMPLE / HELD-OUT TEST SET]
          </span>

          <span style={{ background: statusBadgeStyle.bg, color: statusBadgeStyle.color, border: `1px solid ${statusBadgeStyle.color}`, padding: '3px 10px', borderRadius: '12px', fontSize: '0.72rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Radio size={12} className={dataStatus === "LIVE" ? "spin" : ""} /> {statusBadgeStyle.label}
          </span>
        </div>

        {/* Asset Title & Live Price Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '10px' }}>
          <div>
            <h3 className="heading-font" style={{ fontSize: '1.25rem', fontWeight: 800 }}>
              {symbol.includes("BTC") ? "BTC/USD" : symbol}
            </h3>
            <div style={{ fontSize: '1.5rem', fontWeight: 800, color: isPulsing ? 'var(--accent-cyan)' : '#fff', transition: 'color 0.3s' }} className="mono-font">
              ${currentPriceVal}
            </div>
          </div>

          {/* Model Selector Dropdown */}
          <select
            value={selectedModel}
            onChange={(e) => onSelectModel(e.target.value)}
            style={{ 
              background: 'var(--bg-secondary)', color: 'var(--text-primary)',
              border: '1px solid var(--border-color)', borderRadius: '8px',
              padding: '6px 12px', fontSize: '0.8rem', outline: 'none'
            }}
          >
            <option value="XGBoost">XGBoost v1.0</option>
            <option value="RandomForest">Random Forest</option>
            <option value="LogisticRegression">Logistic Regression</option>
            <option value="MajorityBaseline">Majority Class Baseline</option>
          </select>
        </div>

        {/* AI Direction & Probability Card */}
        <div style={{ 
          background: isUp ? 'var(--up-green-bg)' : 'var(--down-red-bg)',
          border: `1px solid ${isUp ? 'rgba(16, 185, 129, 0.4)' : 'rgba(239, 68, 68, 0.4)'}`,
          borderRadius: '16px', padding: '16px', textAlign: 'center', marginBottom: '16px'
        }}>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            AI Research Prediction
          </div>

          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', color: isUp ? 'var(--up-green)' : 'var(--down-red)' }}>
            {isUp ? <ArrowUpRight size={28} /> : <ArrowDownRight size={28} />}
            <span className="heading-font" style={{ fontSize: '1.8rem', fontWeight: 800 }}>
              {prediction.predicted_direction}
            </span>
          </div>

          <div style={{ marginTop: '8px', fontSize: '1.15rem', fontWeight: 700 }}>
            <span style={{ color: 'var(--up-green)' }}>UP {probUpPct}%</span>
            <span style={{ margin: '0 8px', color: 'var(--text-muted)' }}>|</span>
            <span style={{ color: 'var(--down-red)' }}>DOWN {probDownPct}%</span>
          </div>
        </div>

        {/* Probability Gauge Bar */}
        <div style={{ marginBottom: '16px' }}>
          <div style={{ height: '8px', background: 'var(--down-red)', borderRadius: '4px', overflow: 'hidden', display: 'flex' }}>
            <div style={{ width: `${probUpPct}%`, background: 'var(--up-green)', transition: 'width 0.5s ease' }} />
          </div>
        </div>

        {/* Details Grid: Prediction Made, Actual Result, Model, Accuracy */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '14px' }}>
          <div style={{ background: 'var(--bg-secondary)', padding: '10px 12px', borderRadius: '10px' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Prediction made:</div>
            <strong className="mono-font" style={{ fontSize: '0.88rem' }}>{lastUpdated}</strong>
          </div>

          <div style={{ background: 'var(--bg-secondary)', padding: '10px 12px', borderRadius: '10px' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Actual result:</div>
            <strong style={{ fontSize: '0.88rem', color: resolvedDisplay.includes('✅') ? 'var(--up-green)' : (resolvedDisplay.includes('❌') ? 'var(--down-red)' : 'var(--text-muted)') }}>
              {resolvedDisplay}
            </strong>
          </div>

          <div style={{ background: 'var(--bg-secondary)', padding: '10px 12px', borderRadius: '10px' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Model:</div>
            <strong style={{ fontSize: '0.88rem', color: 'var(--accent-cyan)' }}>{selectedModel} v1.0</strong>
          </div>

          <div style={{ background: 'var(--bg-secondary)', padding: '10px 12px', borderRadius: '10px' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Recent OOS Live Accuracy:</div>
            <strong className="mono-font" style={{ fontSize: '0.82rem', color: accuracyDisplay.includes('%') ? 'var(--up-green)' : 'var(--text-muted)' }}>{accuracyDisplay}</strong>
          </div>
        </div>

        {/* Live Prediction Counter Stats */}
        <div style={{ background: 'var(--bg-secondary)', padding: '10px 14px', borderRadius: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', fontSize: '0.82rem' }}>
          <div>
            <span style={{ color: 'var(--text-muted)' }}>Predictions: </span>
            <strong className="mono-font">{totalPreds}</strong>
          </div>
          <div>
            <span style={{ color: 'var(--up-green)' }}>Correct: </span>
            <strong className="mono-font" style={{ color: 'var(--up-green)' }}>{correctPreds}</strong>
          </div>
          <div>
            <span style={{ color: 'var(--down-red)' }}>Wrong: </span>
            <strong className="mono-font" style={{ color: 'var(--down-red)' }}>{wrongPreds}</strong>
          </div>
        </div>
      </div>

      {/* Mandatory Calibration & Academic Profitability Warning */}
      <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', lineHeight: '1.4', background: 'rgba(239, 68, 68, 0.08)', border: '1px solid rgba(239, 68, 68, 0.2)', padding: '8px 12px', borderRadius: '8px' }}>
        <AlertTriangle size={14} color="var(--down-red)" style={{ display: 'inline', marginRight: '6px' }} />
        <strong>ACADEMIC RESEARCH DISCLAIMER:</strong> A {probUpPct}% {prediction.predicted_direction} directional prediction is an empirical statistical estimate and does NOT guarantee profitability or trading accuracy.
      </div>
    </div>
  );
}
