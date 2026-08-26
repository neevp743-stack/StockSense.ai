import React, { useState, useEffect } from 'react';
import { api } from '../api';
import { Server, Database, Radio, Cpu, ShieldCheck, RefreshCw, BarChart2, Activity, Cpu as CpuIcon } from 'lucide-react';

// Import the relocated diagnostics monitors
import { ProductionMonitor } from './ProductionMonitor';
import { Phase18ShadowMonitor } from './Phase18ShadowMonitor';
import { Phase19AMonitor } from './Phase19AMonitor';
import Phase19DecisionDashboard from './Phase19DecisionDashboard';
import Phase20ResearchDashboard from './Phase20ResearchDashboard';

export function AdminDiagnosticsPage({ symbol = 'RELIANCE' }) {
  const [diagnostics, setDiagnostics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeSubTab, setActiveSubTab] = useState('system-health'); // system-health, production-metrics, shadow-validation, model-research

  useEffect(() => {
    fetchDiagnostics();
    const interval = setInterval(fetchDiagnostics, 10000); // Poll diagnostics every 10s
    return () => clearInterval(interval);
  }, []);

  const fetchDiagnostics = async () => {
    try {
      const res = await api.getAdminDiagnostics();
      setDiagnostics(res.data?.data || res.data);
    } catch (err) {
      console.error("Failed to load admin diagnostics:", err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-secondary)' }}>
        <RefreshCw size={32} color="var(--accent-cyan)" className="spin" style={{ marginBottom: '12px' }} />
        <h3>Loading System Diagnostic Panel...</h3>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Title */}
      <div>
        <h2 style={{ fontSize: '1.8rem', fontWeight: 800, margin: 0, color: '#fff', display: 'flex', alignItems: 'center', gap: '10px' }} className="heading-font">
          <ShieldCheck size={28} color="var(--risk-high)" /> Admin Diagnostics Console
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '4px' }}>
          Real-time server operational metrics, websocket connections, cache latency, model validation, and shadow pipelines.
        </p>
      </div>

      {/* Diagnostics Sub-Navigation */}
      <div style={subNavBarStyle}>
        {[
          { id: 'system-health', label: '🖥️ System Health & API' },
          { id: 'production-metrics', label: '📊 Production Monitor' },
          { id: 'shadow-validation', label: '⚡ Shadow Pipelines' },
          { id: 'model-research', label: '🔬 Model Research' }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveSubTab(tab.id)}
            style={{
              ...subTabButtonStyle,
              borderColor: activeSubTab === tab.id ? 'var(--accent-cyan)' : 'transparent',
              color: activeSubTab === tab.id ? 'var(--accent-cyan)' : 'var(--text-secondary)',
              backgroundColor: activeSubTab === tab.id ? 'rgba(0, 242, 254, 0.08)' : 'transparent'
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* SUB-TAB 1: SYSTEM HEALTH */}
      {activeSubTab === 'system-health' && diagnostics && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Main Telemetry Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
            <div className="glass-card" style={statCardStyle}>
              <Server size={20} color="var(--accent-cyan)" />
              <div>
                <div style={statLabelStyle}>Backend Process</div>
                <strong style={{ fontSize: '1.2rem', color: 'var(--up-green)' }}>{diagnostics.backend_status}</strong>
                <div style={statSubLabelStyle}>Env: {diagnostics.environment}</div>
              </div>
            </div>

            <div className="glass-card" style={statCardStyle}>
              <Database size={20} color="var(--accent-cyan)" />
              <div>
                <div style={statLabelStyle}>SQLite Database</div>
                <strong style={{ fontSize: '1.2rem', color: 'var(--up-green)' }}>{diagnostics.database_status}</strong>
                <div style={statSubLabelStyle}>Pool Active</div>
              </div>
            </div>

            <div className="glass-card" style={statCardStyle}>
              <CpuIcon size={20} color="var(--accent-cyan)" />
              <div>
                <div style={statLabelStyle}>Memory RSS Footprint</div>
                <strong style={{ fontSize: '1.2rem', color: '#fff' }} className="mono-font">
                  {diagnostics.memory_rss_mb} MB
                </strong>
                <div style={statSubLabelStyle}>Peak Heap Segment</div>
              </div>
            </div>

            <div className="glass-card" style={statCardStyle}>
              <ShieldCheck size={20} color="var(--up-green)" />
              <div>
                <div style={statLabelStyle}>Model Integrity Check</div>
                <strong style={{ fontSize: '1.2rem', color: diagnostics.model_integrity?.all_compatible ? 'var(--up-green)' : 'var(--down-red)' }}>
                  {diagnostics.model_integrity?.all_compatible ? '100% INVARIANT' : 'INTEGRITY ERROR'}
                </strong>
                <div style={statSubLabelStyle}>{diagnostics.model_integrity?.total_models}/128 Hashes Checked</div>
              </div>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '20px' }}>
            
            {/* Coinbase WebSocket Telemetry */}
            <div className="glass-card" style={{ padding: '20px' }}>
              <h3 className="heading-font" style={cardTitleStyle}>
                <Radio size={16} color="var(--accent-cyan)" /> Coinbase WS Stream Telemetry
              </h3>
              {diagnostics.coinbase_websocket ? (
                <div style={diagListStyle}>
                  <div style={diagRowStyle}>
                    <span>Connection Status</span>
                    <strong style={{ color: diagnostics.coinbase_websocket.connected ? 'var(--up-green)' : 'var(--down-red)' }}>
                      {diagnostics.coinbase_websocket.connected ? 'CONNECTED' : 'DISCONNECTED'}
                    </strong>
                  </div>
                  <div style={diagRowStyle}>
                    <span>Reconnect Cycles</span>
                    <span className="mono-font">{diagnostics.coinbase_websocket.reconnect_count}</span>
                  </div>
                  <div style={diagRowStyle}>
                    <span>Incoming Tick Count</span>
                    <span className="mono-font">{diagnostics.coinbase_websocket.tick_count}</span>
                  </div>
                  <div style={diagRowStyle}>
                    <span>Candles Computed</span>
                    <span className="mono-font">{diagnostics.coinbase_websocket.candle_count}</span>
                  </div>
                  <div style={diagRowStyle}>
                    <span>Heartbeats Received</span>
                    <span className="mono-font">{diagnostics.coinbase_websocket.heartbeat_count}</span>
                  </div>
                  <div style={diagRowStyle}>
                    <span>Total Exceptions Logged</span>
                    <span className="mono-font" style={{ color: diagnostics.coinbase_websocket.error_count > 0 ? 'var(--down-red)' : 'var(--text-secondary)' }}>
                      {diagnostics.coinbase_websocket.error_count}
                    </span>
                  </div>
                  {diagnostics.coinbase_websocket.last_error && (
                    <div style={{ ...diagRowStyle, flexDirection: 'column', alignItems: 'flex-start', border: 'none', gap: '4px' }}>
                      <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Last Exception Trace:</span>
                      <code style={{ fontSize: '0.74rem', color: 'var(--down-red)', wordBreak: 'break-all' }}>{diagnostics.coinbase_websocket.last_error}</code>
                    </div>
                  )}
                </div>
              ) : (
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Coinbase WebSocket Provider Not Loaded.</div>
              )}
            </div>

            {/* Twelve Data REST Telemetry */}
            <div className="glass-card" style={{ padding: '20px' }}>
              <h3 className="heading-font" style={cardTitleStyle}>
                <Server size={16} color="var(--accent-cyan)" /> Twelve Data API Telemetry
              </h3>
              {diagnostics.twelve_data_rest ? (
                <div style={diagListStyle}>
                  <div style={diagRowStyle}>
                    <span>API Config Status</span>
                    <strong style={{ color: diagnostics.twelve_data_rest.is_configured ? 'var(--up-green)' : 'var(--risk-medium)' }}>
                      {diagnostics.twelve_data_rest.is_configured ? 'CONFIGURED' : 'MISSING_API_KEY'}
                    </strong>
                  </div>
                  <div style={diagRowStyle}>
                    <span>Total API Calls</span>
                    <span className="mono-font">{diagnostics.twelve_data_rest.request_count}</span>
                  </div>
                  <div style={diagRowStyle}>
                    <span>Failed Requests</span>
                    <span className="mono-font" style={{ color: diagnostics.twelve_data_rest.failed_request_count > 0 ? 'var(--down-red)' : 'var(--text-secondary)' }}>
                      {diagnostics.twelve_data_rest.failed_request_count}
                    </span>
                  </div>
                  <div style={diagRowStyle}>
                    <span>Rate Limits Hit (HTTP 429)</span>
                    <span className="mono-font" style={{ color: diagnostics.twelve_data_rest.rate_limit_count > 0 ? 'var(--down-red)' : 'var(--text-secondary)' }}>
                      {diagnostics.twelve_data_rest.rate_limit_count}
                    </span>
                  </div>
                  <div style={diagRowStyle}>
                    <span>Average API Latency</span>
                    <span className="mono-font" style={{ color: 'var(--accent-cyan)' }}>{diagnostics.twelve_data_rest.average_latency_ms} ms</span>
                  </div>
                  <div style={diagRowStyle}>
                    <span>Last Successful Sync</span>
                    <span style={{ fontSize: '0.74rem' }}>{diagnostics.twelve_data_rest.last_success_ts || 'N/A'}</span>
                  </div>
                </div>
              ) : (
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Twelve Data Provider Not Loaded.</div>
              )}
            </div>

          </div>
        </div>
      )}

      {/* SUB-TAB 2: PRODUCTION METRICS */}
      {activeSubTab === 'production-metrics' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <ProductionMonitor symbol={symbol} />
          <Phase19DecisionDashboard />
        </div>
      )}

      {/* SUB-TAB 3: SHADOW VALIDATION */}
      {activeSubTab === 'shadow-validation' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <Phase18ShadowMonitor symbol={symbol} />
          <Phase19AMonitor symbol={symbol} />
        </div>
      )}

      {/* SUB-TAB 4: MODEL RESEARCH */}
      {activeSubTab === 'model-research' && (
        <Phase20ResearchDashboard />
      )}

    </div>
  );
}

