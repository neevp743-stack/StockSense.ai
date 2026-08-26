import React from 'react';
import { ShieldAlert, Target, TrendingUp, TrendingDown, Layers, Activity, DollarSign, CheckCircle, AlertCircle, Clock, BarChart2 } from 'lucide-react';
import { api } from '../api';
import { formatPrice } from '../utils/formatters';

export function TradeSetupPanel({ symbol, showStats = false }) {
  const [setup, setSetup] = React.useState(null);
  const [backtest, setBacktest] = React.useState(null);
  const [paperPerf, setPaperPerf] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);

  React.useEffect(() => {
    if (!symbol) return;
    setLoading(true);
    setError(null);

    const controller = new AbortController();
    const opts = { signal: controller.signal };

    // 1. Fetch Primary Trade Setup Object (Unblocked, renders immediately)
    api.getTradeSetup(symbol, opts)
      .then(res => {
        if (!controller.signal.aborted) {
          if (res && res.data) {
            setSetup(res.data);
          }
          setLoading(false);
        }
      })
      .catch(err => {
        if (!controller.signal.aborted) {
          console.error("Trade setup fetch error:", err);
          setError("Failed to load trade setup analytics.");
          setLoading(false);
        }
      });

    // 2. Fetch Secondary Backtest Analytics (Asynchronous non-blocking load)
    api.getTradeSetupBacktest(symbol, opts)
      .then(res => {
        if (!controller.signal.aborted && res && res.data) {
          setBacktest(res.data);
        }
      })
      .catch(() => {});

    // 3. Fetch Live Paper Tracker Analytics (Asynchronous non-blocking load)
    api.getPaperPerformance(symbol, opts)
      .then(res => {
        if (!controller.signal.aborted && res && res.data) {
          setPaperPerf(res.data);
        }
      })
      .catch(() => {});

    return () => {
      controller.abort();
    };
  }, [symbol]);


  if (loading) {
    return (
      <div className="glass-card" style={{ padding: '24px', textAlign: 'center' }}>
        <Activity size={32} color="var(--accent-cyan)" className="spin" style={{ marginBottom: '12px' }} />
        <h4 className="heading-font" style={{ fontSize: '1rem', color: '#fff' }}>Computing AI Trade Setup & Backtest for {symbol}...</h4>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>Evaluating entry zone, stop loss, R:R multiples, and out-of-sample backtest...</p>
      </div>
    );
  }

  if (error || !setup) {
    return (
      <div className="glass-card" style={{ padding: '20px', textAlign: 'center', color: 'var(--text-muted)' }}>
        <AlertCircle size={28} color="#ef4444" style={{ marginBottom: '8px' }} />
        <div>Trade setup analytics currently unavailable for {symbol}.</div>
      </div>
    );
  }

  const signal = setup.signal || 'HOLD';
  const isBuy = signal === 'BUY';
  const isSell = signal === 'SELL';
  const isHold = signal === 'HOLD';

  const signalColor = isBuy ? 'var(--up-green)' : (isSell ? 'var(--down-red)' : 'var(--risk-medium)');
  const signalBg = isBuy ? 'var(--up-green-bg)' : (isSell ? 'var(--down-red-bg)' : 'rgba(255, 255, 255, 0.05)');
  const signalBorder = isBuy ? 'var(--up-green-border)' : (isSell ? 'var(--down-red-border)' : 'rgba(255, 255, 255, 0.12)');

  const currPriceDisp = formatPrice(setup.current_price, symbol);
  const entryLowDisp = formatPrice(setup.entry_low, symbol);
  const entryHighDisp = formatPrice(setup.entry_high, symbol);
  const stopLossDisp = formatPrice(setup.stop_loss, symbol);
  const target1Disp = formatPrice(setup.target_1, symbol);
  const target2Disp = formatPrice(setup.target_2, symbol);

  return (
    <div className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Target size={20} color="var(--accent-cyan)" />
            <h3 className="heading-font" style={{ fontSize: '1.25rem', fontWeight: 800, color: '#fff', margin: 0 }}>
              AI TRADE SETUP ENGINE
            </h3>
            <span style={{ background: 'rgba(0, 242, 254, 0.12)', color: 'var(--accent-cyan)', border: '1px solid rgba(0, 242, 254, 0.3)', padding: '2px 8px', borderRadius: '10px', fontSize: '0.7rem', fontWeight: 700 }}>
              PHASE 14 DECISION SUPPORT
            </span>
          </div>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
            Deterministic trade setup generated from Phase 12 Calibrated XGBoost probabilities & technical structure.
          </p>
        </div>

        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>As-of Current Price</div>
          <div className="mono-font" style={{ fontSize: '1.3rem', fontWeight: 800, color: '#fff' }}>
            {currPriceDisp}
          </div>
        </div>
      </div>

      {/* Main Signal Banner */}
      <div style={{ 
        background: signalBg, border: `1px solid ${signalBorder}`, borderRadius: '16px', padding: '20px',
        display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', alignItems: 'center'
      }}>
        {/* Signal & Direction */}
        <div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', fontWeight: 700, letterSpacing: '0.05em' }}>
            AI RESEARCH SIGNAL
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginTop: '4px' }}>
            {isBuy && <TrendingUp size={36} color="var(--up-green)" />}
            {isSell && <TrendingDown size={36} color="var(--down-red)" />}
            {isHold && <Activity size={36} color="var(--risk-medium)" />}
            <div>
              <span className="heading-font" style={{ fontSize: '2rem', fontWeight: 900, color: signalColor }}>
                {signal}
              </span>
              <div style={{ fontSize: '0.82rem', color: 'var(--text-primary)', fontWeight: 600 }}>
                Probability: {(setup.probability_up * 100).toFixed(1)}% UP | {((1 - setup.probability_up) * 100).toFixed(1)}% DOWN
              </div>
            </div>
          </div>
        </div>

        {/* Confidence & Regime */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div style={{ background: 'rgba(0,0,0,0.2)', padding: '8px 12px', borderRadius: '10px', border: '1px solid var(--border-color)' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Confidence Tier:</div>
            <strong style={{ fontSize: '0.88rem', color: setup.confidence === 'HIGH' ? 'var(--up-green)' : (setup.confidence === 'MODERATE' ? 'var(--accent-cyan)' : 'var(--risk-medium)') }}>
              {setup.confidence} ({((setup.confidence_score || 0.5) * 100).toFixed(0)}% Score)
            </strong>
          </div>

          <div style={{ background: 'rgba(0,0,0,0.2)', padding: '8px 12px', borderRadius: '10px', border: '1px solid var(--border-color)' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Market Regime:</div>
            <strong style={{ fontSize: '0.85rem', color: 'var(--accent-cyan)' }}>
              {setup.combined_regime}
            </strong>
          </div>
        </div>
      </div>

      {/* Trade Parameters Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px' }}>
        <div style={{ background: 'var(--bg-secondary)', padding: '14px', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Entry Zone</div>
          <strong className="mono-font" style={{ fontSize: '1rem', color: '#fff' }}>
            {entryLowDisp} – {entryHighDisp}
          </strong>
          <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '4px' }}>{setup.entry_method}</div>
        </div>

        <div style={{ background: 'var(--bg-secondary)', padding: '14px', borderRadius: '12px', border: '1px solid var(--down-red-border)' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--down-red)' }}>Stop Loss</div>
          <strong className="mono-font" style={{ fontSize: '1rem', color: 'var(--down-red)' }}>
            {stopLossDisp}
          </strong>
          <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '4px' }}>{setup.stop_loss_method}</div>
        </div>

        <div style={{ background: 'var(--bg-secondary)', padding: '14px', borderRadius: '12px', border: '1px solid var(--up-green-border)' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--up-green)' }}>Target 1 (Conservative)</div>
          <strong className="mono-font" style={{ fontSize: '1rem', color: 'var(--up-green)' }}>
            {target1Disp}
          </strong>
          <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '4px' }}>R:R {setup.risk_reward_target_1} : 1</div>
        </div>

        <div style={{ background: 'var(--bg-secondary)', padding: '14px', borderRadius: '12px', border: '1px solid var(--up-green-border)' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--up-green)' }}>Target 2 (Extended)</div>
          <strong className="mono-font" style={{ fontSize: '1rem', color: 'var(--up-green)' }}>
            {target2Disp}
          </strong>
          <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '4px' }}>R:R {setup.risk_reward_target_2} : 1</div>
        </div>

        <div style={{ background: 'var(--bg-secondary)', padding: '14px', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Asset Liquidity</div>
          <strong style={{ fontSize: '0.95rem', color: setup.liquidity === 'HIGH' ? 'var(--up-green)' : 'var(--text-primary)' }}>
            {setup.liquidity} (Vol Ratio: {setup.volume_ratio})
          </strong>
          <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Bid/Ask Spread: {setup.bid_ask_available ? `${setup.bid_ask_spread}%` : 'N/A (Unavailable)'}
          </div>
        </div>

        <div style={{ background: 'var(--bg-secondary)', padding: '14px', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Expected 1-Day Move</div>
          <strong className="mono-font" style={{ fontSize: '0.95rem', color: 'var(--accent-cyan)' }}>
            ±{setup.expected_move_percent}%
          </strong>
          <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Range: {formatPrice(setup.expected_range_low, symbol)} – {formatPrice(setup.expected_range_high, symbol)}
          </div>
        </div>
      </div>

      {/* Positive & Negative Factors Explainability */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '12px' }}>
        <div style={{ background: 'rgba(16, 185, 129, 0.05)', border: '1px solid var(--up-green-border)', padding: '14px', borderRadius: '12px' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--up-green)', fontWeight: 700, marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <CheckCircle size={14} /> POSITIVE SUPPORTING FACTORS
          </div>
          {setup.positive_factors && setup.positive_factors.length > 0 ? (
            <ul style={{ margin: 0, paddingLeft: '16px', fontSize: '0.78rem', color: 'var(--text-primary)' }}>
              {setup.positive_factors.map((f, idx) => (
                <li key={idx} style={{ marginBottom: '4px' }}>{f}</li>
              ))}
            </ul>
          ) : (
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>No positive factors detected</div>
          )}
        </div>

        <div style={{ background: 'rgba(239, 68, 68, 0.05)', border: '1px solid var(--down-red-border)', padding: '14px', borderRadius: '12px' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--down-red)', fontWeight: 700, marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <AlertCircle size={14} /> CONTRADICTORY / RISK FACTORS
          </div>
          {setup.negative_factors && setup.negative_factors.length > 0 ? (
            <ul style={{ margin: 0, paddingLeft: '16px', fontSize: '0.78rem', color: 'var(--text-primary)' }}>
              {setup.negative_factors.map((f, idx) => (
                <li key={idx} style={{ marginBottom: '4px' }}>{f}</li>
              ))}
            </ul>
          ) : (
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>No high-risk factors detected</div>
          )}
        </div>
      </div>

      {/* Historical Setup Backtest & Live Paper Tracker Comparison */}
      {showStats && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
          {/* Historical Out-of-Sample Backtest Card */}
          <div style={{ background: 'var(--bg-secondary)', padding: '16px', borderRadius: '14px', border: '1px solid var(--border-color)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
              <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#fff', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <BarChart2 size={16} color="var(--accent-cyan)" /> HISTORICAL SETUP BACKTEST
              </span>
              <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Net Costs Deducted</span>
            </div>

            {backtest && !backtest.error ? (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', fontSize: '0.8rem' }}>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Valid Setups: </span>
                  <strong style={{ color: '#fff' }}>{backtest.number_of_trades}</strong>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Win Rate: </span>
                  <strong style={{ color: 'var(--up-green)' }}>{backtest.win_rate_pct}%</strong>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Avg Net Return: </span>
                  <strong style={{ color: backtest.average_net_return_pct >= 0 ? 'var(--up-green)' : 'var(--down-red)' }}>
                    {backtest.average_net_return_pct}%
                  </strong>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Profit Factor: </span>
                  <strong style={{ color: 'var(--accent-cyan)' }}>{backtest.profit_factor}</strong>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Target 1 Hit: </span>
                  <strong style={{ color: '#fff' }}>{backtest.target_1_hit_rate_pct}%</strong>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Stop Loss Hit: </span>
                  <strong style={{ color: 'var(--down-red)' }}>{backtest.stop_loss_rate_pct}%</strong>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Max Drawdown: </span>
                  <strong style={{ color: 'var(--down-red)' }}>{backtest.maximum_drawdown_pct}%</strong>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Ambiguous Candles: </span>
                  <strong style={{ color: 'var(--risk-medium)' }}>{backtest.ambiguous_count}</strong>
                </div>
              </div>
            ) : (
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Backtest statistics loading or insufficient historical setups.</div>
            )}
          </div>

          {/* Live Paper Trading Tracker Card */}
          <div style={{ background: 'var(--bg-secondary)', padding: '16px', borderRadius: '14px', border: '1px solid var(--border-color)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
              <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#fff', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Clock size={16} color="var(--up-green)" /> LIVE PAPER TRADING TRACKER
              </span>
              <span style={{ fontSize: '0.68rem', color: 'var(--accent-cyan)', fontWeight: 600 }}>LIVE FORWARD TEST</span>
            </div>

            {paperPerf ? (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', fontSize: '0.8rem' }}>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Total Logged: </span>
                  <strong style={{ color: '#fff' }}>{paperPerf.total_predictions}</strong>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Resolved Setups: </span>
                  <strong style={{ color: '#fff' }}>{paperPerf.resolved_predictions}</strong>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Paper Win Rate: </span>
                  <strong style={{ color: 'var(--up-green)' }}>
                    {paperPerf.resolved_predictions > 0 ? `${paperPerf.win_rate_pct}%` : 'INSUFFICIENT SAMPLE'}
                  </strong>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Accuracy: </span>
                  <strong style={{ color: 'var(--accent-cyan)' }}>
                    {paperPerf.resolved_predictions > 0 ? `${paperPerf.accuracy_pct}%` : 'PENDING SETTLEMENT'}
                  </strong>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Avg Realized Return: </span>
                  <strong style={{ color: paperPerf.average_return_pct >= 0 ? 'var(--up-green)' : 'var(--down-red)' }}>
                    {paperPerf.average_return_pct}%
                  </strong>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Pending Settlement: </span>
                  <strong style={{ color: 'var(--risk-medium)' }}>{paperPerf.pending_predictions}</strong>
                </div>
              </div>
            ) : (
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Paper performance statistics loading...</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
