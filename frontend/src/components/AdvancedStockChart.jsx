import React, { useEffect, useRef, useState } from 'react';
import { createChart, ColorType } from 'lightweight-charts';
import { ChartDrawingToolbar } from './ChartDrawingToolbar';
import { ChartAnalysisPanel } from './ChartAnalysisPanel';
import { 
  calcSMA, calcEMA, calcVWAP, calcRSI, calcMACD, calcBollinger, detectSupportResistance 
} from '../utils/technicalIndicators';
import { api, getWebSocketUrl } from '../api';
import { Radio, Maximize2, Minimize2, Sliders, Eye, EyeOff } from 'lucide-react';

export function AdvancedStockChart({ symbol = "BTC-USD", historyData = [], predictionData = null }) {
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);
  const candleSeriesRef = useRef(null);
  const volumeSeriesRef = useRef(null);
  const indicatorSeriesRef = useRef([]);

  const [timeframe, setTimeframe] = useState('1D');
  const [liveTick, setLiveTick] = useState(null);
  const [activeTool, setActiveTool] = useState('pointer');
  const [drawings, setDrawings] = useState([]);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Indicator Toggles & Settings
  const [indicators, setIndicators] = useState({
    sma: true,
    ema: false,
    vwap: true,
    bollinger: false,
    rsi: false,
    macd: false,
  });

  const [techAnalysis, setTechAnalysis] = useState(null);
  const [supportResistance, setSupportResistance] = useState(null);

  // Fetch backend technical analysis on symbol change
  useEffect(() => {
    if (!symbol) return;
    api.getTechnicalAnalysis(symbol)
      .then(res => {
        setTechAnalysis(res.data?.latest_indicators || null);
        setSupportResistance({
          support_levels: res.data?.support_levels || [],
          resistance_levels: res.data?.resistance_levels || []
        });
      })
      .catch(() => {});
  }, [symbol]);

  // Real-time WebSocket Subscription
  useEffect(() => {
    if (!symbol) return;
    const wsUrl = getWebSocketUrl(symbol);
    const ws = new WebSocket(wsUrl);


    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data && data.price) {
          setLiveTick(data);
          // Update lightweight-charts live candle
          if (candleSeriesRef.current) {
            const timeStr = data.timestamp ? data.timestamp.split('T')[0] : new Date().toISOString().split('T')[0];
            candleSeriesRef.current.update({
              time: timeStr,
              open: data.price,
              high: data.price,
              low: data.price,
              close: data.price
            });
          }
        }
      } catch (err) {
        console.error("Error parsing WS tick:", err);
      }
    };

    return () => ws.close();
  }, [symbol]);

  // Lightweight-Charts Initialization
  useEffect(() => {
    if (!chartContainerRef.current || !historyData || historyData.length === 0) return;

    // Clean up existing chart
    if (chartRef.current) {
      chartRef.current.remove();
    }

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#0f172a' },
        textColor: '#94a3b8',
      },
      grid: {
        vertLines: { color: 'rgba(255, 255, 255, 0.05)' },
        horzLines: { color: 'rgba(255, 255, 255, 0.05)' },
      },
      crosshair: {
        mode: 1,
      },
      rightPriceScale: {
        borderColor: 'rgba(255, 255, 255, 0.1)',
      },
      timeScale: {
        borderColor: 'rgba(255, 255, 255, 0.1)',
        timeVisible: true,
      },
      width: chartContainerRef.current.clientWidth,
      height: 480,
    });

    chartRef.current = chart;

    // Candlestick Series
    const candleSeries = chart.addCandlestickSeries({
      upColor: '#10b981',
      downColor: '#ef4444',
      borderVisible: false,
      wickUpColor: '#10b981',
      wickDownColor: '#ef4444',
    });
    candleSeriesRef.current = candleSeries;

    // Volume Series
    const volumeSeries = chart.addHistogramSeries({
      color: '#26a69a',
      priceFormat: { type: 'volume' },
      priceScaleId: '', // Set as overlay
      scaleMargins: { top: 0.8, bottom: 0 },
    });
    volumeSeriesRef.current = volumeSeries;

    // Format data for lightweight-charts
    const formattedCandles = historyData.map(d => ({
      time: typeof d.date === 'string' ? d.date.split('T')[0] : d.date,
      open: parseFloat(d.open),
      high: parseFloat(d.high),
      low: parseFloat(d.low),
      close: parseFloat(d.close),
    })).filter(c => c.time && !isNaN(c.close)).sort((a, b) => (a.time > b.time ? 1 : -1));

    const formattedVolume = historyData.map(d => ({
      time: typeof d.date === 'string' ? d.date.split('T')[0] : d.date,
      value: parseFloat(d.volume || 0),
      color: parseFloat(d.close) >= parseFloat(d.open) ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'
    })).filter(v => v.time && !isNaN(v.value)).sort((a, b) => (a.time > b.time ? 1 : -1));

    candleSeries.setData(formattedCandles);
    volumeSeries.setData(formattedVolume);

    // Render Overlay Indicators
    indicatorSeriesRef.current = [];

    if (indicators.sma && formattedCandles.length > 20) {
      const smaData = calcSMA(formattedCandles, 20);
      const smaLine = chart.addLineSeries({ color: '#00f2fe', lineWidth: 2, title: 'SMA 20' });
      smaLine.setData(smaData);
      indicatorSeriesRef.current.push(smaLine);
    }

    if (indicators.ema && formattedCandles.length > 12) {
      const emaData = calcEMA(formattedCandles, 12);
      const emaLine = chart.addLineSeries({ color: '#f59e0b', lineWidth: 2, title: 'EMA 12' });
      emaLine.setData(emaData);
      indicatorSeriesRef.current.push(emaLine);
    }

    if (indicators.vwap && formattedCandles.length > 0) {
      const vwapData = calcVWAP(formattedCandles);
      const vwapLine = chart.addLineSeries({ color: '#a855f7', lineWidth: 1.5, title: 'VWAP' });
      vwapLine.setData(vwapData);
      indicatorSeriesRef.current.push(vwapLine);
    }

    if (indicators.bollinger && formattedCandles.length > 20) {
      const { upper, middle, lower } = calcBollinger(formattedCandles, 20, 2);
      const uLine = chart.addLineSeries({ color: 'rgba(244, 63, 94, 0.6)', lineWidth: 1, title: 'BB Upper' });
      const mLine = chart.addLineSeries({ color: 'rgba(244, 63, 94, 0.4)', lineWidth: 1, title: 'BB Mid' });
      const lLine = chart.addLineSeries({ color: 'rgba(244, 63, 94, 0.6)', lineWidth: 1, title: 'BB Lower' });
      uLine.setData(upper);
      mLine.setData(middle);
      lLine.setData(lower);
      indicatorSeriesRef.current.push(uLine, mLine, lLine);
    }

    chart.timeScale().fitContent();

    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [historyData, indicators]);

  // Derived Header Metrics
  const latestPriceVal = liveTick?.price || (historyData.length > 0 ? historyData[historyData.length - 1].close : 0);
  const prevPriceVal = historyData.length > 1 ? historyData[historyData.length - 2].close : latestPriceVal;
  const priceChange = latestPriceVal - prevPriceVal;
  const pctChange = prevPriceVal !== 0 ? (priceChange / prevPriceVal) * 100 : 0;
  const isPos = priceChange >= 0;

  const dataStatus = liveTick?.data_status || predictionData?.quote_info?.data_status || "HISTORICAL";
  const providerName = liveTick?.provider || predictionData?.quote_info?.provider || "Finnhub";

  const statusBadgeStyle = 
    dataStatus === "LIVE" ? { bg: 'rgba(16, 185, 129, 0.15)', color: 'var(--up-green)', label: `🟢 LIVE (${providerName})` } :
    dataStatus === "DELAYED" ? { bg: 'rgba(245, 158, 11, 0.15)', color: '#f59e0b', label: '🟡 DELAYED' } :
    dataStatus === "STALE" ? { bg: 'rgba(239, 68, 68, 0.15)', color: 'var(--down-red)', label: '🔴 STALE' } :
    { bg: 'rgba(148, 163, 184, 0.15)', color: '#94a3b8', label: '⚪ HISTORICAL BAR' };

  const toggleIndicator = (name) => {
    setIndicators(prev => ({ ...prev, [name]: !prev[name] }));
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '20px', marginBottom: '24px' }}>
      {/* Left: Main TradingView Terminal Chart Area */}
      <div className="glass-card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
        
        {/* Terminal Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <h2 className="heading-font" style={{ fontSize: '1.4rem', fontWeight: 800 }}>{symbol}</h2>
              <span style={{ background: statusBadgeStyle.bg, color: statusBadgeStyle.color, border: `1px solid ${statusBadgeStyle.color}`, padding: '2px 8px', borderRadius: '12px', fontSize: '0.72rem', fontWeight: 700 }}>
                {statusBadgeStyle.label}
              </span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '4px' }}>
              <span className="mono-font" style={{ fontSize: '1.4rem', fontWeight: 800 }}>
                ${latestPriceVal ? latestPriceVal.toLocaleString('en-US', { minimumFractionDigits: 2 }) : 'N/A'}
              </span>
              <span className="mono-font" style={{ fontSize: '0.9rem', fontWeight: 700, color: isPos ? 'var(--up-green)' : 'var(--down-red)' }}>
                {isPos ? '+' : ''}{priceChange.toFixed(2)} ({isPos ? '+' : ''}{pctChange.toFixed(2)}%)
              </span>
            </div>
          </div>

          {/* Timeframe Selector & Fullscreen Toggle */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'var(--bg-secondary)', padding: '4px', borderRadius: '10px', border: '1px solid var(--border-color)' }}>
            {['1m', '5m', '15m', '1H', '1D', '1W'].map((tf) => (
              <button
                key={tf}
                onClick={() => setTimeframe(tf)}
                style={{
                  padding: '4px 10px', fontSize: '0.78rem', fontWeight: 700, border: 'none',
                  borderRadius: '6px', background: timeframe === tf ? 'var(--accent-cyan)' : 'transparent',
                  color: timeframe === tf ? '#000' : 'var(--text-secondary)', cursor: 'pointer'
                }}
              >
                {tf}
              </button>
            ))}
          </div>
        </div>

        {/* Technical Indicators Bar */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap', fontSize: '0.78rem', background: 'var(--bg-secondary)', padding: '6px 12px', borderRadius: '10px' }}>
          <span style={{ color: 'var(--text-muted)', fontWeight: 700 }}>INDICATORS:</span>
          {Object.keys(indicators).map(indKey => (
            <button
              key={indKey}
              onClick={() => toggleIndicator(indKey)}
              style={{
                background: indicators[indKey] ? 'rgba(0, 242, 254, 0.15)' : 'transparent',
                color: indicators[indKey] ? 'var(--accent-cyan)' : 'var(--text-muted)',
                border: `1px solid ${indicators[indKey] ? 'var(--accent-cyan)' : 'transparent'}`,
                padding: '2px 8px', borderRadius: '6px', fontWeight: 600, cursor: 'pointer',
                textTransform: 'uppercase'
              }}
            >
              {indKey}
            </button>
          ))}
        </div>

        {/* Main Chart Area with Drawing Toolbar Sidebar */}
        <div style={{ display: 'flex', gap: '12px', position: 'relative' }}>
          <ChartDrawingToolbar
            activeTool={activeTool}
            onSelectTool={setActiveTool}
            onClearDrawings={() => setDrawings([])}
            drawingsCount={drawings.length}
          />

          <div style={{ position: 'relative', flexGrow: 1 }}>
            <div ref={chartContainerRef} style={{ width: '100%', height: '480px', borderRadius: '8px', overflow: 'hidden' }} />

            {/* AI Prediction Marker Badge Overlay on Chart */}
            {predictionData?.predicted_direction && (
              <div style={{
                position: 'absolute', top: '16px', right: '16px', zIndex: 10,
                background: predictionData.predicted_direction === 'UP' ? 'rgba(16, 185, 129, 0.9)' : 'rgba(239, 68, 68, 0.9)',
                color: '#fff', padding: '6px 14px', borderRadius: '12px', fontSize: '0.82rem', fontWeight: 800,
                boxShadow: '0 4px 14px rgba(0,0,0,0.4)', backdropFilter: 'blur(8px)', display: 'flex', alignItems: 'center', gap: '6px'
              }}>
                AI → {predictionData.predicted_direction} (UP: {(predictionData.probability_up * 100).toFixed(1)}%)
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Right: Terminal Analysis Panel */}
      <ChartAnalysisPanel
        symbol={symbol}
        prediction={predictionData}
        indicators={techAnalysis}
        supportResistance={supportResistance}
      />
    </div>
  );
}
