import React, { useEffect, useState } from 'react';
import { api } from '../api';
import { Shield, Eye, Activity, CheckCircle, AlertTriangle, Scale, TrendingUp, Info } from 'lucide-react';

export function Phase18ShadowMonitor({ symbol = 'RELIANCE' }) {
  const [status, setStatus] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [trades, setTrades] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const controller = new AbortController();
    const opts = { signal: controller.signal };

    Promise.all([
      api.getPhase18Status(opts).catch(() => null),
      api.getPhase18Comparison(symbol, opts).catch(() => null),
      api.getPhase18Trades(opts).catch(() => null),
      api.getPhase18Statistics(opts).catch(() => null)
    ]).then(([sRes, cRes, tRes, stRes]) => {
      if (controller.signal.aborted) return;
      if (sRes?.data) setStatus(sRes.data);
      if (cRes?.data) setComparison(cRes.data);
      if (tRes?.data) setTrades(tRes.data);
      if (stRes?.data) setStats(stRes.data);
      setLoading(false);
    }).catch(() => {
      if (!controller.signal.aborted) setLoading(false);
    });

    return () => controller.abort();
  }, [symbol]);

  const promoStatus = status?.promotion_status || 'PHASE18_INSUFFICIENT_FORWARD_DATA';
  const isInsufficient = promoStatus === 'PHASE18_INSUFFICIENT_FORWARD_DATA';
  const totalObs = status?.total_observations ?? 0;
  const pairedResolved = status?.paired_resolved_samples ?? 0;

  const compData = comparison?.summary || {};
  const champAcc = compData?.champion?.accuracy;
  const challAcc = compData?.challenger?.accuracy;

  const champBrier = compData?.champion?.brier_score;
  const challBrier = compData?.challenger?.brier_score;

  const pValue = stats?.mcnemar?.p_value;
  const isSig = stats?.statistically_significant;

  return (
    <div style={{
      background: 'var(--card-bg, #1e293b)',
      borderRadius: '12px',
      padding: '20px',
      border: '1px solid var(--border-color, #334155)',
      marginTop: '20px',
      color: '#f8fafc'
    }}>
      {/* Top Banner */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '16px',
        paddingBottom: '12px',
        borderBottom: '1px solid rgba(255,255,255,0.1)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Eye size={22} style={{ color: '#38bdf8' }} />
          <div>
            <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 600 }}>Phase 18 Shadow Forward Validation</h3>
            <p style={{ margin: 0, fontSize: '0.8rem', color: '#94a3b8' }}>
              Independent Champion/Challenger Forward Performance Comparison
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{
            background: 'rgba(56, 189, 248, 0.15)',
            color: '#38bdf8',
            padding: '4px 10px',
            borderRadius: '20px',
            fontSize: '0.75rem',
            fontWeight: 700,
            letterSpacing: '0.5px'
          }}>
            RESEARCH / SHADOW MODE
          </span>
          <span style={{
            background: isInsufficient ? 'rgba(234, 179, 8, 0.15)' : 'rgba(34, 197, 94, 0.15)',
            color: isInsufficient ? '#eab308' : '#22c55e',
            padding: '4px 10px',
            borderRadius: '20px',
            fontSize: '0.75rem',
            fontWeight: 600
          }}>
            {promoStatus}
          </span>
        </div>
      </div>

      {/* Model Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: '16px',
        marginBottom: '20px'
      }}>
        {/* Champion Model Card */}
        <div style={{
          background: 'rgba(15, 23, 42, 0.6)',
          padding: '16px',
          borderRadius: '8px',
          borderLeft: '4px solid #38bdf8'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.8rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Official Production Champion</span>
            <Shield size={16} style={{ color: '#38bdf8' }} />
          </div>
          <div style={{ fontSize: '1rem', fontWeight: 700, color: '#f8fafc' }}>Phase 12 Calibrated XGBoost v1.0</div>
          <div style={{ marginTop: '12px', fontSize: '0.85rem', color: '#cbd5e1' }}>
            <div>Accuracy: <strong>{champAcc != null ? `${(champAcc * 100).toFixed(1)}%` : (isInsufficient ? "Insufficient live data" : "N/A")}</strong></div>
            <div>Brier Score: <strong>{champBrier != null ? champBrier.toFixed(4) : "N/A"}</strong></div>
          </div>
        </div>

        {/* Challenger Model Card */}
        <div style={{
          background: 'rgba(15, 23, 42, 0.6)',
          padding: '16px',
          borderRadius: '8px',
          borderLeft: '4px solid #a855f7'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.8rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Shadow Challenger</span>
            <Eye size={16} style={{ color: '#a855f7' }} />
          </div>
          <div style={{ fontSize: '1rem', fontWeight: 700, color: '#f8fafc' }}>Phase 17 Large XGBoost</div>
          <div style={{ marginTop: '12px', fontSize: '0.85rem', color: '#cbd5e1' }}>
            <div>Accuracy: <strong>{challAcc != null ? `${(challAcc * 100).toFixed(1)}%` : (isInsufficient ? "Insufficient live data" : "N/A")}</strong></div>
            <div>Brier Score: <strong>{challBrier != null ? challBrier.toFixed(4) : "N/A"}</strong></div>
          </div>
        </div>
      </div>

      {/* Statistical & Resolution Details */}
      <div style={{
        background: 'rgba(15, 23, 42, 0.4)',
        padding: '14px',
        borderRadius: '8px',
        fontSize: '0.85rem',
        color: '#94a3b8',
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: 'space-between',
        gap: '12px'
      }}>
        <div>Total Observations: <strong style={{ color: '#f8fafc' }}>{totalObs}</strong></div>
        <div>Paired Resolved Samples: <strong style={{ color: '#f8fafc' }}>{pairedResolved}</strong></div>
        <div>McNemar p-value: <strong style={{ color: '#f8fafc' }}>{pValue != null ? pValue.toFixed(4) : "N/A"}</strong></div>
        <div>Statistically Significant: <strong style={{ color: isSig ? '#22c55e' : '#f97316' }}>{isSig ? "YES (p < 0.05)" : "NO"}</strong></div>
      </div>

      {/* Recommendation Disclaimer */}
      <div style={{ marginTop: '14px', fontSize: '0.8rem', color: '#64748b', display: 'flex', alignItems: 'center', gap: '6px' }}>
        <Info size={14} />
        <span>{status?.recommendation || "KEEP PHASE 12 IN PRODUCTION. Shadow evaluation operating additively."}</span>
      </div>
    </div>
  );
}
