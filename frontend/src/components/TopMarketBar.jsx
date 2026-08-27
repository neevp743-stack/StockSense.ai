import React, { useEffect, useState } from 'react';
import { TrendingUp, TrendingDown, Radio, Info } from 'lucide-react';
import { api } from '../api';

const TICKER_CONFIG = [
  { symbol: 'NIFTY 50', apiKey: 'NIFTY 50', navTarget: 'RELIANCE' },
  { symbol: 'SENSEX', apiKey: 'SENSEX', navTarget: 'RELIANCE' },
  { symbol: 'NASDAQ', apiKey: 'NASDAQ', navTarget: 'AAPL' },
  { symbol: 'BTC/USD', apiKey: 'BTC-USD', navTarget: 'BTC-USD' },
  { symbol: 'S&P 500', apiKey: 'S&P 500', navTarget: 'AAPL' },
  { symbol: 'XAU/USD', apiKey: 'XAUUSD', navTarget: 'XAUUSD' },
  { symbol: 'RELIANCE', apiKey: 'RELIANCE', navTarget: 'RELIANCE' }
];

export function TopMarketBar({ onSelectTicker }) {
  const [tickerData, setTickerData] = useState({});
  const [overallStatus, setOverallStatus] = useState("CHECKING");

  const fetchTickerData = async () => {
    const recvTime = new Date().toISOString();
    const nextData = {};

    let hasLiveFeed = false;

    await Promise.all(TICKER_CONFIG.map(async (item) => {
      try {
        const res = await api.getRealtimeQuote(item.apiKey);
        const data = res?.data || res;
        
        if (data && data.price !== undefined && data.price !== null) {
          const sourceTs = data.timestamp || data.time || recvTime;
          const sourceDate = new Date(sourceTs);
          const recvDate = new Date(recvTime);
          const ageSeconds = Math.max(0, Math.round((recvDate.getTime() - sourceDate.getTime()) / 1000));
          const isLive = data.data_status === 'LIVE' || data.data_status === 'READY';
          if (isLive) hasLiveFeed = true;

          nextData[item.symbol] = {
            available: true,
            price: typeof data.price === 'number' ? data.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : String(data.price),
            change: data.change_percent ? `${data.change_percent >= 0 ? '+' : ''}${data.change_percent.toFixed(2)}%` : (data.change ? String(data.change) : '0.00%'),
            isPos: data.change_percent !== undefined ? data.change_percent >= 0 : true,
            provider: data.provider || 'API_ROUTER',
            sourceTimestamp: sourceTs,
            receivedTimestamp: recvTime,
            freshnessAgeSeconds: ageSeconds,
            status: isLive ? 'LIVE' : (data.data_status || 'STALE')
          };
        } else {
          nextData[item.symbol] = {
            available: false,
            price: 'NO LIVE DATA',
            change: 'N/A',
            isPos: false,
            provider: 'UNAVAILABLE',
            sourceTimestamp: 'N/A',
            receivedTimestamp: recvTime,
            freshnessAgeSeconds: 0,
            status: 'NO LIVE DATA'
          };
        }
      } catch (err) {
        nextData[item.symbol] = {
          available: false,
          price: 'NO LIVE DATA',
          change: 'N/A',
          isPos: false,
          provider: 'UNAVAILABLE',
          sourceTimestamp: 'N/A',
          receivedTimestamp: recvTime,
          freshnessAgeSeconds: 0,
          status: 'NO LIVE DATA'
        };
      }
    }));

    setTickerData(nextData);
    setOverallStatus(hasLiveFeed ? "LIVE" : "DEGRADED");
  };

  useEffect(() => {
    fetchTickerData();
    const intervalId = setInterval(fetchTickerData, 10000);
    return () => clearInterval(intervalId);
  }, []);

  let statusColor = "var(--down-red)";
  let statusText = "NO LIVE DATA ● FEED DOWN";

  if (overallStatus === "LIVE") {
    statusColor = "var(--up-green)";
    statusText = "REALTIME ● LIVE DATA";
  } else if (overallStatus === "DEGRADED") {
    statusColor = "#f59e0b";
    statusText = "PARTIAL FEED ● DEGRADED";
  }

  return (
    <div 
      style={{ 
        background: '#090d16', 
        borderBottom: '1px solid var(--border-color)',
        padding: '6px 20px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        overflowX: 'auto',
        whiteSpace: 'nowrap',
        fontSize: '0.78rem',
        scrollbarWidth: 'none',
        gap: '24px'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)', flexShrink: 0 }}>
        <Radio size={12} color={statusColor} className={overallStatus === "LIVE" ? "spin" : ""} />
        <span style={{ fontWeight: 700, letterSpacing: '0.05em', color: 'var(--text-secondary)' }}>MARKET TICKER</span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '20px', flexGrow: 1 }}>
        {TICKER_CONFIG.map((config) => {
          const t = tickerData[config.symbol] || {
            available: false,
            price: 'NO LIVE DATA',
            change: 'N/A',
            isPos: false,
            provider: 'UNAVAILABLE',
            sourceTimestamp: 'N/A',
            receivedTimestamp: 'N/A',
            freshnessAgeSeconds: 0,
            status: 'NO LIVE DATA'
          };

          const tooltipTxt = `Provider: ${t.provider} | Source TS: ${t.sourceTimestamp} | Recv TS: ${t.receivedTimestamp} | Freshness: ${t.freshnessAgeSeconds}s | Status: ${t.status}`;

          return (
            <div 
              key={config.symbol} 
              onClick={() => onSelectTicker && onSelectTicker(config.navTarget)}
              title={tooltipTxt}
              style={{ 
                display: 'inline-flex', 
                alignItems: 'center', 
                gap: '6px',
                cursor: 'pointer',
                padding: '2px 8px',
                borderRadius: '6px',
                transition: 'background 0.2s'
              }}
              className="hover-bg"
            >
              <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{config.symbol}</span>
              
              {t.available ? (
                <>
                  <span className="mono-font" style={{ color: 'var(--text-secondary)' }}>{t.price}</span>
                  <span 
                    className="mono-font" 
                    style={{ 
                      color: t.isPos ? 'var(--up-green)' : 'var(--down-red)',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '2px',
                      fontWeight: 600
                    }}
                  >
                    {t.isPos ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                    {t.change}
                  </span>
                  <span style={{ fontSize: '0.65rem', color: t.status === 'LIVE' ? 'var(--up-green)' : '#f59e0b', padding: '1px 4px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px' }}>
                    {t.provider} ({t.freshnessAgeSeconds}s)
                  </span>
                </>
              ) : (
                <span className="mono-font" style={{ color: 'var(--down-red)', fontSize: '0.74rem', fontWeight: 600 }}>
                  NO LIVE DATA
                </span>
              )}
            </div>
          );
        })}
      </div>

      <div style={{ color: statusColor, fontSize: '0.74rem', flexShrink: 0 }} className="mono-font">
        {statusText}
      </div>
    </div>
  );
}
