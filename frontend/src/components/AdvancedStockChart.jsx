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
import { Radio, Sliders, TrendingUp, TrendingDown } from 'lucide-react';

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
  const indicatorSeriesRefs = useRef({});

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

  // Fetch Technical Analysis Gauges
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

  // Real-time WebSocket Subscription
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

          // Lightweight update on latest candle without full re-render
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

  // 1. Initialize Chart Canvas Instance ONCE
  useEffect(() => {
    if (!chartContainerRef.current) return;

    if (!chartRef.current) {
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
        crosshair: { mode: 1 },
        rightPriceScale: { borderColor: 'rgba(255, 255, 255, 0.08)' },
        timeScale: { borderColor: 'rgba(255, 255, 255, 0.08)', timeVisible: true },
        width: chartContainerRef.current.clientWidth,
        height: 520,
      });

      chartRef.current = chart;

      candleSeriesRef.current = addCandleSeries(chart, {
        upColor: '#10b981',
        downColor: '#ef4444',
        borderVisible: false,
        wickUpColor: '#10b981',
        wickDownColor: '#ef4444',
      });

      volumeSeriesRef.current = addHistoSeries(chart, {
        color: '#26a69a',
        priceFormat: { type: 'volume' },
        priceScaleId: '',
        scaleMargins: { top: 0.82, bottom: 0 },
      });

      const resizeObserver = new ResizeObserver(entries => {
        if (entries[0] && chartRef.current) {
          chartRef.current.applyOptions({ width: entries[0].contentRect.width });
        }
      });
      resizeObserver.observe(chartContainerRef.current);

      return () => {
        resizeObserver.disconnect();
        if (chartRef.current) {
          chartRef.current.remove();
          chartRef.current = null;
        }
      };
    }
  }, []);

  // 2. Set Historical Candle & Volume Data ONLY when historyData changes
  useEffect(() => {
    if (!chartRef.current || !candleSeriesRef.current || !volumeSeriesRef.current || !historyData || historyData.length === 0) return;

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
      candleSeriesRef.current.setData(formattedCandles);
      volumeSeriesRef.current.setData(formattedVolume);
      chartRef.current.timeScale().fitContent();
    }
  }, [historyData, symbol]);

  // 3. Update Indicator Series Dynamically without destroying chart
  useEffect(() => {
    if (!chartRef.current || !historyData || historyData.length === 0) return;

    const uniqueCandles = new Map();
    historyData.forEach(d => {
      if (!d || !d.date) return;
      const dateStr = typeof d.date === 'string' ? d.date.split('T')[0] : String(d.date);
      const closePrice = parseFloat(d.close);
      if (dateStr && !isNaN(closePrice)) {
        uniqueCandles.set(dateStr, {
          time: dateStr,
          open: parseFloat(d.open),
          high: parseFloat(d.high),
          low: parseFloat(d.low),
          close: closePrice,
        });
      }
    });

    const formattedCandles = Array.from(uniqueCandles.values()).sort((a, b) => (a.time > b.time ? 1 : -1));
    const refs = indicatorSeriesRefs.current;

    // Helper to add or remove line series safely
    const syncSeries = (key, enabled, options, dataFn) => {
      if (enabled && formattedCandles.length > 0) {
        if (!refs[key]) {
          refs[key] = addLSeries(chartRef.current, options);
        }
        refs[key].setData(dataFn(formattedCandles));
      } else if (refs[key]) {
        chartRef.current.removeSeries(refs[key]);
        delete refs[key];
      }
    };

    syncSeries('sma', indicators.sma, { color: '#00f2fe', lineWidth: 2, title: 'SMA 20' }, c => calcSMA(c, 20));
    syncSeries('ema', indicators.ema, { color: '#f59e0b', lineWidth: 2, title: 'EMA 12' }, c => calcEMA(c, 12));
    syncSeries('vwap', indicators.vwap, { color: '#a855f7', lineWidth: 1.5, title: 'VWAP' }, c => calcVWAP(c));

    if (indicators.bollinger && formattedCandles.length > 20) {
      const { upper, middle, lower } = calcBollinger(formattedCandles, 20, 2);
      syncSeries('bb_upper', true, { color: 'rgba(244, 63, 94, 0.6)', lineWidth: 1, title: 'BB Upper' }, () => upper);
      syncSeries('bb_middle', true, { color: 'rgba(244, 63, 94, 0.4)', lineWidth: 1, title: 'BB Mid' }, () => middle);
      syncSeries('bb_lower', true, { color: 'rgba(244, 63, 94, 0.6)', lineWidth: 1, title: 'BB Lower' }, () => lower);
    } else {
      ['bb_upper', 'bb_middle', 'bb_lower'].forEach(k => {
        if (refs[k]) {
          chartRef.current.removeSeries(refs[k]);
          delete refs[k];
        }
      });
    }
  }, [indicators, historyData]);

  const validLiveTick = (liveTick && liveTick.symbol && liveTick.symbol.toUpperCase() === symbol.toUpperCase()) ? liveTick : null;
  const validPredictionData = (predictionData && predictionData.symbol && predictionData.symbol.toUpperCase() === symbol.toUpperCase()) ? predictionData : null;

  const latestPriceVal = validLiveTick?.price || (historyData.length > 0 ? historyData[historyData.length - 1].close : (validPredictionData?.latest_price || 0));
  const prevPriceVal = historyData.length > 1 ? historyData[historyData.length - 2].close : latestPriceVal;
  const priceChange = latestPriceVal - prevPriceVal;
  const pctChange = prevPriceVal !== 0 ? (priceChange / prevPriceVal) * 100 : 0;
  const isPos = priceChange >= 0;

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

                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.9rem', fontWeight: 700, color: isPos ? 'var(--up-green)' : 'var(--down-red)' }}>
                  {isPos ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                  <span>{isPos ? '+' : ''}{priceChange.toFixed(2)} ({pctChange.toFixed(2)}%)</span>
                </div>
              </div>
            </div>

            {/* Timeframe Buttons */}
            <div style={{ display: 'flex', gap: '4px', background: 'var(--bg-secondary)', padding: '4px', borderRadius: '10px', border: '1px solid var(--border-color)' }}>
              {['1D', '1W', '1M', '1Y', '5Y'].map(tf => (
                <button
                  key={tf}
                  onClick={() => setTimeframe(tf)}
                  className={`btn-secondary ${timeframe === tf ? 'active' : ''}`}
                  style={{ padding: '4px 10px', fontSize: '0.76rem', borderRadius: '6px' }}
                >
                  {tf}
                </button>
              ))}
            </div>
          </div>

          {/* Indicator Toggles Ribbon */}
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap', padding: '10px 14px', background: 'var(--bg-secondary)', borderRadius: '10px', border: '1px solid var(--border-color)' }}>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Sliders size={14} color="var(--accent-cyan)" /> OVERLAYS:
            </span>

            {[
              { id: 'sma', label: 'SMA 20', color: '#00f2fe' },
              { id: 'ema', label: 'EMA 12', color: '#f59e0b' },
              { id: 'vwap', label: 'VWAP', color: '#a855f7' },
              { id: 'bollinger', label: 'Bollinger Bands', color: '#f43f5e' },
            ].map(ind => (
              <button
                key={ind.id}
                onClick={() => toggleIndicator(ind.id)}
                style={{
                  background: indicators[ind.id] ? 'rgba(0, 242, 254, 0.12)' : 'transparent',
                  border: `1px solid ${indicators[ind.id] ? ind.color : 'var(--border-color)'}`,
                  color: indicators[ind.id] ? ind.color : 'var(--text-muted)',
                  padding: '4px 10px',
                  borderRadius: '6px',
                  fontSize: '0.76rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
              >
                {ind.label}
              </button>
            ))}
          </div>

          {/* Drawing Toolbar & Chart Canvas */}
          <div style={{ display: 'flex', gap: '12px' }}>
            <ChartDrawingToolbar 
              activeTool={activeTool}
              onSelectTool={setActiveTool}
              onClearDrawings={() => setDrawings([])}
            />

            <div style={{ flexGrow: 1, position: 'relative' }}>
              <div ref={chartContainerRef} style={{ width: '100%', height: '520px', borderRadius: '12px', overflow: 'hidden' }} />
            </div>
          </div>
        </div>

        {/* Technical Indicators & Support/Resistance Panel */}
        <TechnicalAnalysisCard indicators={techAnalysis} supportResistance={supportResistance} symbol={symbol} />
      </div>

      <ChartAnalysisPanel symbol={symbol} historyData={historyData} />
    </div>
  );
}
