import React from 'react';
import { ArrowUpRight, ArrowDownRight, Cpu, Radio, AlertTriangle } from 'lucide-react';
import { api, getWebSocketUrl } from '../api';
import { formatPrice } from '../utils/formatters';

export function PredictionCard({ prediction, symbol, selectedModel, onSelectModel }) {
  const [liveTick, setLiveTick] = React.useState(null);
  const [isPulsing, setIsPulsing] = React.useState(false);
  const [trackerStats, setTrackerStats] = React.useState(null);

  React.useEffect(() => {
    if (!symbol) return;
    setLiveTick(null);
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
      </div>
    );
  }

  const isUp = prediction.predicted_direction === "UP";
  const probUpPct = (prediction.probability_up * 100).toFixed(1);
  const probDownPct = (prediction.probability_down * 100).toFixed(1);

  const validLiveTick = (liveTick && liveTick.symbol && liveTick.symbol.toUpperCase() === symbol.toUpperCase()) ? liveTick : null;
  const rawPrice = validLiveTick?.price || prediction.latest_price;
  const currentPriceDisplay = formatPrice(rawPrice, symbol);

  const quoteInfo = prediction.quote_info || {};
  const dataStatus = liveTick?.data_status || quoteInfo.data_status || "HISTORICAL";
  const lastUpdated = liveTick?.timestamp ? new Date(liveTick.timestamp).toLocaleTimeString() : (quoteInfo.last_updated || new Date().toLocaleTimeString());
  const providerName = liveTick?.provider || quoteInfo.provider || "Finnhub";

  const totalPreds = trackerStats ? trackerStats.total_predictions : 0;
  const correctPreds = trackerStats ? trackerStats.correct_count : 0;
  const wrongPreds = trackerStats ? trackerStats.wrong_count : 0;
  const accuracyDisplay = trackerStats ? trackerStats.accuracy_display : "INSUFFICIENT SAMPLE SIZE";

  return (
    <div className="glass-card" style={{ height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', padding: '24px' }}>
      <div>
        {/* Out of Sample Pill Tag & Data Status */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '8px' }}>
          <span style={{ background: 'rgba(0, 242, 254, 0.12)', color: 'var(--accent-cyan)', border: '1px solid rgba(0, 242, 254, 0.3)', padding: '3px 10px', borderRadius: '12px', fontSize: '0.72rem', fontWeight: 700 }}>
            [OUT-OF-SAMPLE TEST SET]
          </span>

          <span style={{ background: 'rgba(16, 185, 129, 0.15)', color: 'var(--up-green)', border: '1px solid var(--up-green-border)', padding: '3px 10px', borderRadius: '12px', fontSize: '0.72rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Radio size={12} className="spin" /> LIVE ({providerName})
          </span>
        </div>

        {/* Asset Title & Live Price Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px', flexWrap: 'wrap', gap: '10px' }}>
          <div>
            <h3 className="heading-font" style={{ fontSize: '1.3rem', fontWeight: 800, color: '#fff' }}>
              {symbol}
            </h3>
            <div style={{ fontSize: '1.6rem', fontWeight: 800, color: isPulsing ? 'var(--accent-cyan)' : '#fff', transition: 'color 0.3s' }} className="mono-font">
              {currentPriceDisplay}
            </div>
          </div>

          {/* Model Selector Dropdown */}
          <select
            value={selectedModel}
            onChange={(e) => onSelectModel(e.target.value)}
            style={{ 
              background: 'var(--bg-secondary)', color: 'var(--text-primary)',
              border: '1px solid var(--border-color)', borderRadius: '10px',
              padding: '6px 12px', fontSize: '0.82rem', outline: 'none', fontWeight: 600
            }}
          >
            <option value="XGBoost">XGBoost v1.0</option>
            <option value="RandomForest">Random Forest</option>
            <option value="LogisticRegression">Logistic Regression</option>
            <option value="MajorityBaseline">Majority Baseline</option>
          </select>
        </div>

        {/* AI Direction & Probability Card */}
        <div style={{ 
          background: isUp ? 'var(--up-green-bg)' : 'var(--down-red-bg)',
          border: `1px solid ${isUp ? 'var(--up-green-border)' : 'var(--down-red-border)'}`,
          borderRadius: '16px', padding: '18px', textAlign: 'center', marginBottom: '16px'
        }}>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '4px', textTransform: 'uppercase', fontWeight: 700, letterSpacing: '0.05em' }}>
            AI DIRECTION PREDICTION
          </div>

          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', color: isUp ? 'var(--up-green)' : 'var(--down-red)' }}>
            {isUp ? <ArrowUpRight size={32} /> : <ArrowDownRight size={32} />}
            <span className="heading-font" style={{ fontSize: '2rem', fontWeight: 800 }}>
              {prediction.predicted_direction}
            </span>
          </div>

          <div style={{ marginTop: '8px', fontSize: '1.25rem', fontWeight: 800 }}>
            <span style={{ color: 'var(--up-green)' }}>UP {probUpPct}%</span>
            <span style={{ margin: '0 8px', color: 'var(--text-muted)' }}>|</span>
            <span style={{ color: 'var(--down-red)' }}>DOWN {probDownPct}%</span>
          </div>
        </div>

        {/* Probability Gauge Bar */}
        <div style={{ marginBottom: '18px' }}>
          <div style={{ height: '8px', background: 'var(--down-red)', borderRadius: '4px', overflow: 'hidden', display: 'flex' }}>
            <div style={{ width: `${probUpPct}%`, background: 'var(--up-green)', transition: 'width 0.5s ease' }} />
          </div>
        </div>

        {/* Details Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '16px' }}>
          <div style={{ background: 'var(--bg-secondary)', padding: '10px 12px', borderRadius: '10px', border: '1px solid var(--border-color)' }}>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Prediction Horizon:</div>
            <strong style={{ fontSize: '0.85rem', color: '#fff' }}>Next Trading Session</strong>
          </div>

          <div style={{ background: 'var(--bg-secondary)', padding: '10px 12px', borderRadius: '10px', border: '1px solid var(--border-color)' }}>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Model Architecture:</div>
            <strong style={{ fontSize: '0.85rem', color: 'var(--accent-cyan)' }}>{selectedModel} v1.0</strong>
          </div>

          <div style={{ background: 'var(--bg-secondary)', padding: '10px 12px', borderRadius: '10px', border: '1px solid var(--border-color)' }}>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Confidence Tier:</div>
            <strong style={{ fontSize: '0.85rem', color: probUpPct > 65 || probDownPct > 65 ? 'var(--up-green)' : 'var(--risk-medium)' }}>
              {probUpPct > 65 || probDownPct > 65 ? 'STRONG CONFIDENCE' : 'MODERATE CONFIDENCE'}
            </strong>
          </div>

          <div style={{ background: 'var(--bg-secondary)', padding: '10px 12px', borderRadius: '10px', border: '1px solid var(--border-color)' }}>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>OOS Live Accuracy:</div>
            <strong className="mono-font" style={{ fontSize: '0.82rem', color: 'var(--accent-cyan)' }}>{accuracyDisplay}</strong>
          </div>
        </div>
      </div>

      {/* Research Disclaimer */}
      <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', lineHeight: '1.4', background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border-color)', padding: '8px 12px', borderRadius: '8px' }}>
        <AlertTriangle size={12} color="#fbbf24" style={{ display: 'inline', marginRight: '6px' }} />
        Research only — not financial advice. Directional estimates reflect empirical historical probabilities.
      </div>
    </div>
  );
}
