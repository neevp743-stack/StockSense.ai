import React, { useState, useEffect } from 'react';
import { api } from '../api';
import { User, Shield, AlertTriangle, CheckCircle, Bell, MessageSquare, Cpu, BarChart } from 'lucide-react';

export function SettingsPage({ userToken, onLogout }) {
  const [profile, setProfile] = useState(null);
  const [preferences, setPreferences] = useState(null);
  const [loading, setLoading] = useState(true);
  
  const [statusMsg, setStatusMsg] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);

  // WhatsApp verification sub-state
  const [phoneInput, setPhoneInput] = useState('');
  const [otpCode, setOtpCode] = useState('');
  const [verificationId, setVerificationId] = useState('');
  const [isVerifying, setIsVerifying] = useState(false);
  const [waStep, setWaStep] = useState('ENTER_PHONE'); // ENTER_PHONE, ENTER_CODE, VERIFIED

  useEffect(() => {
    fetchSettings();
  }, [userToken]);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const [profRes, prefRes] = await Promise.all([
        api.getUserProfile(),
        api.getUserPreferences()
      ]);
      
      const prof = profRes.data?.data || profRes.data;
      const pref = prefRes.data?.data || prefRes.data;

      setProfile(prof);
      setPreferences(pref);
      
      if (prof?.whatsapp?.phone_masked) {
        setPhoneInput(prof.whatsapp.phone_masked);
      }
      if (prof?.whatsapp?.status === 'VERIFIED') {
        setWaStep('VERIFIED');
      } else {
        setWaStep('ENTER_PHONE');
      }
    } catch (err) {
      console.error("Failed to load settings:", err);
      setErrorMsg("Failed to retrieve profile preferences from server.");
    } finally {
      setLoading(false);
    }
  };

  const handleSavePreferences = async () => {
    setStatusMsg(null);
    setErrorMsg(null);
    try {
      const res = await api.updateUserPreferences(preferences);
      setPreferences(res.data?.data || res.data);
      setStatusMsg("Preferences saved successfully.");
      setTimeout(() => setStatusMsg(null), 3000);
    } catch (err) {
      setErrorMsg("Failed to save updated preferences.");
    }
  };

  // WhatsApp alerts verification handlers
  const handleRequestWaVerify = async (e) => {
    e.preventDefault();
    setStatusMsg(null);
    setErrorMsg(null);
    if (!phoneInput.trim() || phoneInput.trim().length < 8) {
      setErrorMsg("Please enter a valid international phone number.");
      return;
    }
    setIsVerifying(true);
    try {
      const res = await api.requestWhatsAppVerify(phoneInput.trim());
      const data = res.data?.data || res.data;
      setVerificationId(data.verification_id);
      
      if (data.status === 'WHATSAPP_NOT_CONFIGURED') {
        setStatusMsg("Verification code generated! (Simulation mode: credentials not in .env). Code is active.");
      } else {
        setStatusMsg(`Verification code sent to ${phoneInput.trim()}`);
      }
      setWaStep('ENTER_CODE');
    } catch (err) {
      setErrorMsg(err.response?.data?.detail?.message || "Failed to trigger phone verification.");
    } finally {
      setIsVerifying(false);
    }
  };

  const handleConfirmWaVerify = async (e) => {
    e.preventDefault();
    setStatusMsg(null);
    setErrorMsg(null);
    if (!otpCode.trim() || otpCode.trim().length !== 6) {
      setErrorMsg("Enter the complete 6-digit OTP code.");
      return;
    }
    setIsVerifying(true);
    try {
      const res = await api.confirmWhatsAppVerify(verificationId, otpCode.trim());
      const data = res.data?.data || res.data;
      if (data.status === 'VERIFIED' || data.success) {
        setStatusMsg("WhatsApp number successfully verified!");
        setWaStep('VERIFIED');
        fetchSettings();
      }
    } catch (err) {
      setErrorMsg("Invalid or expired verification code.");
    } finally {
      setIsVerifying(false);
    }
  };

  const handleSendTestWa = async () => {
    setStatusMsg(null);
    setErrorMsg(null);
    try {
      const res = await api.sendTestWhatsApp();
      const data = res.data?.data || res.data;
      if (data.status === 'WHATSAPP_NOT_CONFIGURED') {
        setStatusMsg("WhatsApp alerts active. Simulation message logged safely.");
      } else {
        setStatusMsg("Test alert dispatched via WhatsApp.");
      }
    } catch (err) {
      setErrorMsg("Test notification failed.");
    }
  };

  const handleDisableWa = async () => {
    try {
      await api.disableWhatsApp();
      setStatusMsg("WhatsApp alerts deactivated.");
      setWaStep('ENTER_PHONE');
      fetchSettings();
    } catch (err) {
      setErrorMsg("Failed to disable alerts.");
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-secondary)' }}>
        <Cpu size={32} color="var(--accent-cyan)" className="spin" style={{ marginBottom: '12px' }} />
        <h3>Loading Account & Preferences Settings...</h3>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Settings Title */}
      <div>
        <h2 style={{ fontSize: '1.8rem', fontWeight: 800, margin: 0, color: '#fff' }} className="heading-font">
          System Settings & Customization
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '4px' }}>
          Configure live market preferences, alerts triggers, AI prediction parameters, and phone verification.
        </p>
      </div>

      {statusMsg && (
        <div style={{ padding: '12px 16px', borderRadius: '10px', backgroundColor: 'var(--up-green-bg)', border: '1px solid var(--up-green-border)', color: 'var(--up-green)', fontSize: '0.82rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <CheckCircle size={16} /> <span>{statusMsg}</span>
        </div>
      )}
      {errorMsg && (
        <div style={{ padding: '12px 16px', borderRadius: '10px', backgroundColor: 'var(--down-red-bg)', border: '1px solid var(--down-red-border)', color: 'var(--down-red)', fontSize: '0.82rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <AlertTriangle size={16} /> <span>{errorMsg}</span>
        </div>
      )}

      {/* Grid Settings Sections */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
        
        {/* Section 1: ACCOUNT */}
        <div className="glass-card" style={{ padding: '24px' }}>
          <h3 className="heading-font" style={{ fontSize: '1.05rem', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px', color: '#fff' }}>
            <User size={18} color="var(--accent-cyan)" /> ACCOUNT PROFILE
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', fontSize: '0.85rem' }}>
            <div>
              <label style={labelStyle}>Full Name</label>
              <input
                type="text"
                value={profile?.full_name || ''}
                readOnly
                style={readOnlyInputStyle}
              />
            </div>
            <div>
              <label style={labelStyle}>Email Address</label>
              <input
                type="text"
                value={profile?.email || ''}
                readOnly
                style={readOnlyInputStyle}
              />
            </div>
            <div>
              <label style={labelStyle}>Username / Handle</label>
              <input
                type="text"
                value={profile?.username || ''}
                readOnly
                style={readOnlyInputStyle}
              />
            </div>
            <div>
              <label style={labelStyle}>Access Role</label>
              <span style={{ display: 'inline-block', padding: '3px 8px', borderRadius: '6px', fontSize: '0.72rem', fontWeight: 700, backgroundColor: profile?.role === 'ADMIN' ? 'rgba(234,179,8,0.15)' : 'rgba(0,242,254,0.12)', color: profile?.role === 'ADMIN' ? '#EAB308' : 'var(--accent-cyan)', marginTop: '4px' }}>
                {profile?.role || 'USER'} ACCOUNT
              </span>
            </div>

            <button
              onClick={onLogout}
              style={{
                marginTop: '10px', width: '100%', backgroundColor: 'rgba(239, 68, 68, 0.12)', color: 'var(--down-red)',
                border: '1px solid var(--down-red-border)', padding: '10px', borderRadius: '10px',
                fontWeight: 700, cursor: 'pointer', transition: 'background-color 0.2s'
              }}
            >
              Sign Out from Terminal
            </button>
          </div>
        </div>

        {/* Section 2: MARKET PREFERENCES */}
        <div className="glass-card" style={{ padding: '24px' }}>
          <h3 className="heading-font" style={{ fontSize: '1.05rem', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px', color: '#fff' }}>
            <BarChart size={18} color="var(--accent-cyan)" /> MARKET PREFERENCES
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', fontSize: '0.85rem' }}>
            <div>
              <label style={labelStyle}>Default Load Asset</label>
              <select
                value={preferences?.default_market || 'BTC-USD'}
                onChange={(e) => setPreferences({ ...preferences, default_market: e.target.value })}
                style={selectStyle}
              >
                <option value="BTC-USD">BTC/USD (Bitcoin Spot)</option>
                <option value="SOL-USD">SOL/USD (Solana Spot)</option>
                <option value="XAUUSD">XAU/USD (Gold Spot)</option>
                <option value="RELIANCE">RELIANCE (NSE Indian Equity)</option>
                <option value="TCS">TCS (NSE Indian Equity)</option>
              </select>
            </div>
            <div>
              <label style={labelStyle}>Default Timeframe</label>
              <select
                value={preferences?.default_timeframe || '1d'}
                onChange={(e) => setPreferences({ ...preferences, default_timeframe: e.target.value })}
                style={selectStyle}
              >
                <option value="15m">15 Minutes</option>
                <option value="1h">1 Hour</option>
                <option value="4h">4 Hours</option>
                <option value="1d">1 Day (Daily)</option>
              </select>
            </div>
            <div>
              <label style={labelStyle}>Base Currency</label>
              <select
                value={preferences?.default_currency || 'USD'}
                onChange={(e) => setPreferences({ ...preferences, default_currency: e.target.value })}
                style={selectStyle}
              >
                <option value="USD">USD ($)</option>
                <option value="INR">INR (₹)</option>
                <option value="EUR">EUR (€)</option>
              </select>
            </div>

            <button
              onClick={handleSavePreferences}
              style={saveButtonStyle}
            >
              Save Preferences
            </button>
          </div>
        </div>

        {/* Section 3: WHATSAPP ALERTS */}
        <div className="glass-card" style={{ padding: '24px' }}>
          <h3 className="heading-font" style={{ fontSize: '1.05rem', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px', color: '#fff' }}>
            <MessageSquare size={18} color="var(--accent-cyan)" /> WHATSAPP NOTIFICATIONS
          </h3>
          
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.78rem', marginBottom: '16px', lineHeight: '1.4' }}>
            Verify your phone number to receive high-confluence AI trade setup alerts immediately on WhatsApp.
          </p>

          {waStep === 'ENTER_PHONE' && (
            <form onSubmit={handleRequestWaVerify} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div>
                <label style={labelStyle}>WhatsApp Phone Number (E.164)</label>
                <input
                  type="text"
                  placeholder="+91 98765 43210"
                  value={phoneInput}
                  onChange={(e) => setPhoneInput(e.target.value)}
                  style={inputStyle}
                  required
                />
              </div>
              <button
                type="submit"
                disabled={isVerifying}
                style={verifyButtonStyle}
              >
                {isVerifying ? 'Requesting OTP...' : 'Send Verification Code'}
              </button>
            </form>
          )}

          {waStep === 'ENTER_CODE' && (
            <form onSubmit={handleConfirmWaVerify} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div>
                <label style={labelStyle}>Enter 6-Digit OTP Code</label>
                <input
                  type="text"
                  maxLength={6}
                  placeholder="123456"
                  value={otpCode}
                  onChange={(e) => setOtpCode(e.target.value)}
                  style={{ ...inputStyle, textAlign: 'center', letterSpacing: '4px', fontSize: '1.1rem' }}
                  required
                />
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button type="submit" disabled={isVerifying} style={{ ...verifyButtonStyle, flex: 1 }}>
                  {isVerifying ? 'Verifying...' : 'Confirm Code'}
                </button>
                <button type="button" onClick={() => setWaStep('ENTER_PHONE')} style={cancelButtonStyle}>
                  Cancel
                </button>
              </div>
            </form>
          )}

          {waStep === 'VERIFIED' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={verifiedBadgeStyle}>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Verified Number</div>
                <strong style={{ fontSize: '0.98rem', color: 'var(--up-green)' }}>{profile?.whatsapp?.phone_masked || phoneInput}</strong>
              </div>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                <button onClick={handleSendTestWa} style={testButtonStyle}>
                  Send Test Alert
                </button>
                <button onClick={handleDisableWa} style={disableButtonStyle}>
                  Disable Alerts
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Section 4: AI ANALYSIS PARAMETERS */}
        <div className="glass-card" style={{ padding: '24px' }}>
          <h3 className="heading-font" style={{ fontSize: '1.05rem', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px', color: '#fff' }}>
            <Cpu size={18} color="var(--accent-cyan)" /> AI ANALYSIS
          </h3>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', fontSize: '0.85rem' }}>
            <div>
              <label style={labelStyle}>AI Analysis Mode</label>
              <div style={{ display: 'flex', gap: '8px', marginTop: '6px' }}>
                {['Conservative', 'Balanced', 'Aggressive'].map(mode => {
                  const isSel = preferences?.ai_settings?.preferred_analysis_mode === mode;
                  return (
                    <button
                      key={mode}
                      onClick={() => setPreferences({
                        ...preferences,
                        ai_settings: {
                          ...preferences.ai_settings,
                          preferred_analysis_mode: mode
                        }
                      })}
                      style={{
                        flex: 1, padding: '8px', borderRadius: '8px', border: `1px solid ${isSel ? 'var(--accent-cyan)' : 'var(--border-color)'}`,
                        backgroundColor: isSel ? 'rgba(0, 242, 254, 0.12)' : 'var(--bg-primary)',
                        color: isSel ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                        fontWeight: 700, cursor: 'pointer'
                      }}
                    >
                      {mode}
                    </button>
                  );
                })}
              </div>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '4px', display: 'block' }}>
                {preferences?.ai_settings?.preferred_analysis_mode === 'Conservative' && 'Conservative: Uses high precision models (Logistic Regression).'}
                {preferences?.ai_settings?.preferred_analysis_mode === 'Balanced' && 'Balanced: Uses optimal calibrated production models (XGBoost).'}
                {preferences?.ai_settings?.preferred_analysis_mode === 'Aggressive' && 'Aggressive: Exposes high volatility model predictions (Random Forest).'}
              </span>
            </div>

            <div>
              <label style={labelStyle}>Signal Sensitivity: {preferences?.ai_settings?.signal_sensitivity || 50}%</label>
              <input
                type="range"
                min="10"
                max="90"
                value={preferences?.ai_settings?.signal_sensitivity || 50}
                onChange={(e) => setPreferences({
                  ...preferences,
                  ai_settings: {
                    ...preferences.ai_settings,
                    signal_sensitivity: parseInt(e.target.value)
                  }
                })}
                style={{ width: '100%', accentColor: 'var(--accent-cyan)', marginTop: '4px' }}
              />
            </div>

            <div>
              <label style={labelStyle}>Risk Preference</label>
              <select
                value={preferences?.ai_settings?.risk_preference || 'Medium'}
                onChange={(e) => setPreferences({
                  ...preferences,
                  ai_settings: {
                    ...preferences.ai_settings,
                    risk_preference: e.target.value
                  }
                })}
                style={selectStyle}
              >
                <option value="Low">Low Risk</option>
                <option value="Medium">Medium Balanced</option>
                <option value="High">High Risk / Reward</option>
              </select>
            </div>

            <button
              onClick={handleSavePreferences}
              style={saveButtonStyle}
            >
              Save AI Settings
            </button>
          </div>
        </div>

        {/* Section 5: MARKET STRUCTURE ALERTS */}
        <div className="glass-card" style={{ padding: '24px', gridColumn: 'span 2' }}>
          <h3 className="heading-font" style={{ fontSize: '1.05rem', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px', color: '#fff' }}>
            <Bell size={18} color="var(--accent-cyan)" /> MARKET STRUCTURE ALERTS
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px', fontSize: '0.85rem' }}>
            
            <label style={toggleWrapperStyle}>
              <input
                type="checkbox"
                checked={preferences?.alerts?.liquidity_sweep || false}
                onChange={(e) => setPreferences({
                  ...preferences,
                  alerts: { ...preferences.alerts, liquidity_sweep: e.target.checked }
                })}
              />
              <span>Liquidity Sweeps Alerts</span>
            </label>

            <label style={toggleWrapperStyle}>
              <input
                type="checkbox"
                checked={preferences?.alerts?.bos || false}
                onChange={(e) => setPreferences({
                  ...preferences,
                  alerts: { ...preferences.alerts, bos: e.target.checked }
                })}
              />
              <span>Break of Structure (BOS)</span>
            </label>

            <label style={toggleWrapperStyle}>
              <input
                type="checkbox"
                checked={preferences?.alerts?.choch || false}
                onChange={(e) => setPreferences({
                  ...preferences,
                  alerts: { ...preferences.alerts, choch: e.target.checked }
                })}
              />
              <span>Change of Character (CHoCH)</span>
            </label>

            <label style={toggleWrapperStyle}>
              <input
                type="checkbox"
                checked={preferences?.alerts?.fvg || false}
                onChange={(e) => setPreferences({
                  ...preferences,
                  alerts: { ...preferences.alerts, fvg: e.target.checked }
                })}
              />
              <span>Fair Value Gaps (FVG)</span>
            </label>

            <label style={toggleWrapperStyle}>
              <input
                type="checkbox"
                checked={preferences?.alerts?.order_block || false}
                onChange={(e) => setPreferences({
                  ...preferences,
                  alerts: { ...preferences.alerts, order_block: e.target.checked }
                })}
              />
              <span>Order Block Identification</span>
            </label>

            <label style={toggleWrapperStyle}>
              <input
                type="checkbox"
                checked={preferences?.alerts?.entry_alerts || false}
                onChange={(e) => setPreferences({
                  ...preferences,
                  alerts: { ...preferences.alerts, entry_alerts: e.target.checked }
                })}
              />
              <span>Trade Entry Triggers</span>
            </label>

            <label style={toggleWrapperStyle}>
              <input
                type="checkbox"
                checked={preferences?.alerts?.tp_alerts || false}
                onChange={(e) => setPreferences({
                  ...preferences,
                  alerts: { ...preferences.alerts, tp_alerts: e.target.checked }
                })}
              />
              <span>Take Profit (TP) Alerts</span>
            </label>

            <label style={toggleWrapperStyle}>
              <input
                type="checkbox"
                checked={preferences?.alerts?.sl_alerts || false}
                onChange={(e) => setPreferences({
                  ...preferences,
                  alerts: { ...preferences.alerts, sl_alerts: e.target.checked }
                })}
              />
              <span>Stop Loss (SL) Alerts</span>
            </label>
          </div>

          <div style={{ borderTop: '1px solid var(--border-color)', marginTop: '20px', paddingTop: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              Confluence Score Gate: <strong>{preferences?.alerts?.confluence_threshold || 70}%</strong>
            </div>
            <input
              type="range"
              min="50"
              max="95"
              step="5"
              value={preferences?.alerts?.confluence_threshold || 70}
              onChange={(e) => setPreferences({
                ...preferences,
                alerts: { ...preferences.alerts, confluence_threshold: parseInt(e.target.value) }
              })}
              style={{ width: '200px', accentColor: 'var(--accent-cyan)' }}
            />
          </div>

          <button
            onClick={handleSavePreferences}
            style={{ ...saveButtonStyle, marginTop: '20px', width: 'auto', padding: '10px 24px' }}
          >
            Save Alert Triggers
          </button>
        </div>

      </div>
    </div>
  );
}

// Styling Constants
const labelStyle = {
  display: 'block',
  fontSize: '0.72rem',
  fontWeight: 700,
  color: 'var(--text-secondary)',
  textTransform: 'uppercase',
  letterSpacing: '0.04em',
  marginBottom: '6px'
};

const inputStyle = {
  width: '100%',
  backgroundColor: 'var(--bg-primary)',
  border: '1px solid var(--border-color)',
  borderRadius: '8px',
  color: '#fff',
  padding: '10px 12px',
  fontSize: '0.86rem',
  outline: 'none',
  boxSizing: 'border-box'
};

const readOnlyInputStyle = {
  ...inputStyle,
  color: 'var(--text-secondary)',
  borderColor: 'rgba(255,255,255,0.04)',
  backgroundColor: 'rgba(255,255,255,0.02)',
  cursor: 'not-allowed'
};

const selectStyle = {
  width: '100%',
  backgroundColor: 'var(--bg-primary)',
  border: '1px solid var(--border-color)',
  borderRadius: '8px',
  color: '#fff',
  padding: '10px 12px',
  fontSize: '0.86rem',
  outline: 'none',
  cursor: 'pointer'
};

const saveButtonStyle = {
  backgroundColor: 'var(--accent-blue)',
  color: '#070a11',
  border: 'none',
  padding: '10px 16px',
  borderRadius: '8px',
  fontWeight: 700,
  cursor: 'pointer',
  fontSize: '0.82rem',
  transition: 'background-color 0.2s',
  marginTop: '8px',
  boxShadow: '0 4px 12px rgba(56, 189, 248, 0.2)'
};

const verifyButtonStyle = {
  backgroundColor: 'var(--up-green)',
  color: '#070a11',
  border: 'none',
  padding: '10px 16px',
  borderRadius: '8px',
  fontWeight: 700,
  cursor: 'pointer',
  fontSize: '0.82rem'
};

const cancelButtonStyle = {
  backgroundColor: 'var(--bg-primary)',
  color: 'var(--text-secondary)',
  border: '1px solid var(--border-color)',
  padding: '10px 16px',
  borderRadius: '8px',
  fontWeight: 600,
  cursor: 'pointer',
  fontSize: '0.82rem'
};

const verifiedBadgeStyle = {
  padding: '14px',
  backgroundColor: 'var(--up-green-bg)',
  border: '1px solid var(--up-green-border)',
  borderRadius: '8px'
};

const testButtonStyle = {
  flex: 1,
  backgroundColor: 'var(--bg-primary)',
  color: 'var(--accent-cyan)',
  border: '1px solid var(--border-glow)',
  padding: '8px 12px',
  borderRadius: '8px',
  fontWeight: 600,
  cursor: 'pointer',
  fontSize: '0.78rem'
};

const disableButtonStyle = {
  backgroundColor: 'rgba(239, 68, 68, 0.15)',
  color: 'var(--down-red)',
  border: '1px solid var(--down-red-border)',
  padding: '8px 12px',
  borderRadius: '8px',
  fontWeight: 600,
  cursor: 'pointer',
  fontSize: '0.78rem'
};

const toggleWrapperStyle = {
  display: 'flex',
  alignItems: 'center',
  gap: '10px',
  cursor: 'pointer',
  userSelect: 'none'
};
