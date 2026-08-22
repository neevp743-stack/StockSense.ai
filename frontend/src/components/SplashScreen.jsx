import React, { useEffect, useState } from 'react';
import { Logo } from './Logo';

export function SplashScreen({ onFinish }) {
  const [stage, setStage] = useState(0); // 0: init logo, 1: text reveal, 2: fade out

  useEffect(() => {
    // Respect prefers-reduced-motion
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const isReturningUser = sessionStorage.getItem('stocksense_visited') === 'true';

    if (prefersReducedMotion || isReturningUser) {
      // Fast path for returning visitors (~300ms)
      const timer = setTimeout(() => {
        sessionStorage.setItem('stocksense_visited', 'true');
        onFinish();
      }, 300);
      return () => clearTimeout(timer);
    }

    // First visit animation sequence (total ~1.2s max)
    sessionStorage.setItem('stocksense_visited', 'true');

    const t1 = setTimeout(() => setStage(1), 400);  // Text reveal
    const t2 = setTimeout(() => setStage(2), 1000); // Fade out start
    const t3 = setTimeout(() => onFinish(), 1250);   // Finish & mount app

    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
    };
  }, [onFinish]);

  return (
    <div 
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 9999,
        backgroundColor: '#05070c',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        opacity: stage === 2 ? 0 : 1,
        transition: 'opacity 0.25s ease-out',
        pointerEvents: stage === 2 ? 'none' : 'auto'
      }}
    >
      {/* Glow Backdrop */}
      <div 
        style={{
          position: 'absolute',
          width: '280px',
          height: '280px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(0, 242, 254, 0.15) 0%, rgba(0, 0, 0, 0) 70%)',
          filter: 'blur(20px)',
          animation: 'pulseGlow 1.5s infinite ease-in-out'
        }}
      />

      {/* Logo & Reveal Animation */}
      <div style={{ position: 'relative', zIndex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
        <Logo size={64} showText={false} animated={true} />

        <div 
          style={{ 
            opacity: stage >= 1 ? 1 : 0, 
            transform: stage >= 1 ? 'translateY(0)' : 'translateY(10px)',
            transition: 'all 0.35s cubic-bezier(0.16, 1, 0.3, 1)',
            textAlign: 'center' 
          }}
        >
          <h1 className="heading-font" style={{ fontSize: '2.2rem', fontWeight: 800, color: '#fff', letterSpacing: '-0.03em' }}>
            StockSense <span style={{ color: 'var(--accent-cyan)' }}>AI</span>
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', fontWeight: 500, letterSpacing: '0.05em', marginTop: '2px', textTransform: 'uppercase' }}>
            AI-Powered Market Intelligence
          </p>
        </div>

        {/* Small Progress Dots */}
        <div style={{ display: 'flex', gap: '6px', marginTop: '16px', opacity: stage >= 1 ? 1 : 0 }}>
          <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--accent-cyan)', animation: 'spin 1s infinite linear' }} />
          <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--accent-cyan)', opacity: 0.5 }} />
          <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--accent-cyan)', opacity: 0.2 }} />
        </div>
      </div>
    </div>
  );
}
