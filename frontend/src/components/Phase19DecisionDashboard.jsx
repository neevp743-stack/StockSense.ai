import React, { useState, useEffect } from 'react';
import { api } from '../api';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar
} from 'recharts';

export default function Phase19DecisionDashboard() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statusData, setStatusData] = useState(null);
  const [summaryData, setSummaryData] = useState(null);
  const [scorecardData, setScorecardData] = useState(null);
  const [regimesData, setRegimesData] = useState(null);
  const [calibrationData, setCalibrationData] = useState(null);
  const [tradesData, setTradesData] = useState(null);
  const [statData, setStatData] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [resStatus, resSummary, resScorecard, resRegimes, resCalib, resTrades, resStat] = await Promise.all([
        api.getPhase19Status(),
        api.getPhase19Summary(),
        api.getPhase19PromotionReadiness(),
        api.getPhase19Regimes(),
        api.getPhase19Calibration(),
        api.getPhase19Trades(),
        api.getPhase19Statistics()
      ]);

      setStatusData(resStatus.data);
      setSummaryData(resSummary.data.summary);
      setScorecardData(resScorecard.data.promotion_readiness);
      setRegimesData(resRegimes.data.regimes);
      setCalibrationData(resCalib.data.calibration);
      setTradesData(resTrades.data.trades);
      setStatData(resStat.data.statistics);
    } catch (err) {
      console.error("Error fetching Phase 19 decision data:", err);
      setError("Failed to load Phase 19 Decision Dashboard data.");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: '#888' }}>
        <h3>Loading Phase 19 Forward Decision Dashboard...</h3>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: '#ff4d4f' }}>
        <h3>{error}</h3>
        <button onClick={fetchData} style={{ marginTop: '1rem', padding: '0.5rem 1rem', cursor: 'pointer' }}>Retry</button>
      </div>
    );
  }

  const sampleSize = summaryData?.total_observations || 0;
  const champAcc = summaryData?.cumulative_summary?.champion?.accuracy;
  const challAcc = summaryData?.cumulative_summary?.challenger?.accuracy;
  const accDelta = summaryData?.cumulative_summary?.comparison?.accuracy_delta;

  const getStatusBadge = (status) => {
    switch (status) {
      case 'PASSED':
        return <span style={{ color: '#52c41a', fontWeight: 'bold' }}>🟢 PASSED</span>;
      case 'INSUFFICIENT':
        return <span style={{ color: '#faad14', fontWeight: 'bold' }}>🟡 INSUFFICIENT</span>;
      case 'INCONCLUSIVE':
        return <span style={{ color: '#fa8c16', fontWeight: 'bold' }}>🟠 INCONCLUSIVE</span>;
      case 'FAILED':
        return <span style={{ color: '#ff4d4f', fontWeight: 'bold' }}>🔴 FAILED</span>;
      default:
        return <span>{status}</span>;
    }
  };

  return (
    <div style={{ padding: '1.5rem', background: '#0a0e17', color: '#e6f7ff', borderRadius: '8px', fontFamily: 'Inter, sans-serif' }}>
      {/* Top Banner */}
      <div style={{ borderBottom: '1px solid #1f293d', paddingBottom: '1rem', marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <span style={{ background: '#177ddc', color: '#fff', padding: '0.2rem 0.6rem', borderRadius: '4px', fontSize: '0.8rem', fontWeight: 'bold' }}>
              RESEARCH / CHAMPION vs CHALLENGER
            </span>
            <h2 style={{ margin: '0.5rem 0 0.2rem 0', color: '#fff' }}>StockSense AI — Phase 19 Forward Decision Support Dashboard</h2>
            <p style={{ margin: 0, color: '#8c8c8c', fontSize: '0.9rem' }}>
              Empirical Champion (Phase 12) vs Challenger (Phase 17) Validation on Live Market Data
            </p>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.85rem', color: '#8c8c8c' }}>Production Model</div>
            <div style={{ fontWeight: 'bold', color: '#52c41a' }}>XGBoost v1.0 Calibrated</div>
            <div style={{ fontSize: '0.85rem', color: '#ff4d4f', marginTop: '0.2rem' }}>Promotion: NOT AUTOMATIC</div>
          </div>
        </div>
      </div>

      {/* Overview Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
        <div style={{ background: '#141c2e', padding: '1rem', borderRadius: '6px', border: '1px solid #1f293d' }}>
          <div style={{ color: '#8c8c8c', fontSize: '0.85rem' }}>Forward Observations</div>
          <div style={{ fontSize: '1.6rem', fontWeight: 'bold', margin: '0.3rem 0' }}>{sampleSize}</div>
          <div style={{ fontSize: '0.75rem', color: '#52c41a' }}>Resolved Paired Ticks</div>
        </div>

        <div style={{ background: '#141c2e', padding: '1rem', borderRadius: '6px', border: '1px solid #1f293d' }}>
          <div style={{ color: '#8c8c8c', fontSize: '0.85rem' }}>Champion Accuracy (Phase 12)</div>
          <div style={{ fontSize: '1.6rem', fontWeight: 'bold', color: '#1890ff', margin: '0.3rem 0' }}>
            {champAcc !== null && champAcc !== undefined ? `${(champAcc * 100).toFixed(2)}%` : 'Insufficient Data'}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#8c8c8c' }}>Production Baseline</div>
        </div>

        <div style={{ background: '#141c2e', padding: '1rem', borderRadius: '6px', border: '1px solid #1f293d' }}>
          <div style={{ color: '#8c8c8c', fontSize: '0.85rem' }}>Challenger Accuracy (Phase 17)</div>
          <div style={{ fontSize: '1.6rem', fontWeight: 'bold', color: '#722ed1', margin: '0.3rem 0' }}>
            {challAcc !== null && challAcc !== undefined ? `${(challAcc * 100).toFixed(2)}%` : 'Insufficient Data'}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#8c8c8c' }}>Shadow Challenger</div>
        </div>

        <div style={{ background: '#141c2e', padding: '1rem', borderRadius: '6px', border: '1px solid #1f293d' }}>
          <div style={{ color: '#8c8c8c', fontSize: '0.85rem' }}>Accuracy Difference</div>
          <div style={{ fontSize: '1.6rem', fontWeight: 'bold', color: accDelta > 0 ? '#52c41a' : (accDelta < 0 ? '#ff4d4f' : '#faad14'), margin: '0.3rem 0' }}>
            {accDelta !== null && accDelta !== undefined ? `${accDelta > 0 ? '+' : ''}${(accDelta * 100).toFixed(2)}%` : 'N/A'}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#8c8c8c' }}>Challenger Delta</div>
        </div>
      </div>

      {/* Decision Status Verdict Card */}
      <div style={{ background: '#141c2e', padding: '1.2rem', borderRadius: '6px', border: '1px solid #1f293d', marginBottom: '1.5rem' }}>
        <h3 style={{ margin: '0 0 0.5rem 0', color: '#fff' }}>Official Phase 19 Decision Verdict</h3>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ fontSize: '1.4rem', fontWeight: 'bold', color: scorecardData?.final_verdict === 'PHASE19_CHALLENGER_READY_FOR_EXPERT_REVIEW' ? '#52c41a' : '#faad14' }}>
            {scorecardData?.final_verdict || 'PHASE19_INSUFFICIENT_FORWARD_DATA'}
          </div>
        </div>
        <p style={{ margin: '0.5rem 0 0 0', color: '#bfbfbf', fontSize: '0.9rem' }}>
          {scorecardData?.verdict_explanation || 'Insufficient genuine forward observations. Phase 12 remains production.'}
        </p>
      </div>

      {/* 12-Point Promotion Readiness Scorecard Table */}
      <div style={{ background: '#141c2e', padding: '1.2rem', borderRadius: '6px', border: '1px solid #1f293d', marginBottom: '1.5rem' }}>
        <h3 style={{ margin: '0 0 1rem 0', color: '#fff' }}>12-Point Promotion Readiness Scorecard</h3>
        {scorecardData?.scorecard ? (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #1f293d', textAlign: 'left', color: '#8c8c8c' }}>
                <th style={{ padding: '0.5rem' }}>Criterion</th>
                <th style={{ padding: '0.5rem' }}>Status</th>
                <th style={{ padding: '0.5rem' }}>Details</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(scorecardData.scorecard).map(([key, item]) => (
                <tr key={key} style={{ borderBottom: '1px solid #141c2e' }}>
                  <td style={{ padding: '0.5rem', fontWeight: '500' }}>{item.name}</td>
                  <td style={{ padding: '0.5rem' }}>{getStatusBadge(item.status)}</td>
                  <td style={{ padding: '0.5rem', color: '#bfbfbf' }}>{item.details || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div style={{ color: '#8c8c8c' }}>Scorecard data unavailable.</div>
        )}
      </div>

      {/* Cumulative Accuracy Time Series Chart */}
      {summaryData?.time_series && summaryData.time_series.length > 0 && (
        <div style={{ background: '#141c2e', padding: '1.2rem', borderRadius: '6px', border: '1px solid #1f293d', marginBottom: '1.5rem' }}>
          <h3 style={{ margin: '0 0 1rem 0', color: '#fff' }}>Cumulative Forward Accuracy Time-Series</h3>
          <div style={{ width: '100%', height: 300 }}>
            <ResponsiveContainer>
              <LineChart data={summaryData.time_series}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f293d" />
                <XAxis dataKey="date" stroke="#8c8c8c" />
                <YAxis stroke="#8c8c8c" domain={[0, 1]} />
                <Tooltip contentStyle={{ background: '#0a0e17', borderColor: '#1f293d' }} />
                <Legend />
                <Line type="monotone" dataKey="champion_accuracy" name="Champion (Phase 12)" stroke="#1890ff" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="challenger_accuracy" name="Challenger (Phase 17)" stroke="#722ed1" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}