// Styling Constants
const subNavBarStyle = {
  display: 'flex',
  gap: '8px',
  background: 'var(--bg-secondary)',
  padding: '6px',
  borderRadius: '12px',
  border: '1px solid var(--border-color)',
  overflowX: 'auto',
  scrollbarWidth: 'none'
};

const subTabButtonStyle = {
  padding: '8px 16px',
  fontSize: '0.82rem',
  fontWeight: 700,
  borderRadius: '8px',
  border: '1px solid transparent',
  cursor: 'pointer',
  whiteSpace: 'nowrap',
  transition: 'border-color 0.2s, background-color 0.2s'
};

const statCardStyle = {
  display: 'flex',
  alignItems: 'center',
  gap: '16px',
  padding: '16px 20px',
  borderRadius: '14px',
  border: '1px solid var(--border-color)'
};

const statLabelStyle = {
  fontSize: '0.7rem',
  fontWeight: 700,
  color: 'var(--text-secondary)',
  textTransform: 'uppercase',
  letterSpacing: '0.04em'
};

const statSubLabelStyle = {
  fontSize: '0.68rem',
  color: 'var(--text-muted)',
  marginTop: '2px'
};

const cardTitleStyle = {
  fontSize: '1rem',
  fontWeight: 800,
  color: '#fff',
  margin: '0 0 16px 0',
  display: 'flex',
  alignItems: 'center',
  gap: '8px'
};

const diagListStyle = {
  display: 'flex',
  flexDirection: 'column',
  gap: '12px'
};

const diagRowStyle = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  fontSize: '0.8rem',
  paddingBottom: '8px',
  borderBottom: '1px solid var(--border-subtle)'
};
