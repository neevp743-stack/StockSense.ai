import React, { useState } from 'react';
import { 
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, Legend 
} from 'recharts';
import { Play, Sliders, AlertTriangle } from 'lucide-react';
import { api } from '../api';

export function BacktesterUI({ symbol }) {
  const [params, setParams] = useState({
    capital: 100000,
    threshold: 0.55,
    allowShort: false,
    cost: 0.001,
    slippage: 0.0005
  });

  const [loading, setLoading] = useState(false);
  const [backtestResult, setBacktestResult] = useState(null);

  const handleRunBacktest = async () => {
    setLoading(true);
    try {
      const res = await api.runBacktest({
        symbol,
        initial_capital: parseFloat(params.capital),
        prob_threshold: parseFloat(params.threshold),
        allow_short: params.allowShort,
        transaction_cost: parseFloat(params.cost),
        slippage: parseFloat(params.slippage)
      });
      setBacktestResult(res.data.results);
    } catch (err) {
      console.error("Backtest failed:", err);
    } finally {
      setLoading(false);
    }
  };

  const aiStats = backtestResult?.ai_strategy;
  const bhStats = backtestResult?.buy_and_hold;

  return (
    <div className="glass-card" style={{ marginBottom: '24px' }}>
      {/* Header with Out of Sample Badge */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h3 className="heading-font" style={{ fontSize: '1.2rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Sliders size={20} color="var(--accent-cyan)" />
              Research Backtesting Simulator — {symbol}
            </h3>
            <span style={{ background: 'rgba(0, 242, 254, 0.12)', color: 'var(--accent-cyan)', border: '1px solid rgba(0, 242, 254, 0.3)', padding: '2px 8px', borderRadius: '10px', fontSize: '0.7rem', fontWeight: 700 }}>
              [STRICT OUT-OF-SAMPLE / HELD-OUT TEST SET EVALUATION]
            </span>
          </div>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
            Evaluates AI Long/Cash Strategy strictly on the held-out 15% out-of-sample test set (179 trading days). In-sample data is excluded.
          </p>
        </div>

        <button 
          className="btn-primary" 
          onClick={handleRunBacktest}
          disabled={loading}
        >
          <Play size={16} />
          {loading ? 'Simulating Out-of-Sample...' : 'Run Out-of-Sample Backtest'}
        </button>
      </div>

      {/* Strategy Parameters Panel */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px', background: 'var(--bg-secondary)', padding: '16px', borderRadius: '12px', marginBottom: '20px' }}>
        <div>
          <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
            Initial Capital (₹)
          </label>
          <input 
            type="number"
            value={params.capital}
            onChange={e => setParams(p => ({ ...p, capital: e.target.value }))}
            style={{ width: '100%', background: '#0a0d14', color: '#fff', border: '1px solid var(--border-color)', padding: '6px 10px', borderRadius: '8px', fontSize: '0.85rem' }}
          />
        </div>

        <div>
          <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
            Probability Threshold
          </label>
          <input 
            type="number"
            step="0.01"
            min="0.50"
            max="0.90"
            value={params.threshold}
            onChange={e => setParams(p => ({ ...p, threshold: e.target.value }))}
            style={{ width: '100%', background: '#0a0d14', color: '#fff', border: '1px solid var(--border-color)', padding: '6px 10px', borderRadius: '8px', fontSize: '0.85rem' }}
          />
        </div>

        <div>
          <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
            Transaction Cost per Trade
          </label>
          <input 
            type="number"
            step="0.0005"
            value={params.cost}
            onChange={e => setParams(p => ({ ...p, cost: e.target.value }))}
            style={{ width: '100%', background: '#0a0d14', color: '#fff', border: '1px solid var(--border-color)', padding: '6px 10px', borderRadius: '8px', fontSize: '0.85rem' }}
          />
        </div>

        <div>
          <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
            Slippage % per Trade
          </label>
          <input 
            type="number"
            step="0.0001"
            value={params.slippage}
            onChange={e => setParams(p => ({ ...p, slippage: e.target.value }))}
            style={{ width: '100%', background: '#0a0d14', color: '#fff', border: '1px solid var(--border-color)', padding: '6px 10px', borderRadius: '8px', fontSize: '0.85rem' }}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '16px' }}>
          <input 
            type="checkbox"
            id="allowShort"
            checked={params.allowShort}
            onChange={e => setParams(p => ({ ...p, allowShort: e.target.checked }))}
          />
          <label htmlFor="allowShort" style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            Allow Shorting (Research Mode)
          </label>
        </div>
      </div>

      {/* Backtest Results Dashboard */}
      {backtestResult && (
        <div>
          {/* Key Metrics Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px', marginBottom: '20px' }}>
            <div style={{ background: 'var(--bg-secondary)', padding: '12px', borderRadius: '12px', borderLeft: '4px solid var(--accent-cyan)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>AI Out-of-Sample Return</div>
              <div className="mono-font" style={{ fontSize: '1.25rem', fontWeight: 700, color: aiStats.total_return_pct >= 0 ? 'var(--up-green)' : 'var(--down-red)' }}>
                {aiStats.total_return_pct.toFixed(2)}%
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>CAGR: {aiStats.cagr_pct.toFixed(2)}%</div>
            </div>

            <div style={{ background: 'var(--bg-secondary)', padding: '12px', borderRadius: '12px', borderLeft: '4px solid #f59e0b' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Buy & Hold Return</div>
              <div className="mono-font" style={{ fontSize: '1.25rem', fontWeight: 700, color: bhStats.total_return_pct >= 0 ? 'var(--up-green)' : 'var(--down-red)' }}>
                {bhStats.total_return_pct.toFixed(2)}%
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>CAGR: {bhStats.cagr_pct.toFixed(2)}%</div>
            </div>

            <div style={{ background: 'var(--bg-secondary)', padding: '12px', borderRadius: '12px', borderLeft: '4px solid var(--accent-blue)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Sharpe Ratio</div>
              <div className="mono-font" style={{ fontSize: '1.25rem', fontWeight: 700 }}>
                {aiStats.sharpe_ratio.toFixed(2)}
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Buy & Hold: {bhStats.sharpe_ratio.toFixed(2)}</div>
            </div>

            <div style={{ background: 'var(--bg-secondary)', padding: '12px', borderRadius: '12px', borderLeft: '4px solid var(--risk-high)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Max Drawdown</div>
              <div className="mono-font" style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--down-red)' }}>
                {aiStats.max_drawdown_pct.toFixed(2)}%
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Buy & Hold: {bhStats.max_drawdown_pct.toFixed(2)}%</div>
            </div>

            <div style={{ background: 'var(--bg-secondary)', padding: '12px', borderRadius: '12px', borderLeft: '4px solid var(--up-green)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Executed Trades & Win Rate</div>
              <div className="mono-font" style={{ fontSize: '1.25rem', fontWeight: 700 }}>
                {aiStats.win_rate_pct.toFixed(1)}%
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Total Trades: {aiStats.trade_count}</div>
            </div>
          </div>

          {/* Equity Curves Chart */}
          <div style={{ height: '300px', width: '100%', marginBottom: '16px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={backtestResult.equity_curve} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                <XAxis dataKey="date" stroke="var(--text-muted)" fontSize={11} tickLine={false} />
                <YAxis domain={['auto', 'auto']} stroke="var(--text-muted)" fontSize={11} tickFormatter={v => `₹${v}`} />
                <Tooltip contentStyle={{ background: '#121824', borderColor: 'var(--border-color)', borderRadius: '8px', color: '#fff' }} />
                <Legend />
                <Line type="monotone" dataKey="ai_strategy" stroke="#00f2fe" strokeWidth={2} dot={false} name="AI Strategy Portfolio (Out-of-Sample)" />
                <Line type="monotone" dataKey="buy_and_hold" stroke="#f59e0b" strokeWidth={1.5} strokeDasharray="3 3" dot={false} name="Buy & Hold Baseline" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Academic Profitability Warning Note */}
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', lineHeight: '1.4', background: 'rgba(239, 68, 68, 0.08)', border: '1px solid rgba(239, 68, 68, 0.2)', padding: '12px 16px', borderRadius: '10px', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <AlertTriangle size={18} color="var(--down-red)" style={{ flexShrink: 0 }} />
            <div>
              <strong>ACADEMIC PROFITABILITY NOTE:</strong> Current backtest results on the out-of-sample test set do <strong>NOT</strong> demonstrate reliable financial profitability. Directional probability predictions in financial markets contain high statistical noise.
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
