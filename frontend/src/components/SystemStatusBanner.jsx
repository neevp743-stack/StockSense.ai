import React, { useEffect, useState } from 'react';
import { api } from '../api';
import { Server, Database, Radio, Cpu, ShieldCheck } from 'lucide-react';

export function SystemStatusBanner() {
  const [status, setStatus] = useState({
    backend: 'ONLINE',
    database: 'CONNECTED',
    realtime_provider: 'FINNHUB',
    realtime_status: 'LIVE',
    model: 'XGBoost v1.0'
  });

  useEffect(() => {
    api.getSystemStatus()
      .then(res => {
        if (res?.data) {
          setStatus(res.data);
        }
      })
      .catch(err => {
        console.error("SystemStatusBanner API Error:", err);
        setStatus(prev => ({
          ...prev,
          backend: 'OFFLINE'
        }));
      });
  }, []);


  const rtBadgeStyle = 
    status.realtime_status === "LIVE" ? { color: "var(--up-green)", label: "🟢 LIVE" } :
    status.realtime_status === "RECONNECTING" ? { color: "#f97316", label: "🟠 RECONNECTING" } :
    { color: "#f59e0b", label: "🟡 DELAYED QUOTES" };

  return (
    <div style={{
      background: 'var(--bg-secondary)', padding: '10px 16px', borderRadius: '12px',
      border: '1px solid var(--border-color)', marginBottom: '16px',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px',
      fontSize: '0.8rem'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-muted)' }}>
        <ShieldCheck size={16} color="var(--accent-cyan)" /> <strong>System Status:</strong>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '20px', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Server size={14} color="var(--text-muted)" /> Backend: <strong style={{ color: status.backend === 'ONLINE' ? 'var(--up-green)' : 'var(--down-red)' }}>{status.backend === 'ONLINE' ? '🟢 ONLINE' : '🔴 OFFLINE'}</strong>
        </div>


        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Database size={14} color="var(--text-muted)" /> Database: <strong style={{ color: 'var(--up-green)' }}>🟢 {status.database}</strong>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Radio size={14} color="var(--text-muted)" /> Market Data ({status.realtime_provider}): <strong style={{ color: rtBadgeStyle.color }}>{rtBadgeStyle.label}</strong>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Cpu size={14} color="var(--text-muted)" /> AI Model: <strong style={{ color: 'var(--accent-cyan)' }}>🟢 {status.model}</strong>
        </div>
      </div>
    </div>
  );
}
