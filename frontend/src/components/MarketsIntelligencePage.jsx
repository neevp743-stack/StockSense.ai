import React, { useEffect, useRef, useState } from 'react';
import { createChart, ColorType, CandlestickSeries, HistogramSeries, LineSeries } from 'lightweight-charts';
import { api, getWebSocketUrl } from '../api';
import { 
  TrendingUp, TrendingDown, Info, Shield, Zap, AlertCircle, Loader2, BarChart2, Eye, Award, CheckCircle
} from 'lucide-react';

// Helper utilities for chart series adding
function addCandleSeries(chart, options) {
  if (typeof chart.addCandlestickSeries === 'function') {
    return chart.addCandlestickSeries(options);
  }
  return chart.addSeries(CandlestickSeries, options);
}

function addHistoSeries(chart, options) {
  if (typeof chart.addHistogramSeries === 'function') {
    return chart.addHistogramSeries(options);
  }
  return chart.addSeries(HistogramSeries, options);
}

function addLineSeries(chart, options) {
  if (typeof chart.addLineSeries === 'function') {
    return chart.addLineSeries(options);
  }
  return chart.addSeries(LineSeries, options);
}

export function MarketsIntelligencePage() {
  const [selectedAsset, setSelectedAsset] = useState('BTC-USD');
  const [interval, setInterval] = useState('1h');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Backend data
  const [analysisData, setAnalysisData] = useState(null);
  const [livePrice, setLivePrice] = useState(null);
  const [priceFlashClass, setPriceFlashClass] = useState('');
  
  // Overlay Toggles
  const [overlays, setOverlays] = useState({
    ema9: true,
    ema21: false,
    ema50: false,
    ema200: false,
    bb: false,
    structure: true,
    fvg: false
  });

  // Chart references
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);
  const candleSeriesRef = useRef(null);
  const volumeSeriesRef = useRef(null);
  
  const ema9SeriesRef = useRef(null);
  const ema21SeriesRef = useRef(null);
  const ema50SeriesRef = useRef(null);
  const ema200SeriesRef = useRef(null);
  const bbUpperSeriesRef = useRef(null);
  const bbLowerSeriesRef = useRef(null);
  
  const lastCandleRef = useRef(null);
  const prevPriceRef = useRef(null);

  // Timeframe switch triggers reload
  useEffect(() => {
    loadIntelligence();
  }, [selectedAsset, interval]);

  // Load backend intelligence aggregates
  const loadIntelligence = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getMarketAnalysis(selectedAsset, interval, 300);
      if (res.data && !res.data.error) {
        setAnalysisData(res.data);
        setLivePrice(res.data.quote?.price || null);
        prevPriceRef.current = res.data.quote?.price || null;
      } else {
        setError(res.data?.error || "Failed to load market intelligence analytics.");
      }
    } catch (err) {
      console.error("Error loading intelligence:", err);
      setError("Market data provider is currently offline or rate-limited. Please retry shortly.");
    } finally {
      setLoading(false);
    }
  };

  // Real-time quote WebSocket proxy connection
  useEffect(() => {
    if (!selectedAsset) return;
    
    let ws = null;
    try {
      const wsUrl = getWebSocketUrl(selectedAsset);
      ws = new WebSocket(wsUrl);
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data && data.price) {
            const newPrice = Number(data.price);
            
            // Trigger visual price flashing green/red on changes
            if (prevPriceRef.current !== null && prevPriceRef.current !== newPrice) {
              const isUp = newPrice > prevPriceRef.current;
              setPriceFlashClass(isUp ? 'tick-flash-up' : 'tick-flash-down');
              setTimeout(() => setPriceFlashClass(''), 600);
            }
            
            prevPriceRef.current = newPrice;
            setLivePrice(newPrice);
            
            // Update last candle in lightweight-charts
            if (candleSeriesRef.current && lastCandleRef.current) {
              const last = lastCandleRef.current;
              const updatedCandle = {
                ...last,
                high: Math.max(last.high, newPrice),
                low: Math.min(last.low, newPrice),
                close: newPrice
              };
              candleSeriesRef.current.update(updatedCandle);
              lastCandleRef.current = updatedCandle;
            }
          }
        } catch (err) {
          // Silent parse fallback
        }
      };
    } catch (err) {
      console.error("WS connection failed:", err);
    }

    return () => {
      if (ws) ws.close();
    };
  }, [selectedAsset]);

  // Initializing TradingView Lightweight Chart canvas
  useEffect(() => {
    if (loading || error || !analysisData || !chartContainerRef.current) return;

    const width = chartContainerRef.current.clientWidth || 800;
    const height = 450;

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#0d131f' },
        textColor: '#94a3b8',
        fontSize: 12,
        fontFamily: 'var(--font-body)'
      },
      grid: {
        vertLines: { color: 'rgba(255, 255, 255, 0.03)' },
        horzLines: { color: 'rgba(255, 255, 255, 0.03)' },
      },
      crosshair: { mode: 1 },
      rightPriceScale: { borderColor: 'rgba(255, 255, 255, 0.08)' },
      timeScale: { borderColor: 'rgba(255, 255, 255, 0.08)', timeVisible: true },
      width: width,
      height: height,
    });

    chartRef.current = chart;

    // Candlesticks
    const candleSeries = addCandleSeries(chart, {
      upColor: '#10b981',
      downColor: '#ef4444',
      borderVisible: false,
      wickUpColor: '#10b981',
      wickDownColor: '#ef4444',
    });
    candleSeriesRef.current = candleSeries;

    // Volume Histogram
    const volumeSeries = addHistoSeries(chart, {
      color: 'rgba(56, 189, 248, 0.25)',
      priceFormat: { type: 'volume' },
      priceScaleId: '',
      scaleMargins: { top: 0.8, bottom: 0 },
    });
    volumeSeriesRef.current = volumeSeries;

    // Format and Set Candle Data
    const formattedCandles = analysisData.candles || [];
    if (formattedCandles.length > 0) {
      candleSeries.setData(formattedCandles.map(c => ({
        time: c.time,
        open: c.open,
        high: c.high,
        low: c.low,
        close: c.close
      })));

      volumeSeries.setData(formattedCandles.map(c => ({
        time: c.time,
        value: c.volume,
        color: c.close >= c.open ? 'rgba(16, 185, 129, 0.25)' : 'rgba(239, 68, 68, 0.25)'
      })));

      lastCandleRef.current = {
        ...formattedCandles[formattedCandles.length - 1],
        time: formattedCandles[formattedCandles.length - 1].time
      };
    }

    // Overlays Initializations
    if (overlays.ema9) {
      ema9SeriesRef.current = addLineSeries(chart, { color: '#38bdf8', lineWidth: 1.5 });
      // Calculate simple EMA locally for plotting if backend returns arrays
      const ema9Data = calculateEMA(formattedCandles, 9);
      ema9SeriesRef.current.setData(ema9Data);
    }
    if (overlays.ema21) {
      ema21SeriesRef.current = addLineSeries(chart, { color: '#a855f7', lineWidth: 1.5 });
      const ema21Data = calculateEMA(formattedCandles, 21);
      ema21SeriesRef.current.setData(ema21Data);
    }
    if (overlays.ema50) {
      ema50SeriesRef.current = addLineSeries(chart, { color: '#eab308', lineWidth: 1.5 });
      const ema50Data = calculateEMA(formattedCandles, 50);
      ema50SeriesRef.current.setData(ema50Data);
    }
    if (overlays.ema200) {
      ema200SeriesRef.current = addLineSeries(chart, { color: '#ec4899', lineWidth: 1.5 });
      const ema200Data = calculateEMA(formattedCandles, 200);
      ema200SeriesRef.current.setData(ema200Data);
    }

    if (overlays.bb) {
      bbUpperSeriesRef.current = addLineSeries(chart, { color: 'rgba(0, 242, 254, 0.35)', lineWidth: 1, lineStyle: 2 });
      bbLowerSeriesRef.current = addLineSeries(chart, { color: 'rgba(0, 242, 254, 0.35)', lineWidth: 1, lineStyle: 2 });
      
      const bbData = calculateBollingerBands(formattedCandles, 20, 2);
      bbUpperSeriesRef.current.setData(bbData.upper);
      bbLowerSeriesRef.current.setData(bbData.lower);
    }

    // Handle Resize
    const handleResize = () => {
      if (chartRef.current && chartContainerRef.current) {
        chartRef.current.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }
    };
  }, [loading, error, analysisData, overlays]);

  // Technical calculations client-side helpers
  function calculateEMA(candles, period) {
    if (candles.length < period) return [];
    const k = 2 / (period + 1);
    let emaVal = candles.slice(0, period).reduce((sum, c) => sum + c.close, 0) / period;
    const results = [{ time: candles[period - 1].time, value: emaVal }];
    
    for (let i = period; i < candles.length; i++) {
      emaVal = (candles[i].close * k) + (emaVal * (1 - k));
      results.push({ time: candles[i].time, value: emaVal });
    }
    return results;
  }

  function calculateBollingerBands(candles, period, stdDev) {
    if (candles.length < period) return { upper: [], lower: [] };
    const upper = [];
    const lower = [];
    
    for (let i = period - 1; i < candles.length; i++) {
      const slice = candles.slice(i - period + 1, i + 1);
      const sma = slice.reduce((sum, c) => sum + c.close, 0) / period;
      const variance = slice.reduce((sum, c) => sum + Math.pow(c.close - sma, 2), 0) / period;
      const std = Math.sqrt(variance);
      
      upper.push({ time: candles[i].time, value: sma + stdDev * std });
      lower.push({ time: candles[i].time, value: sma - stdDev * std });
    }
    return { upper, lower };
  }

  const getFreshnessBadge = (status) => {
    switch (status) {
      case 'LIVE':
        return <span style={{ background: '#10b981', color: '#fff', fontSize: '0.72rem', fontWeight: 800, padding: '3px 8px', borderRadius: '20px' }}>LIVE</span>;
      case 'RECENT':
        return <span style={{ background: '#38bdf8', color: '#fff', fontSize: '0.72rem', fontWeight: 800, padding: '3px 8px', borderRadius: '20px' }}>RECENT</span>;
      case 'STALE':
        return <span style={{ background: '#f59e0b', color: '#fff', fontSize: '0.72rem', fontWeight: 800, padding: '3px 8px', borderRadius: '20px' }}>STALE</span>;
      default:
        return <span style={{ background: '#ef4444', color: '#fff', fontSize: '0.72rem', fontWeight: 800, padding: '3px 8px', borderRadius: '20px' }}>OFFLINE</span>;
    }
  };

  const getRegimeColor = (regime) => {
    if (regime === 'TRENDING_BULLISH') return '#10b981';
    if (regime === 'TRENDING_BEARISH') return '#ef4444';
    return '#8b5cf6';
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      {/* 1. Header cockpit */}
      <div className="glass-card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        
        {/* Switcher assets */}
        <div style={{ display: 'flex', gap: '8px' }}>
          {['BTC-USD', 'SOL-USD', 'XAU/USD'].map(asset => (
            <button
              key={asset}
              className={`btn-secondary ${selectedAsset === asset ? 'active' : ''}`}
              onClick={() => setSelectedAsset(asset)}
              style={{
                fontSize: '0.9rem',
                fontWeight: 700,
                padding: '10px 18px',
                borderRadius: '8px',
                border: '1px solid var(--border-color)'
              }}
            >
              {asset === 'XAU/USD' ? '🔥 XAU/USD (Gold)' : asset}
            </button>
          ))}
        </div>

        {/* Timeframe picker */}
        <div style={{ display: 'flex', gap: '4px', background: 'var(--bg-primary)', padding: '4px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
          {['5m', '15m', '30m', '1h', '4h', '1d', '1w'].map(tf => (
            <button
              key={tf}
              onClick={() => setInterval(tf)}
              style={{
                background: interval === tf ? 'var(--bg-card-hover)' : 'transparent',
                color: interval === tf ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                border: 'none',
                padding: '6px 12px',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '0.8rem',
                fontWeight: 600
              }}
            >
              {tf.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* 2. Metadata Banner */}
      {!loading && !error && analysisData && (
        <div className="glass-card" style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '20px', padding: '16px 24px' }}>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Asset / Price</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginTop: '4px' }}>
              <span className={`heading-font ${priceFlashClass}`} style={{ fontSize: '1.8rem', fontWeight: 800 }}>
                ${livePrice ? Number(livePrice).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 4 }) : '---'}
              </span>
              {getFreshnessBadge(analysisData.quote?.data_status)}
            </div>
          </div>

          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Market Regime</div>
            <div style={{ color: getRegimeColor(analysisData.regime), fontWeight: 800, fontSize: '1.1rem', marginTop: '6px', letterSpacing: '0.04em' }}>
              {analysisData.regime?.replace('_', ' ')}
            </div>
          </div>

          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Data Feed</div>
            <div style={{ marginTop: '6px', fontSize: '0.9rem', fontWeight: 600 }}>
              {analysisData.provider} REST
            </div>
          </div>

          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Last Update</div>
            <div className="mono-font" style={{ marginTop: '6px', fontSize: '0.82rem', color: 'var(--text-muted)' }}>
              {analysisData.quote?.timestamp ? new Date(analysisData.quote.timestamp).toLocaleTimeString() : '---'}
            </div>
          </div>
        </div>
      )}

      {/* Main Workspace layout */}
      {loading ? (
        <div className="glass-card" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
          <div style={{ textAlign: 'center' }}>
            <Loader2 className="spin" size={48} color="var(--accent-cyan)" />
            <div style={{ marginTop: '16px', color: 'var(--text-secondary)' }}>Executing technical and market-structure mathematical models...</div>
          </div>
        </div>
      ) : error ? (
        <div className="glass-card" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '300px', borderColor: 'var(--down-red)' }}>
          <div style={{ textAlign: 'center', color: 'var(--down-red)' }}>
            <AlertCircle size={48} />
            <div style={{ marginTop: '16px', fontWeight: 700 }}>{error}</div>
            <button className="btn-primary" onClick={loadIntelligence} style={{ marginTop: '16px' }}>Retry Connection</button>
          </div>
        </div>
      ) : (
        <div className="responsive-grid-2col" style={{ display: 'grid', gridTemplateColumns: '3fr 1.25fr', gap: '20px' }}>
          
          {/* Left panel: chart & overlays */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div className="glass-card" style={{ position: 'relative', overflow: 'hidden' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <BarChart2 size={18} color="var(--accent-cyan)" />
                  <span className="heading-font" style={{ fontWeight: 700 }}>Lightweight Candlestick & Volume Chart</span>
                </div>

                {/* Overlay Checkboxes */}
                <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.74rem', cursor: 'pointer', color: 'var(--text-secondary)' }}>
                    <input type="checkbox" checked={overlays.ema9} onChange={(e) => setOverlays({ ...overlays, ema9: e.target.checked })} />
                    EMA 9
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.74rem', cursor: 'pointer', color: 'var(--text-secondary)' }}>
                    <input type="checkbox" checked={overlays.ema21} onChange={(e) => setOverlays({ ...overlays, ema21: e.target.checked })} />
                    EMA 21
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.74rem', cursor: 'pointer', color: 'var(--text-secondary)' }}>
                    <input type="checkbox" checked={overlays.ema50} onChange={(e) => setOverlays({ ...overlays, ema50: e.target.checked })} />
                    EMA 50
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.74rem', cursor: 'pointer', color: 'var(--text-secondary)' }}>
                    <input type="checkbox" checked={overlays.ema200} onChange={(e) => setOverlays({ ...overlays, ema200: e.target.checked })} />
                    EMA 200
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.74rem', cursor: 'pointer', color: 'var(--text-secondary)' }}>
                    <input type="checkbox" checked={overlays.bb} onChange={(e) => setOverlays({ ...overlays, bb: e.target.checked })} />
                    Bollinger
                  </label>
                </div>
              </div>

              {/* TradingView Chart Container */}
              <div ref={chartContainerRef} style={{ width: '100%', height: '450px', background: '#0d131f', borderRadius: '10px' }} />
            </div>

            {/* Overlays Detail Indicator panels */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
              <div className="glass-card">
                <div style={{ fontSize: '0.9rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '6px', borderBottom: '1px solid var(--border-color)', paddingBottom: '10px', marginBottom: '10px' }}>
                  <Zap size={15} color="var(--accent-cyan)" />
                  <span>Technical Indicators & Oscillators</span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.84rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>RSI (14)</span>
                    <span className="mono-font" style={{ fontWeight: 700 }}>{analysisData.indicators?.rsi_14}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>MACD Line</span>
                    <span className="mono-font" style={{ fontWeight: 700 }}>{analysisData.indicators?.macd_line}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>MACD Signal</span>
                    <span className="mono-font" style={{ fontWeight: 700 }}>{analysisData.indicators?.macd_signal}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>ATR (14)</span>
                    <span className="mono-font" style={{ fontWeight: 700 }}>{analysisData.indicators?.atr_14}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Relative Vol</span>
                    <span className="mono-font" style={{ fontWeight: 700 }}>{analysisData.indicators?.relative_volume}x</span>
                  </div>
                </div>
              </div>

              <div className="glass-card">
                <div style={{ fontSize: '0.9rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '6px', borderBottom: '1px solid var(--border-color)', paddingBottom: '10px', marginBottom: '10px' }}>
                  <Eye size={15} color="var(--accent-purple)" />
                  <span>Liquidity & Gaps Engine</span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.84rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Last Sweep</span>
                    <span className="mono-font" style={{ color: analysisData.liquidity?.last_sweep_direction === 'BULLISH' ? '#10b981' : (analysisData.liquidity?.last_sweep_direction === 'BEARISH' ? '#ef4444' : 'var(--text-muted)'), fontWeight: 700 }}>
                      {analysisData.liquidity?.last_sweep_direction}
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Unmitigated Gaps (FVG)</span>
                    <span className="mono-font" style={{ fontWeight: 700 }}>{analysisData.liquidity?.unmitigated_bullish_fvgs + analysisData.liquidity?.unmitigated_bearish_fvgs}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Active Order Blocks</span>
                    <span className="mono-font" style={{ fontWeight: 700 }}>{analysisData.liquidity?.unmitigated_bullish_obs + analysisData.liquidity?.unmitigated_bearish_obs}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Confirmed High Swing</span>
                    <span className="mono-font" style={{ fontWeight: 700 }}>${analysisData.structure?.swing_high}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Confirmed Low Swing</span>
                    <span className="mono-font" style={{ fontWeight: 700 }}>${analysisData.structure?.swing_low}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Right panel: confluence & setup details */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            
            {/* Confluence scoring card */}
            <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-color)', paddingBottom: '10px' }}>
                <span className="heading-font" style={{ fontWeight: 700, display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Award size={16} color="var(--accent-cyan)" />
                  Confluence Analysis
                </span>
                <span className="mono-font" style={{ background: 'var(--bg-primary)', padding: '4px 10px', borderRadius: '6px', fontWeight: 800, color: 'var(--accent-cyan)' }}>
                  {analysisData.confluence?.score}/100
                </span>
              </div>

              {/* Progress gauge */}
              <div style={{ background: 'rgba(255,255,255,0.03)', height: '8px', borderRadius: '4px', overflow: 'hidden' }}>
                <div style={{ background: 'var(--accent-cyan)', width: `${analysisData.confluence?.score}%`, height: '100%', boxShadow: '0 0 10px var(--accent-cyan)' }} />
              </div>

              {/* Confluence explanations list */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Confluence Arguments</div>
                
                {/* Positive signals */}
                {analysisData.confluence?.reasons?.map((reason, idx) => (
                  <div key={idx} style={{ display: 'flex', gap: '8px', fontSize: '0.78rem', color: '#fff', alignItems: 'flex-start' }}>
                    <span style={{ color: '#10b981', fontWeight: 700 }}>✓</span>
                    <span>{reason.replace(/^\+\s*/, '')}</span>
                  </div>
                ))}
                
                {/* Negative signals */}
                {analysisData.confluence?.penalties?.map((penalty, idx) => (
                  <div key={idx} style={{ display: 'flex', gap: '8px', fontSize: '0.78rem', color: 'var(--text-secondary)', alignItems: 'flex-start' }}>
                    <span style={{ color: '#ef4444', fontWeight: 700 }}>⚠</span>
                    <span>{penalty.replace(/^-\s*/, '')}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Setup card */}
            <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '14px', border: analysisData.setup?.bias !== 'NO QUALIFIED SETUP' ? '1px solid rgba(0, 242, 254, 0.25)' : '1px solid var(--border-color)' }}>
              <div className="heading-font" style={{ fontWeight: 800, display: 'flex', alignItems: 'center', gap: '6px', borderBottom: '1px solid var(--border-color)', paddingBottom: '10px' }}>
                <CheckCircle size={16} color="var(--accent-cyan)" />
                Market Setup Signal
              </div>
              
              <div style={{
                textAlign: 'center',
                padding: '12px',
                borderRadius: '8px',
                background: 'var(--bg-primary)',
                fontWeight: 800,
                fontSize: '1rem',
                color: analysisData.setup?.bias.includes('LONG') ? '#10b981' : (analysisData.setup?.bias.includes('SHORT') ? '#ef4444' : 'var(--text-muted)'),
                boxShadow: analysisData.setup?.bias.includes('LONG') ? '0 0 15px rgba(16, 185, 129, 0.1)' : (analysisData.setup?.bias.includes('SHORT') ? '0 0 15px rgba(239, 68, 68, 0.1)' : 'none')
              }}>
                {analysisData.setup?.bias}
              </div>

              {analysisData.setup?.bias !== 'NO QUALIFIED SETUP' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '0.84rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '6px' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Entry Zone</span>
                    <span className="mono-font" style={{ fontWeight: 700 }}>{analysisData.setup?.entry_zone}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '6px' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Stop Loss / Invalidation</span>
                    <span className="mono-font" style={{ fontWeight: 700, color: '#ef4444' }}>${analysisData.setup?.stop_loss}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '6px' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Take Profit 1</span>
                    <span className="mono-font" style={{ fontWeight: 700, color: '#10b981' }}>${analysisData.setup?.tp1}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '6px' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Take Profit 2</span>
                    <span className="mono-font" style={{ fontWeight: 700, color: '#10b981' }}>${analysisData.setup?.tp2}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Risk / Reward Ratio</span>
                    <span className="mono-font" style={{ fontWeight: 700 }}>{analysisData.setup?.rr}:1</span>
                  </div>
                </div>
              )}

              {/* Research warning */}
              <div style={{
                background: 'rgba(245, 158, 11, 0.05)',
                border: '1px solid rgba(245, 158, 11, 0.15)',
                borderRadius: '8px',
                padding: '10px',
                fontSize: '0.72rem',
                color: '#f59e0b',
                display: 'flex',
                gap: '8px',
                lineHeight: '1.4'
              }}>
                <Info size={16} style={{ flexShrink: 0 }} />
                <span>
                  <strong>RESEARCH BIAS ONLY:</strong> This is a deterministic structural confluence signal calculated for quantitative academic evaluation. It does NOT guarantee future price outcomes and is NOT financial advice.
                </span>
              </div>
            </div>

          </div>

        </div>
      )}

    </div>
  );
}
