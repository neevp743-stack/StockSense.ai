import React from 'react';
import { MousePointer, Minus, Sliders, Type, Trash2, ArrowUpRight, ShieldAlert, Layers } from 'lucide-react';

export function ChartDrawingToolbar({ activeTool, onSelectTool, onClearDrawings, drawingsCount }) {
  const tools = [
    { id: 'pointer', label: 'Cursor', icon: <MousePointer size={16} /> },
    { id: 'trendline', label: 'Trend Line', icon: <ArrowUpRight size={16} /> },
    { id: 'hline', label: 'Horizontal Line', icon: <Minus size={16} /> },
    { id: 'fibonacci', label: 'Fibonacci Retracement', icon: <Sliders size={16} /> },
    { id: 'supres', label: 'Support/Resistance Level', icon: <Layers size={16} /> },
    { id: 'text', label: 'Text Note', icon: <Type size={16} /> },
  ];

  return (
    <div style={{
      display: 'flex', flexDirection: 'column', gap: '6px',
      background: 'var(--bg-secondary)', padding: '8px', borderRadius: '12px',
      border: '1px solid var(--border-color)', width: '48px', flexShrink: 0
    }}>
      {tools.map((tool) => {
        const isActive = activeTool === tool.id;
        return (
          <button
            key={tool.id}
            title={tool.label}
            onClick={() => onSelectTool(tool.id)}
            style={{
              width: '32px', height: '32px', borderRadius: '8px', border: 'none',
              background: isActive ? 'var(--accent-cyan)' : 'transparent',
              color: isActive ? '#000' : 'var(--text-secondary)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              cursor: 'pointer', transition: 'all 0.2s'
            }}
          >
            {tool.icon}
          </button>
        );
      })}

      <div style={{ height: '1px', background: 'var(--border-color)', margin: '4px 0' }} />

      <button
        title={`Clear ${drawingsCount} Drawings`}
        onClick={onClearDrawings}
        disabled={drawingsCount === 0}
        style={{
          width: '32px', height: '32px', borderRadius: '8px', border: 'none',
          background: 'transparent', color: drawingsCount > 0 ? 'var(--down-red)' : 'var(--text-muted)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          cursor: drawingsCount > 0 ? 'pointer' : 'not-allowed', opacity: drawingsCount > 0 ? 1 : 0.4
        }}
      >
        <Trash2 size={16} />
      </button>
    </div>
  );
}
