import React from 'react';
import { LayoutDashboard, Activity, TestTube, Award, History, Flame } from 'lucide-react';

export function MobileNav({ activeTab, onSelectTab }) {
  const tabs = [
    { id: 'dashboard', label: 'Markets', icon: LayoutDashboard },
    { id: 'intelligence', label: 'Intel', icon: Flame },
    { id: 'live-research', label: 'Live AI', icon: Activity },
    { id: 'ablation', label: 'Ablation', icon: TestTube },
    { id: 'leaderboard', label: 'Models', icon: Award },
    { id: 'backtest', label: 'Backtest', icon: History },
  ];

  return (
    <div 
      style={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        zIndex: 90,
        background: 'rgba(7, 10, 17, 0.95)',
        backdropFilter: 'blur(20px)',
        borderTop: '1px solid var(--border-color)',
        display: 'flex',
        justifyContent: 'space-around',
        alignItems: 'center',
        padding: '8px 4px 12px 4px'
      }}
      className="mobile-only-nav"
    >
      {tabs.map(t => {
        const Icon = t.icon;
        const isActive = activeTab === t.id;

        return (
          <button
            key={t.id}
            onClick={() => onSelectTab(t.id)}
            style={{
              background: 'transparent',
              border: 'none',
              color: isActive ? 'var(--accent-cyan)' : 'var(--text-muted)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '3px',
              fontSize: '0.68rem',
              fontWeight: isActive ? 700 : 500,
              cursor: 'pointer',
              flex: 1
            }}
          >
            <Icon size={20} color={isActive ? 'var(--accent-cyan)' : 'var(--text-muted)'} />
            <span>{t.label}</span>
          </button>
        );
      })}
    </div>
  );
}
