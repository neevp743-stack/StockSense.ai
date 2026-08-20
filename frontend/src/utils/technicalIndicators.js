/**
 * StockSense AI — Technical Indicator Calculations
 * Provides client-side calculations for SMA, EMA, VWAP, RSI, MACD, Bollinger Bands,
 * ATR, Stochastic, OBV, and Support/Resistance levels for Lightweight Charts.
 */

export function calcSMA(data, period = 20) {
  const result = [];
  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) continue;
    let sum = 0;
    for (let j = 0; j < period; j++) {
      sum += data[i - j].close;
    }
    result.push({ time: data[i].time, value: sum / period });
  }
  return result;
}

export function calcEMA(data, period = 12) {
  const result = [];
  if (data.length < period) return result;
  
  const k = 2 / (period + 1);
  let prevEma = data.slice(0, period).reduce((acc, d) => acc + d.close, 0) / period;
  result.push({ time: data[period - 1].time, value: prevEma });

  for (let i = period; i < data.length; i++) {
    const currentEma = (data[i].close * k) + (prevEma * (1 - k));
    result.push({ time: data[i].time, value: currentEma });
    prevEma = currentEma;
  }
  return result;
}

export function calcVWAP(data) {
  const result = [];
  let cumVol = 0;
  let cumTpVol = 0;

  for (let i = 0; i < data.length; i++) {
    const tp = (data[i].high + data[i].low + data[i].close) / 3;
    const vol = data[i].volume || 1;
    cumTpVol += tp * vol;
    cumVol += vol;
    result.push({ time: data[i].time, value: cumTpVol / cumVol });
  }
  return result;
}

export function calcRSI(data, period = 14) {
  const result = [];
  if (data.length < period + 1) return result;

  let gains = 0;
  let losses = 0;

  for (let i = 1; i <= period; i++) {
    const diff = data[i].close - data[i - 1].close;
    if (diff >= 0) gains += diff;
    else losses -= diff;
  }

  let avgGain = gains / period;
  let avgLoss = losses / period;

  let rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
  let rsi = 100 - (100 / (1 + rs));
  result.push({ time: data[period].time, value: rsi });

  for (let i = period + 1; i < data.length; i++) {
    const diff = data[i].close - data[i - 1].close;
    const currentGain = diff > 0 ? diff : 0;
    const currentLoss = diff < 0 ? -diff : 0;

    avgGain = (avgGain * (period - 1) + currentGain) / period;
    avgLoss = (avgLoss * (period - 1) + currentLoss) / period;

    rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
    rsi = 100 - (100 / (1 + rs));
    result.push({ time: data[i].time, value: rsi });
  }
  return result;
}

export function calcMACD(data, fast = 12, slow = 26, signal = 9) {
  const fastEma = calcEMA(data, fast);
  const slowEma = calcEMA(data, slow);
  
  const macdLine = [];
  const slowMap = new Map(slowEma.map(d => [d.time, d.value]));

  for (let f of fastEma) {
    if (slowMap.has(f.time)) {
      macdLine.push({ time: f.time, close: f.value - slowMap.get(f.time) });
    }
  }

  const signalLine = calcEMA(macdLine, signal);
  const signalMap = new Map(signalLine.map(d => [d.time, d.value]));

  const macdSeries = [];
  const signalSeries = [];
  const histSeries = [];

  for (let m of macdLine) {
    if (signalMap.has(m.time)) {
      const sigVal = signalMap.get(m.time);
      macdSeries.push({ time: m.time, value: m.close });
      signalSeries.push({ time: m.time, value: sigVal });
      histSeries.push({ 
        time: m.time, 
        value: m.close - sigVal, 
        color: (m.close - sigVal) >= 0 ? '#10b981' : '#ef4444' 
      });
    }
  }

  return { macdSeries, signalSeries, histSeries };
}

export function calcBollinger(data, period = 20, stdDev = 2) {
  const upper = [];
  const middle = [];
  const lower = [];

  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) continue;
    const slice = data.slice(i - period + 1, i + 1);
    const mean = slice.reduce((acc, d) => acc + d.close, 0) / period;
    const variance = slice.reduce((acc, d) => acc + Math.pow(d.close - mean, 2), 0) / period;
    const sd = Math.sqrt(variance);

    middle.push({ time: data[i].time, value: mean });
    upper.push({ time: data[i].time, value: mean + (sd * stdDev) });
    lower.push({ time: data[i].time, value: mean - (sd * stdDev) });
  }

  return { upper, middle, lower };
}

export function detectSupportResistance(data, window = 5) {
  if (!data || data.length < window * 2) {
    return { support: [], resistance: [] };
  }

  const highs = [];
  const lows = [];
  const currentPrice = data[data.length - 1].close;

  for (let i = window; i < data.length - window; i++) {
    let isHigh = true;
    let isLow = true;
    for (let j = i - window; j <= i + window; j++) {
      if (j === i) continue;
      if (data[j].high > data[i].high) isHigh = false;
      if (data[j].low < data[i].low) isLow = false;
    }
    if (isHigh) highs.push(data[i].high);
    if (isLow) lows.push(data[i].low);
  }

  const resistance = [...new Set(highs.filter(p => p > currentPrice))].sort((a, b) => a - b).slice(0, 3);
  const support = [...new Set(lows.filter(p => p < currentPrice))].sort((a, b) => b - a).slice(0, 3);

  return { support, resistance, currentPrice };
}
