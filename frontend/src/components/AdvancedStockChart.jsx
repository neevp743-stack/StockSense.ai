import React, { useEffect, useRef, useState } from 'react';
import { createChart, ColorType, CandlestickSeries, HistogramSeries, LineSeries } from 'lightweight-charts';
import { ChartDrawingToolbar } from './ChartDrawingToolbar';
import { ChartAnalysisPanel } from './ChartAnalysisPanel';
import { TechnicalAnalysisCard } from './TechnicalAnalysisCard';
import { 
  calcSMA, calcEMA, calcVWAP, calcBollinger 
} from '../utils/technicalIndicators';
import { api, getWebSocketUrl } from '../api';
import { formatPrice } from '../utils/formatters';
import { Radio, Maximize2, Minimize2, Sliders, TrendingUp, TrendingDown } from 'lucide-react';

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

function addLSeries(chart, options) {
  if (typeof chart.addLineSeries === 'function') {
    return chart.addLineSeries(options);
  }
  return chart.addSeries(LineSeries, options);
}

export function AdvancedStockChart({ symbol = "RELIANCE", historyData = [], predictionData = null }) {
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);
  const candleSeriesRef = useRef(null);
  const volumeSeriesRef = useRef(null);
  const indicatorSeriesRef = useRef([]);

  const [timeframe, setTimeframe] = useState('1D');
  const [liveTick, setLiveTick] = useState(null);
  const [activeTool, setActiveTool] = useState('pointer');
  const [drawings, setDrawings] = useState([]);
  const [priceFlashClass, setPriceFlashClass] = useState('');
  const prevPriceRef = useRef(null);

  // Indicator Toggles
  const [indicators, setIndicators] = useState({
    sma: true,
    ema: false,
    vwap: true,
    bollinger: false,
  });

  const [techAnalysis, setTechAnalysis] = useState(null);
  const [supportResistance, setSupportResistance] = useState(null);

  useEffect(() => {
    if (!symbol) return;
    setTechAnalysis(null);
    setSupportResistance(null);

    const controller = new AbortController();
    const { signal } = controller;

    api.getTechnicalAnalysis(symbol, { signal })
      .then(res => {
        setTechAnalysis(res.data?.latest_indicators || null);
        setSupportResistance({
          support_levels: res.data?.support_levels || [],
          resistance_levels: res.data?.resistance_levels || []
        });
      })
      .catch(() => {});

    return () => { controller.abort(); };
  }, [symbol]);

  // Real-time WebSocket Subscription with Tick Directional Flash Animation
  useEffect(() => {
    if (!symbol) return;
    setLiveTick(null);
    const wsUrl = getWebSocketUrl(symbol);
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data && data.price && (!data.symbol || data.symbol.toUpperCase() === symbol.toUpperCase())) {
          const newPrice = data.price;
          
          if (prevPriceRef.current !== null && prevPriceRef.current !== newPrice) {
            const isUp = newPrice > prevPriceRef.current;
            setPriceFlashClass(isUp ? 'tick-flash-up' : 'tick-flash-down');
            setTimeout(() => setPriceFlashClass(''), 800);
          }
          prevPriceRef.current = newPrice;
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

    if (chartRef.current) {
      chartRef.current.remove();
      chartRef.current = null;
    }

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#070a11' },
        textColor: '#94a3b8',
        fontSize: 12,
        fontFamily: 'var(--font-body)'
      },
      grid: {
        vertLines: { color: 'rgba(255, 255, 255, 0.04)' },
        horzLines: { color: 'rgba(255, 255, 255, 0.04)' },
      },
      crosshair: {
        mode: 1,
      },
      rightPriceScale: {
        borderColor: 'rgba(255, 255, 255, 0.08)',
      },
      timeScale: {
        borderColor: 'rgba(255, 255, 255, 0.08)',
        timeVisible: true,
      },
      width: chartContainerRef.current.clientWidth,
      height: 520,
    });

    chartRef.current = chart;

    // Candlestick Series
    const candleSeries = addCandleSeries(chart, {
      upColor: '#10b981',
      downColor: '#ef4444',
      borderVisible: false,
      wickUpColor: '#10b981',
      wickDownColor: '#ef4444',
    });
    candleSeriesRef.current = candleSeries;

    // Volume Series
    const volumeSeries = addHistoSeries(chart, {
      color: '#26a69a',
      priceFormat: { type: 'volume' },
      priceScaleId: '',
      scaleMargins: { top: 0.82, bottom: 0 },
    });
    volumeSeriesRef.current = volumeSeries;

    const uniqueCandles = new Map();
    const uniqueVolume = new Map();

    historyData.forEach(d => {
      if (!d || !d.date) return;
      const dateStr = typeof d.date === 'string' ? d.date.split('T')[0] : (d.date.isoformat ? d.date.isoformat().split('T')[0] : String(d.date));
      const closePrice = parseFloat(d.close);
      if (dateStr && !isNaN(closePrice)) {
        uniqueCandles.set(dateStr, {
          time: dateStr,
          open: parseFloat(d.open),
          high: parseFloat(d.high),
          low: parseFloat(d.low),
          close: closePrice,
        });
        uniqueVolume.set(dateStr, {
          time: dateStr,
          value: parseFloat(d.volume || 0),
          color: closePrice >= parseFloat(d.open) ? 'rgba(16, 185, 129, 0.35)' : 'rgba(239, 68, 68, 0.35)'
        });
      }
    });

    const formattedCandles = Array.from(uniqueCandles.values()).sort((a, b) => (a.time > b.time ? 1 : -1));
    const formattedVolume = Array.from(uniqueVolume.values()).sort((a, b) => (a.time > b.time ? 1 : -1));

    if (formattedCandles.length > 0) {
      candleSeries.setData(formattedCandles);
      volumeSeries.setData(formattedVolume);
    }

    // Render Overlay Indicators
    indicatorSeriesRef.current = [];

    if (indicators.sma && formattedCandles.length > 20) {
      const smaData = calcSMA(formattedCandles, 20);
      const smaLine = addLSeries(chart, { color: '#00f2fe', lineWidth: 2, title: 'SMA 20' });
      smaLine.setData(smaData);
      indicatorSeriesRef.current.push(smaLine);
    }

    if (indicators.ema && formattedCandles.length > 12) {
      const emaData = calcEMA(formattedCandles, 12);
      const emaLine = addLSeries(chart, { color: '#f59e0b', lineWidth: 2, title: 'EMA 12' });
      emaLine.setData(emaData);
      indicatorSeriesRef.current.push(emaLine);
    }

    if (indicators.vwap && formattedCandles.length > 0) {
      const vwapData = calcVWAP(formattedCandles);
      const vwapLine = addLSeries(chart, { color: '#a855f7', lineWidth: 1.5, title: 'VWAP' });
      vwapLine.setData(vwapData);
      indicatorSeriesRef.current.push(vwapLine);
    }

    if (indicators.bollinger && formattedCandles.length > 20) {
      const { upper, middle, lower } = calcBollinger(formattedCandles, 20, 2);
      const uLine = addLSeries(chart, { color: 'rgba(244, 63, 94, 0.6)', lineWidth: 1, title: 'BB Upper' });
      const mLine = addLSeries(chart, { color: 'rgba(244, 63, 94, 0.4)', lineWidth: 1, title: 'BB Mid' });
      const lLine = addLSeries(chart, { color: 'rgba(244, 63, 94, 0.6)', lineWidth: 1, title: 'BB Lower' });
      uLine.setData(upper);
      mLine.setData(middle);
      lLine.setData(lower);
      indicatorSeriesRef.current.push(uLine, mLine, lLine);
    }

    chart.timeScale().fitContent();

    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };
    window.addEventListener('resize', handleResize);

    const resizeObserver = new ResizeObserver(() => handleResize());
    if (chartContainerRef.current) resizeObserver.observe(chartContainerRef.current);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (resizeObserver) resizeObserver.disconnect();
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }
    };
  }, [historyData, indicators]);

  const validLiveTick = (liveTick && liveTick.symbol && liveTick.symbol.toUpperCase() === symbol.toUpperCase()) ? liveTick : null;
  const validPredictionData = (predictionData && predictionData.symbol && predictionData.symbol.toUpperCase() === symbol.toUpperCase()) ? predictionData : null;

  const latestPriceVal = validLiveTick?.price || (historyData.length > 0 ? historyData[historyData.length - 1].close : (validPredictionData?.latest_price || 0));
  const prevPriceVal = historyData.length > 1 ? historyData[historyData.length - 2].close : latestPriceVal;
  const priceChange = latestPriceVal - prevPriceVal;
  const pctChange = prevPriceVal !== 0 ? (priceChange / prevPriceVal) * 100 : 0;
  const isPos = priceChange >= 0;

  const dataStatus = validLiveTick?.data_status || validPredictionData?.quote_info?.data_status || "HISTORICAL";
  const providerName = validLiveTick?.provider || validPredictionData?.quote_info?.provider || "Finnhub";

  const toggleIndicator = (name) => {
    setIndicators(prev => ({ ...prev, [name]: !prev[name] }));
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', marginBottom: '24px' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '20px' }}>
        {/* Dominant Stock Chart View */}
        <div className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          
          {/* Header Stock Info Bar */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <h2 className="heading-font" style={{ fontSize: '1.65rem', fontWeight: 800, color: '#fff' }}>{symbol}</h2>
                <span className="badge badge-up" style={{ fontSize: '0.74rem' }}>
                  <Radio size={12} className="spin" /> LIVE ● {providerName}
                </span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginTop: '6px' }}>
                <span 
                  className={`mono-font ${priceFlashClass}`} 
                  style={{ fontSize: '1.75rem', fontWeight: 800, padding: '2px 8px', borderRadius: '6px', transition: 'all 0.3s' }}
                >
                  {formatPrice(latestPriceVal, symbol)}
                </span>

                <span 
                  className="mono-font" 
                  style={{ 
                    fontSize: '0.95rem', 
                    fontWeight: 700, 
                    color: isPos ? 'var(--up-green)' : 'var(--down-red)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px'
                  }}
                >
                  {isPos ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                  {isPos ? '+' : ''}{priceChange.toFixed(2)} ({isPos ? '+' : ''}{pctChange.toFixed(2)}%)
                </span>

                <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                  Updated 0.2s ago
                </span>
              </div>
            </div>

            {/* Timeframe Controls: [1D] [1W] [1M] [3M] [6M] [1Y] [5Y] */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px', background: 'var(--bg-secondary)', padding: '4px', borderRadius: '10px', border: '1px solid var(--border-color)' }}>
              {['1D', '1W', '1M', '3M', '6M', '1Y', '5Y'].map((tf) => (
                <button
                  key={tf}
                  onClick={() => setTimeframe(tf)}
                  style={{
                    padding: '6px 12px', fontSize: '0.8rem', fontWeight: 700, border: 'none',
                    borderRadius: '7px', background: timeframe === tf ? 'var(--accent-cyan)' : 'transparent',
                    color: timeframe === tf ? '#000' : 'var(--text-secondary)', cursor: 'pointer',
                    transition: 'all 0.15s'
                  }}
                >
                  {tf}
                </button>
              ))}
            </div>
          </div>

          {/* Indicators Bar */}
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
                  padding: '3px 10px', borderRadius: '6px', fontWeight: 700, cursor: 'pointer',
                  textTransform: 'uppercase'
                }}
              >
                {indKey}
              </button>
            ))}
          </div>

          {/* Main Trading Terminal Canvas */}
          <div style={{ display: 'flex', gap: '12px', position: 'relative' }}>
            <ChartDrawingToolbar
              activeTool={activeTool}
              onSelectTool={setActiveTool}
              onClearDrawings={() => setDrawings([])}
              drawingsCount={drawings.length}
            />

            <div style={{ position: 'relative', flexGrow: 1 }}>
              <div ref={chartContainerRef} style={{ width: '100%', height: '520px', borderRadius: '10px', overflow: 'hidden' }} />

              {predictionData?.predicted_direction && (
                <div style={{
                  position: 'absolute', top: '16px', right: '16px', zIndex: 10,
                  background: predictionData.predicted_direction === 'UP' ? 'rgba(16, 185, 129, 0.9)' : 'rgba(239, 68, 68, 0.9)',
                  color: '#fff', padding: '6px 14px', borderRadius: '12px', fontSize: '0.82rem', fontWeight: 800,
                  boxShadow: '0 4px 14px rgba(0,0,0,0.4)', backdropFilter: 'blur(8px)', display: 'flex', alignItems: 'center', gap: '6px'
                }}>
                  AI DIRECTION → {predictionData.predicted_direction} ({(predictionData.probability_up * 100).toFixed(1)}%)
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Terminal Analysis Panel */}
        <ChartAnalysisPanel
          symbol={symbol}
          prediction={predictionData}
          indicators={techAnalysis}
          supportResistance={supportResistance}
        />
      </div>

      {/* Technical Analysis Visual Signal Gauges */}
      <TechnicalAnalysisCard 
        indicators={techAnalysis} 
        symbol={symbol} 
        latestPrice={latestPriceVal} 
      />
    </div>
  );
}
