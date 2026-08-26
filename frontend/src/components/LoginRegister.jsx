import React, { useState, useEffect } from 'react';
import { api } from '../api';
import { Lock, Mail, User, Phone, CheckCircle, AlertTriangle, Eye, EyeOff } from 'lucide-react';

export function LoginRegister({ onAuthSuccess }) {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState(null);

  // Clear errors when toggling modes
  useEffect(() => {
    setError(null);
    setSuccessMsg(null);
    setPassword('');
    setConfirmPassword('');
  }, [isLogin]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);

    // Frontend validations
    if (!isLogin) {
      if (!fullName.trim()) {
        setError("Full Name is required.");
        return;
      }
      if (password !== confirmPassword) {
        setError("Passwords do not match.");
        return;
      }
      if (password.length < 6) {
        setError("Password must be at least 6 characters.");
        return;
      }
    }

    setLoading(true);
    try {
      if (isLogin) {
        // Login Flow
        const res = await api.loginUser(email, password);
        const data = res.data?.data || res.data;
        if (data.access_token) {
          localStorage.setItem('stocksense_token', data.access_token);
          setSuccessMsg("Access granted. Initializing terminal...");
          setTimeout(() => {
            onAuthSuccess(data.access_token);
          }, 400);
        } else {
          setError("Failed to fetch access credentials.");
        }
      } else {
        // Registration Flow
        const regRes = await api.registerUser(null, email, password, {
          full_name: fullName,
          phone_number: phoneNumber
        });
        setSuccessMsg("Account created! Logging in...");
        
        // Auto Login after Registration
        setTimeout(async () => {
          try {
            const loginRes = await api.loginUser(email, password);
            const loginData = loginRes.data?.data || loginRes.data;
            if (loginData.access_token) {
              localStorage.setItem('stocksense_token', loginData.access_token);
              onAuthSuccess(loginData.access_token);
            } else {
              setIsLogin(true);
              setSuccessMsg(null);
            }
          } catch (loginErr) {
            setIsLogin(true);
            setSuccessMsg(null);
          }
        }, 800);
      }
    } catch (err) {
      const detail = err.response?.data?.detail;
      const code = detail?.code || "";
      
      if (code === "INVALID_CREDENTIALS") {
        setError("Email or password is incorrect.");
      } else if (code === "USER_ALREADY_EXISTS") {
        setError("An account with this email is already registered.");
      } else if (err.response?.status === 429) {
        setError("Too many login attempts. Please try again in a few minutes.");
      } else {
        setError("Unable to complete credentials verification. Please try again shortly.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={containerStyle}>
      {/* Decorative Grid Backdrop (GPU Friendly transform movement) */}
      <div style={gridBackdropStyle} className="decorative-grid" />
      
      {/* Visual Header Motif */}
      <div style={headerMotifStyle}>
        <div style={logoIconStyle}>📊</div>
        <h1 style={logoTextStyle} className="heading-font">StockSense AI</h1>
        <p style={logoSubStyle}>AI-Powered Market Intelligence</p>
      </div>

      {/* Glass card container */}
      <div style={glassCardStyle}>
        <h2 style={formTitleStyle} className="heading-font">
          {isLogin ? "Welcome Back" : "Create Account"}
        </h2>
        <p style={formSubStyle}>
          {isLogin ? "Sign in to access advanced BTC, SOL, and XAU intelligence" : "Get started with professional-grade analysis tools"}
        </p>

        {error && (
          <div style={errorContainerStyle}>
            <AlertTriangle size={16} color="var(--down-red)" style={{ flexShrink: 0 }} />
            <span style={errorTextStyle}>{error}</span>
          </div>
        )}

        {successMsg && (
          <div style={successContainerStyle}>
            <CheckCircle size={16} color="var(--up-green)" style={{ flexShrink: 0 }} />
            <span style={successTextStyle}>{successMsg}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} style={formStyle}>
          {!isLogin && (
            <div style={inputGroupStyle}>
              <label style={labelStyle}>Full Name</label>
              <div style={inputWrapperStyle}>
                <User size={16} style={inputIconStyle} />
                <input
                  type="text"
                  placeholder="Enter full name"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  style={inputStyle}
                  required
                />
              </div>
            </div>
          )}

          <div style={inputGroupStyle}>
            <label style={labelStyle}>Email Address</label>
            <div style={inputWrapperStyle}>
              <Mail size={16} style={inputIconStyle} />
              <input
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                style={inputStyle}
                required
              />
            </div>
          </div>

          <div style={inputGroupStyle}>
            <label style={labelStyle}>Password</label>
            <div style={inputWrapperStyle}>
              <Lock size={16} style={inputIconStyle} />
              <input
                type={showPassword ? "text" : "password"}
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                style={inputStyle}
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={passwordToggleStyle}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          {!isLogin && (
            <>
              <div style={inputGroupStyle}>
                <label style={labelStyle}>Confirm Password</label>
                <div style={inputWrapperStyle}>
                  <Lock size={16} style={inputIconStyle} />
                  <input
                    type="password"
                    placeholder="••••••••"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    style={inputStyle}
                    required
                  />
                </div>
              </div>

              <div style={inputGroupStyle}>
                <label style={labelStyle}>WhatsApp Alerts Number (Optional)</label>
                <div style={inputWrapperStyle}>
                  <Phone size={16} style={inputIconStyle} />
                  <input
                    type="tel"
                    placeholder="+1 555 123 4567"
                    value={phoneNumber}
                    onChange={(e) => setPhoneNumber(e.target.value)}
                    style={inputStyle}
                  />
                </div>
                <span style={inputHelpStyle}>For secure, high-confluence alerts. Can be verified later.</span>
              </div>
            </>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              ...submitButtonStyle,
              opacity: loading ? 0.75 : 1,
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? (isLogin ? "Verifying..." : "Creating Account...") : (isLogin ? "Sign In" : "Register")}
          </button>
        </form>

        <div style={footerToggleContainer}>
          <button 
            type="button" 
            onClick={() => setIsLogin(!isLogin)} 
            style={toggleLinkStyle}
          >
            {isLogin ? "Don't have an account? Register" : "Already have an account? Sign In"}
          </button>
        </div>
      </div>
      
      {/* Inline Subtle Market Quote Bar */}
      <div style={marketTickersContainer}>
        <div style={tickerStyle}>BTC/USD <span style={{ color: 'var(--up-green)' }}>▲ Live</span></div>
        <div style={tickerSeparator}>•</div>
        <div style={tickerStyle}>SOL/USD <span style={{ color: 'var(--up-green)' }}>▲ Live</span></div>
        <div style={tickerSeparator}>•</div>
        <div style={tickerStyle}>XAU/USD <span style={{ color: 'var(--accent-cyan)' }}>■ Spot</span></div>
      </div>
    </div>
  );
}

const containerStyle = {
  position: 'relative',
  width: '100%',
  minHeight: '100vh',
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'center',
  alignItems: 'center',
  padding: '40px 20px',
  background: '#070a11',
  overflow: 'hidden'
};

const gridBackdropStyle = {
  position: 'absolute',
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  opacity: 0.1,
  backgroundImage: 'radial-gradient(rgba(255,255,255,0.08) 1px, transparent 1px)',
  backgroundSize: '24px 24px',
  zIndex: 1,
  pointerEvents: 'none'
};

const headerMotifStyle = {
  textAlign: 'center',
  marginBottom: '28px',
  zIndex: 10
};

const logoIconStyle = {
  fontSize: '2.5rem',
  marginBottom: '8px'
};

const logoTextStyle = {
  fontSize: '2.4rem',
  fontWeight: 800,
  background: 'linear-gradient(135deg, #00f2fe 0%, #38bdf8 100%)',
  WebkitBackgroundClip: 'text',
  WebkitTextFillColor: 'transparent',
  margin: 0
};

const logoSubStyle = {
  fontSize: '0.9rem',
  color: 'var(--text-secondary)',
  marginTop: '4px',
  fontWeight: 500
};

const glassCardStyle = {
  position: 'relative',
  width: '100%',
  maxWidth: '430px',
  background: 'rgba(13, 19, 31, 0.85)',
  backdropFilter: 'blur(20px)',
  WebkitBackdropFilter: 'blur(20px)',
  border: '1px solid var(--border-color)',
  borderRadius: '20px',
  padding: '36px 30px',
  boxShadow: '0 20px 60px rgba(0, 0, 0, 0.5)',
  zIndex: 10,
  boxSizing: 'border-box'
};

const formTitleStyle = {
  fontSize: '1.4rem',
  fontWeight: 800,
  color: '#fff',
  margin: 0
};

const formSubStyle = {
  fontSize: '0.82rem',
  color: 'var(--text-secondary)',
  marginTop: '6px',
  marginBottom: '24px',
  lineHeight: '1.4'
};

const errorContainerStyle = {
  display: 'flex',
  alignItems: 'center',
  gap: '10px',
  background: 'var(--down-red-bg)',
  border: '1px solid var(--down-red-border)',
  borderRadius: '10px',
  padding: '10px 14px',
  marginBottom: '20px'
};

const errorTextStyle = {
  color: 'var(--down-red)',
  fontSize: '0.8rem',
  fontWeight: 500
};

const successContainerStyle = {
  display: 'flex',
  alignItems: 'center',
  gap: '10px',
  background: 'var(--up-green-bg)',
  border: '1px solid var(--up-green-border)',
  borderRadius: '10px',
  padding: '10px 14px',
  marginBottom: '20px'
};

const successTextStyle = {
  color: 'var(--up-green)',
  fontSize: '0.8rem',
  fontWeight: 500
};

const formStyle = {
  display: 'flex',
  flexDirection: 'column',
  gap: '16px'
};

const inputGroupStyle = {
  display: 'flex',
  flexDirection: 'column',
  gap: '6px'
};

const labelStyle = {
  fontSize: '0.74rem',
  fontWeight: 700,
  color: 'var(--text-secondary)',
  textTransform: 'uppercase',
  letterSpacing: '0.04em'
};

const inputWrapperStyle = {
  position: 'relative',
  display: 'flex',
  alignItems: 'center'
};

const inputIconStyle = {
  position: 'absolute',
  left: '12px',
  color: 'var(--text-muted)'
};

const inputStyle = {
  width: '100%',
  background: 'var(--bg-primary)',
  border: '1px solid var(--border-color)',
  borderRadius: '10px',
  color: '#fff',
  padding: '10px 14px 10px 38px',
  fontSize: '0.86rem',
  outline: 'none',
  transition: 'border-color 0.2s ease',
  boxSizing: 'border-box'
};

const passwordToggleStyle = {
  position: 'absolute',
  right: '12px',
  background: 'transparent',
  border: 'none',
  color: 'var(--text-muted)',
  cursor: 'pointer',
  display: 'flex',
  alignItems: 'center'
};

const inputHelpStyle = {
  fontSize: '0.68rem',
  color: 'var(--text-muted)',
  marginTop: '2px'
};

const submitButtonStyle = {
  width: '100%',
  background: 'linear-gradient(135deg, #00f2fe 0%, #38bdf8 100%)',
  color: '#070a11',
  border: 'none',
  borderRadius: '10px',
  padding: '12px',
  fontSize: '0.9rem',
  fontWeight: 700,
  marginTop: '8px',
  boxShadow: '0 8px 24px rgba(0, 242, 254, 0.25)',
  transition: 'transform 0.15s ease, opacity 0.2s ease'
};

const footerToggleContainer = {
  marginTop: '24px',
  textAlign: 'center'
};

const toggleLinkStyle = {
  background: 'transparent',
  border: 'none',
  color: 'var(--accent-blue)',
  fontSize: '0.8rem',
  fontWeight: 600,
  cursor: 'pointer',
  textDecoration: 'none'
};

const marketTickersContainer = {
  display: 'flex',
  alignItems: 'center',
  gap: '14px',
  marginTop: '36px',
  fontSize: '0.76rem',
  color: 'var(--text-muted)',
  zIndex: 10
};

const tickerStyle = {
  fontWeight: 600
};

const tickerSeparator = {
  opacity: 0.3
};
