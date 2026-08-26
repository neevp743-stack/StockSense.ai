import React, { useState, useEffect } from 'react';
import { api } from '../api';

export function UserInformationPage() {
  const [profile, setProfile] = useState({
    username: 'Trader_Pro',
    email: 'trader@stocksense.ai',
    role: 'USER',
    created_at: '2026-01-15',
    whatsapp: {
      status: 'UNVERIFIED',
      phone_masked: null,
      alerts_enabled: false
    }
  });

  const [preferences, setPreferences] = useState({
    theme: 'dark',
    default_market: 'BTC-USD',
    default_timeframe: '1d',
    default_currency: 'USD',
    notifications_enabled: true,
    alerts: {
      liquidity_sweep: true,
      confluence: true,
      price_alerts: true,
      regime_change: true,
      whatsapp: false
    }
  });

  const [phoneInput, setPhoneInput] = useState('+91 ');
  const [verificationId, setVerificationId] = useState('');
  const [otpCode, setOtpCode] = useState('');
  const [isVerifying, setIsVerifying] = useState(false);
  const [step, setStep] = useState('ENTER_PHONE'); // ENTER_PHONE, ENTER_CODE, VERIFIED
  const [statusMessage, setStatusMessage] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  // Authentication State
  const [token, setToken] = useState(localStorage.getItem('stocksense_token') || null);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authMode, setAuthMode] = useState('login'); // login or register
  const [authUsername, setAuthUsername] = useState('');
  const [authEmail, setAuthEmail] = useState('');
  const [authPassword, setAuthPassword] = useState('');

  // Load User Data
  useEffect(() => {
    fetchUserData();
  }, [token]);

  const fetchUserData = async () => {
    if (!token) return;
    try {
      setIsLoading(true);
      const [profRes, prefRes] = await Promise.all([
        api.getUserProfile().catch(() => null),
        api.getUserPreferences().catch(() => null)
      ]);

      if (profRes && profRes.data && profRes.data.data) {
        setProfile(profRes.data.data);
        if (profRes.data.data.whatsapp?.status === 'VERIFIED') {
          setStep('VERIFIED');
        }
      }
      if (prefRes && prefRes.data && prefRes.data.data) {
        setPreferences(prefRes.data.data);
      }
    } catch (err) {
      console.warn('Failed to load profile via v1 API, using default user state:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAuthSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage(null);
    setStatusMessage(null);
    try {
      if (authMode === 'register') {
        const res = await api.registerUser(authUsername, authEmail, authPassword);
        setStatusMessage('Registration successful! Logging in...');
        const loginRes = await api.loginUser(authUsername, authPassword);
        const tok = loginRes.data.data.access_token;
        localStorage.setItem('stocksense_token', tok);
        setToken(tok);
        setShowAuthModal(false);
      } else {
        const loginRes = await api.loginUser(authUsername, authPassword);
        const tok = loginRes.data.data.access_token;
        localStorage.setItem('stocksense_token', tok);
        setToken(tok);
        setStatusMessage('Logged in successfully!');
        setShowAuthModal(false);
      }
    } catch (err) {
      const msg = err.response?.data?.detail?.message || err.response?.data?.error?.message || err.message;
      setErrorMessage(msg);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('stocksense_token');
    setToken(null);
    setStatusMessage('Logged out successfully.');
  };

  const handleSavePreferences = async () => {
    setErrorMessage(null);
    setStatusMessage(null);
    try {
      if (token) {
        await api.updateUserPreferences(preferences);
      }
      setStatusMessage('Preferences saved successfully!');
      setTimeout(() => setStatusMessage(null), 3000);
    } catch (err) {
      setErrorMessage('Failed to save preferences.');
    }
  };

  // WhatsApp Verification Handlers
  const handleRequestVerification = async (e) => {
    e.preventDefault();
    setErrorMessage(null);
    setStatusMessage(null);

    if (!phoneInput || phoneInput.trim().length < 8) {
      setErrorMessage('Please enter a valid international phone number (e.g. +91 98765 43210).');
      return;
    }

    try {
      setIsVerifying(true);
      const res = await api.requestWhatsAppVerify(phoneInput.trim());
      const data = res.data?.data || res.data;

      if (data.status === 'WHATSAPP_NOT_CONFIGURED') {
        setVerificationId(data.verification_id);
        setStatusMessage('⚠️ Verification code generated! Note: Official WhatsApp API credentials are not configured in environment, but phone flow is valid.');
        setStep('ENTER_CODE');
      } else if (data.status === 'VERIFICATION_SENT' || data.success) {
        setVerificationId(data.verification_id);
        setStatusMessage(`Verification code sent to ${data.masked_phone || phoneInput}! Expires in 5 minutes.`);
        setStep('ENTER_CODE');
      } else {
        setErrorMessage(data.message || 'Verification request failed.');
      }
    } catch (err) {
      const msg = err.response?.data?.detail?.message || err.response?.data?.error?.message || err.message;
      setErrorMessage(msg || 'Failed to send WhatsApp verification code.');
    } finally {
      setIsVerifying(false);
    }
  };

  const handleConfirmVerification = async (e) => {
    e.preventDefault();
    setErrorMessage(null);
    setStatusMessage(null);

    if (!otpCode || otpCode.trim().length !== 6) {
      setErrorMessage('Please enter the complete 6-digit verification code.');
      return;
    }

    try {
      setIsVerifying(true);
      const res = await api.confirmWhatsAppVerify(verificationId, otpCode.trim());
      const data = res.data?.data || res.data;

      if (data.status === 'VERIFIED' || data.success) {
        setStatusMessage('🎉 WhatsApp number successfully verified! Alerts are now active.');
        setProfile(prev => ({
          ...prev,
          whatsapp: {
            status: 'VERIFIED',
            phone_masked: data.masked_phone || maskLocal(phoneInput),
            alerts_enabled: true
          }
        }));
        setStep('VERIFIED');
      }
    } catch (err) {
      const msg = err.response?.data?.detail?.message || err.response?.data?.error?.message || err.message;
      setErrorMessage(msg || 'Invalid verification code or code expired.');
    } finally {
      setIsVerifying(false);
    }
  };

  const handleTestWhatsApp = async () => {
    setErrorMessage(null);
    setStatusMessage(null);
    try {
      const res = await api.sendTestWhatsApp();
      const data = res.data?.data || res.data;
      if (data.status === 'WHATSAPP_NOT_CONFIGURED') {
        setStatusMessage('⚠️ WhatsApp verification active. Note: WHATSAPP_NOT_CONFIGURED (Provider API key not in .env). Test simulation completed safely.');
      } else {
        setStatusMessage('✅ Test WhatsApp alert delivered to your phone!');
      }
    } catch (err) {
      const msg = err.response?.data?.detail?.message || err.response?.data?.error?.message || err.message;
      setErrorMessage(msg || 'Test message failed.');
    }
  };

  const handleDisableWhatsApp = async () => {
    try {
      await api.disableWhatsApp();
      setProfile(prev => ({
        ...prev,
        whatsapp: { ...prev.whatsapp, alerts_enabled: false }
      }));
      setStatusMessage('WhatsApp alerts disabled.');
    } catch (err) {
      setErrorMessage('Failed to disable WhatsApp alerts.');
    }
  };

  const maskLocal = (str) => {
    const clean = str.replace(/\s+/g, '');
    if (clean.length < 7) return '******';
    return `${clean.slice(0, 3)} ****** ${clean.slice(-4)}`;
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '24px 16px', color: '#f3f4f6' }}>
      
      {/* Page Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '28px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 style={{ fontSize: '28px', fontWeight: '800', background: 'linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', margin: 0 }}>
            User Account & Preferences
          </h1>
          <p style={{ color: '#9ca3af', fontSize: '14px', margin: '4px 0 0 0' }}>
            Manage profile, security credentials, market settings, and verified WhatsApp alerts
          </p>
        </div>

        <div>
          {token ? (
            <button
              onClick={handleLogout}
              style={{
                backgroundColor: 'rgba(239, 68, 68, 0.15)', color: '#f87171', border: '1px solid rgba(239, 68, 68, 0.3)',
                padding: '8px 16px', borderRadius: '8px', fontWeight: '600', cursor: 'pointer', fontSize: '14px'
              }}
            >
              Sign Out
            </button>
          ) : (
            <button
              onClick={() => { setAuthMode('login'); setShowAuthModal(true); }}
              style={{
                backgroundColor: '#3b82f6', color: '#ffffff', border: 'none',
                padding: '10px 20px', borderRadius: '8px', fontWeight: '600', cursor: 'pointer', fontSize: '14px',
                boxShadow: '0 4px 12px rgba(59, 130, 246, 0.3)'
              }}
            >
              Sign In / Register
            </button>
          )}
        </div>
      </div>

      {/* Global Banners */}
      {statusMessage && (
        <div style={{ padding: '12px 16px', borderRadius: '8px', backgroundColor: 'rgba(34, 197, 94, 0.15)', border: '1px solid rgba(34, 197, 94, 0.3)', color: '#4ade80', marginBottom: '20px', fontSize: '14px' }}>
          {statusMessage}
        </div>
      )}
      {errorMessage && (
        <div style={{ padding: '12px 16px', borderRadius: '8px', backgroundColor: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.3)', color: '#f87171', marginBottom: '20px', fontSize: '14px' }}>
          {errorMessage}
        </div>
      )}

      {/* Grid Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '24px' }}>

        {/* Card 1: User Profile & Security */}
        <div style={{ backgroundColor: '#111827', border: '1px solid #1f2937', borderRadius: '12px', padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '20px' }}>
            <div style={{ width: '56px', height: '56px', borderRadius: '50%', background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '24px', fontWeight: 'bold' }}>
              {profile.username ? profile.username[0].toUpperCase() : 'U'}
            </div>
            <div>
              <h2 style={{ fontSize: '18px', fontWeight: '700', margin: 0 }}>{profile.username}</h2>
              <span style={{ fontSize: '12px', color: '#9ca3af' }}>{profile.email}</span>
              <div style={{ marginTop: '4px' }}>
                <span style={{ fontSize: '11px', fontWeight: '700', padding: '2px 8px', borderRadius: '12px', backgroundColor: profile.role === 'ADMIN' ? 'rgba(234, 179, 8, 0.2)' : 'rgba(59, 130, 246, 0.2)', color: profile.role === 'ADMIN' ? '#fde047' : '#93c5fd' }}>
                  {profile.role || 'USER'} ROLE
                </span>
              </div>
            </div>
          </div>

          <div style={{ borderTop: '1px solid #1f2937', paddingTop: '16px', display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '14px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#9ca3af' }}>Account Status:</span>
              <span style={{ color: token ? '#4ade80' : '#fbbf24', fontWeight: '600' }}>
                {token ? '🟢 Authenticated' : '🟡 Guest Mode (Session Active)'}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#9ca3af' }}>Member Since:</span>
              <span>{profile.created_at ? profile.created_at.slice(0, 10) : '2026-01-15'}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#9ca3af' }}>JWT Token Expiry:</span>
              <span style={{ color: '#9ca3af', fontSize: '13px' }}>4 Hours (Expiring Refresh)</span>
            </div>
          </div>
        </div>

        {/* Card 2: WhatsApp Verification Flow */}
        <div style={{ backgroundColor: '#111827', border: '1px solid #1f2937', borderRadius: '12px', padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h2 style={{ fontSize: '18px', fontWeight: '700', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
              💬 WhatsApp Alert Verification
            </h2>
            <span style={{
              fontSize: '12px', fontWeight: '700', padding: '3px 10px', borderRadius: '12px',
              backgroundColor: step === 'VERIFIED' ? 'rgba(34, 197, 94, 0.2)' : (step === 'ENTER_CODE' ? 'rgba(234, 179, 8, 0.2)' : 'rgba(156, 163, 175, 0.2)'),
              color: step === 'VERIFIED' ? '#4ade80' : (step === 'ENTER_CODE' ? '#fde047' : '#9ca3af')
            }}>
              {step === 'VERIFIED' ? '🟢 VERIFIED' : (step === 'ENTER_CODE' ? '🟡 CODE SENT' : '🔴 UNVERIFIED')}
            </span>
          </div>

          <p style={{ color: '#9ca3af', fontSize: '13px', marginBottom: '20px' }}>
            Verify your international phone number via WhatsApp to receive realtime liquidity sweep and high-confluence trade setup alerts directly on mobile.
          </p>

          {/* STEP 1: ENTER PHONE */}
          {step === 'ENTER_PHONE' && (
            <form onSubmit={handleRequestVerification} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '12px', color: '#9ca3af', marginBottom: '6px' }}>
                  International WhatsApp Phone Number (E.164)
                </label>
                <input
                  type="text"
                  value={phoneInput}
                  onChange={(e) => setPhoneInput(e.target.value)}
                  placeholder="+91 98765 43210"
                  style={{
                    width: '100%', backgroundColor: '#1f2937', border: '1px solid #374151', color: '#f3f4f6',
                    padding: '10px 14px', borderRadius: '8px', fontSize: '14px', outline: 'none'
                  }}
                  required
                />
              </div>

              <button
                type="submit"
                disabled={isVerifying}
                style={{
                  backgroundColor: '#16a34a', color: '#ffffff', border: 'none', padding: '10px 16px',
                  borderRadius: '8px', fontWeight: '600', cursor: 'pointer', fontSize: '14px',
                  opacity: isVerifying ? 0.6 : 1
                }}
              >
                {isVerifying ? 'Sending Code...' : 'Send Verification Code'}
              </button>
            </form>
          )}

          {/* STEP 2: ENTER CODE */}
          {step === 'ENTER_CODE' && (
            <form onSubmit={handleConfirmVerification} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '12px', color: '#9ca3af', marginBottom: '6px' }}>
                  Enter 6-Digit WhatsApp Verification Code
                </label>
                <input
                  type="text"
                  maxLength={6}
                  value={otpCode}
                  onChange={(e) => setOtpCode(e.target.value)}
                  placeholder="123456"
                  style={{
                    width: '100%', backgroundColor: '#1f2937', border: '1px solid #3b82f6', color: '#f3f4f6',
                    padding: '12px 14px', borderRadius: '8px', fontSize: '18px', letterSpacing: '4px', textAlign: 'center', outline: 'none'
                  }}
                  required
                />
                <span style={{ fontSize: '11px', color: '#6b7280', marginTop: '4px', display: 'block' }}>
                  Code expires in 5 minutes. Max 5 verification attempts.
                </span>
              </div>

              <div style={{ display: 'flex', gap: '10px' }}>
                <button
                  type="submit"
                  disabled={isVerifying}
                  style={{
                    flex: 1, backgroundColor: '#2563eb', color: '#ffffff', border: 'none', padding: '10px 16px',
                    borderRadius: '8px', fontWeight: '600', cursor: 'pointer', fontSize: '14px'
                  }}
                >
                  {isVerifying ? 'Verifying...' : 'Verify Code'}
                </button>

                <button
                  type="button"
                  onClick={() => setStep('ENTER_PHONE')}
                  style={{
                    backgroundColor: '#374151', color: '#d1d5db', border: 'none', padding: '10px 14px',
                    borderRadius: '8px', fontWeight: '600', cursor: 'pointer', fontSize: '14px'
                  }}
                >
                  Change Number
                </button>
              </div>
            </form>
          )}

          {/* STEP 3: VERIFIED */}
          {step === 'VERIFIED' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ padding: '14px', backgroundColor: 'rgba(34, 197, 94, 0.1)', border: '1px solid rgba(34, 197, 94, 0.25)', borderRadius: '8px' }}>
                <div style={{ fontSize: '13px', color: '#9ca3af' }}>Verified WhatsApp Number:</div>
                <div style={{ fontSize: '18px', fontWeight: '700', color: '#4ade80', margin: '4px 0' }}>
                  {profile.whatsapp?.phone_masked || maskLocal(phoneInput)}
                </div>
                <div style={{ fontSize: '12px', color: '#6b7280' }}>
                  Alerts: {profile.whatsapp?.alerts_enabled ? 'ON' : 'OFF'}
                </div>
              </div>

              <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                <button
                  onClick={handleTestWhatsApp}
                  style={{
                    flex: 1, backgroundColor: '#059669', color: '#ffffff', border: 'none', padding: '8px 14px',
                    borderRadius: '8px', fontWeight: '600', cursor: 'pointer', fontSize: '13px'
                  }}
                >
                  Send Test WhatsApp
                </button>

                <button
                  onClick={handleDisableWhatsApp}
                  style={{
                    backgroundColor: 'rgba(239, 68, 68, 0.2)', color: '#f87171', border: 'none', padding: '8px 14px',
                    borderRadius: '8px', fontWeight: '600', cursor: 'pointer', fontSize: '13px'
                  }}
                >
                  Disable Alerts
                </button>

                <button
                  onClick={() => setStep('ENTER_PHONE')}
                  style={{
                    backgroundColor: '#374151', color: '#d1d5db', border: 'none', padding: '8px 14px',
                    borderRadius: '8px', fontWeight: '600', cursor: 'pointer', fontSize: '13px'
                  }}
                >
                  Change Number
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Card 3: Platform Preferences */}
        <div style={{ backgroundColor: '#111827', border: '1px solid #1f2937', borderRadius: '12px', padding: '24px' }}>
          <h2 style={{ fontSize: '18px', fontWeight: '700', margin: '0 0 16px 0' }}>⚙️ Platform Preferences</h2>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', fontSize: '14px' }}>
            <div>
              <label style={{ display: 'block', color: '#9ca3af', marginBottom: '4px', fontSize: '12px' }}>Default Market Asset</label>
              <select
                value={preferences.default_market}
                onChange={(e) => setPreferences({ ...preferences, default_market: e.target.value })}
                style={{ width: '100%', backgroundColor: '#1f2937', border: '1px solid #374151', color: '#f3f4f6', padding: '8px 12px', borderRadius: '8px', outline: 'none' }}
              >
                <option value="BTC-USD">BTC/USD (Bitcoin Spot)</option>
                <option value="SOL-USD">SOL/USD (Solana Spot)</option>
                <option value="XAUUSD">XAU/USD (Gold Spot)</option>
                <option value="RELIANCE">RELIANCE (NSE India)</option>
                <option value="TCS">TCS (NSE India)</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', color: '#9ca3af', marginBottom: '4px', fontSize: '12px' }}>Default Chart Timeframe</label>
              <select
                value={preferences.default_timeframe}
                onChange={(e) => setPreferences({ ...preferences, default_timeframe: e.target.value })}
                style={{ width: '100%', backgroundColor: '#1f2937', border: '1px solid #374151', color: '#f3f4f6', padding: '8px 12px', borderRadius: '8px', outline: 'none' }}
              >
                <option value="1d">1 Day (Daily)</option>
                <option value="4h">4 Hours</option>
                <option value="1h">1 Hour</option>
                <option value="15m">15 Minutes</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', color: '#9ca3af', marginBottom: '4px', fontSize: '12px' }}>Base Currency Display</label>
              <select
                value={preferences.default_currency}
                onChange={(e) => setPreferences({ ...preferences, default_currency: e.target.value })}
                style={{ width: '100%', backgroundColor: '#1f2937', border: '1px solid #374151', color: '#f3f4f6', padding: '8px 12px', borderRadius: '8px', outline: 'none' }}
              >
                <option value="USD">USD ($)</option>
                <option value="INR">INR (₹)</option>
                <option value="EUR">EUR (€)</option>
              </select>
            </div>

            <button
              onClick={handleSavePreferences}
              style={{
                backgroundColor: '#3b82f6', color: '#ffffff', border: 'none', padding: '10px 16px',
                borderRadius: '8px', fontWeight: '600', cursor: 'pointer', fontSize: '14px', marginTop: '8px'
              }}
            >
              Save Preferences
            </button>
          </div>
        </div>

        {/* Card 4: Security & Privacy Disclaimer */}
        <div style={{ backgroundColor: '#111827', border: '1px solid #1f2937', borderRadius: '12px', padding: '24px' }}>
          <h2 style={{ fontSize: '18px', fontWeight: '700', margin: '0 0 16px 0' }}>🛡️ Security & Data Privacy</h2>

          <div style={{ fontSize: '13px', color: '#9ca3af', lineHeight: '1.6', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <p style={{ margin: 0 }}>
              <strong style={{ color: '#f3f4f6' }}>Zero Secret Exposure:</strong> API credentials, tokens, and private keys are strictly managed on backend servers and never exposed in client bundles or public repositories.
            </p>
            <p style={{ margin: 0 }}>
              <strong style={{ color: '#f3f4f6' }}>Provider Transparency:</strong> Quotes and candles are ingested live from Coinbase WebSocket streams, Twelve Data API, and NSE feeds.
            </p>
            <p style={{ margin: 0 }}>
              <strong style={{ color: '#f3f4f6' }}>Causality Protection:</strong> Technical indicators and market structures operate with zero look-ahead bias.
            </p>
          </div>
        </div>

      </div>

      {/* Auth Modal */}
      {showAuthModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div style={{ backgroundColor: '#111827', border: '1px solid #374151', borderRadius: '12px', padding: '28px', maxWidth: '400px', width: '100%' }}>
            <h2 style={{ fontSize: '20px', fontWeight: '700', margin: '0 0 16px 0' }}>
              {authMode === 'login' ? 'Sign In to StockSense AI' : 'Register Account'}
            </h2>

            <form onSubmit={handleAuthSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '12px', color: '#9ca3af', marginBottom: '4px' }}>Username</label>
                <input
                  type="text"
                  value={authUsername}
                  onChange={(e) => setAuthUsername(e.target.value)}
                  style={{ width: '100%', backgroundColor: '#1f2937', border: '1px solid #374151', color: '#f3f4f6', padding: '8px 12px', borderRadius: '6px' }}
                  required
                />
              </div>

              {authMode === 'register' && (
                <div>
                  <label style={{ display: 'block', fontSize: '12px', color: '#9ca3af', marginBottom: '4px' }}>Email</label>
                  <input
                    type="email"
                    value={authEmail}
                    onChange={(e) => setAuthEmail(e.target.value)}
                    style={{ width: '100%', backgroundColor: '#1f2937', border: '1px solid #374151', color: '#f3f4f6', padding: '8px 12px', borderRadius: '6px' }}
                    required
                  />
                </div>
              )}

              <div>
                <label style={{ display: 'block', fontSize: '12px', color: '#9ca3af', marginBottom: '4px' }}>Password</label>
                <input
                  type="password"
                  value={authPassword}
                  onChange={(e) => setAuthPassword(e.target.value)}
                  style={{ width: '100%', backgroundColor: '#1f2937', border: '1px solid #374151', color: '#f3f4f6', padding: '8px 12px', borderRadius: '6px' }}
                  required
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', gap: '10px', marginTop: '8px' }}>
                <button
                  type="submit"
                  style={{ flex: 1, backgroundColor: '#3b82f6', color: '#ffffff', border: 'none', padding: '10px', borderRadius: '6px', fontWeight: '600', cursor: 'pointer' }}
                >
                  {authMode === 'login' ? 'Sign In' : 'Register'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowAuthModal(false)}
                  style={{ backgroundColor: '#374151', color: '#d1d5db', border: 'none', padding: '10px 14px', borderRadius: '6px', fontWeight: '600', cursor: 'pointer' }}
                >
                  Cancel
                </button>
              </div>

              <div style={{ textAlign: 'center', marginTop: '8px', fontSize: '13px', color: '#9ca3af' }}>
                {authMode === 'login' ? (
                  <span>Don't have an account? <a href="#register" onClick={(e) => { e.preventDefault(); setAuthMode('register'); }} style={{ color: '#60a5fa' }}>Register</a></span>
                ) : (
                  <span>Already registered? <a href="#login" onClick={(e) => { e.preventDefault(); setAuthMode('login'); }} style={{ color: '#60a5fa' }}>Sign In</a></span>
                )}
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
}
