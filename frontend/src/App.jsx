import React, { useState, useEffect, useRef, Suspense, lazy } from 'react';
import { Header } from './components/Header';
import { TopMarketBar } from './components/TopMarketBar';
import { DashboardHero } from './components/DashboardHero';
import { Watchlist } from './components/Watchlist';
import { AdvancedStockChart } from './components/AdvancedStockChart';
import { PredictionCard } from './components/PredictionCard';
import { ExplanationCard } from './components/ExplanationCard';
import { TradeSetupPanel } from './components/TradeSetupPanel';
import { PatternAnalysisCard } from './components/PatternAnalysisCard';
import { ProductionMonitor } from './components/ProductionMonitor';
import { Phase18ShadowMonitor } from './components/Phase18ShadowMonitor';
import { Phase19AMonitor } from './components/Phase19AMonitor';
import Phase19DecisionDashboard from './components/Phase19DecisionDashboard';
import { SystemStatusBanner } from './components/SystemStatusBanner';



import { SplashScreen } from './components/SplashScreen';
import { SearchModal } from './components/SearchModal';
import { MobileNav } from './components/MobileNav';
import { ChartSkeleton, PredictionSkeleton } from './components/SkeletonLoaders';
import { ErrorFallbackCard } from './components/EmptyState';
import { api } from './api';

// Code-splitting heavy research & market universe modules
const MarketsPage = lazy(() => import('./components/MarketsPage').then(m => ({ default: m.MarketsPage })));
const LiveResearchPage = lazy(() => import('./components/LiveResearchPage').then(m => ({ default: m.LiveResearchPage })));
const BacktesterUI = lazy(() => import('./components/BacktesterUI').then(m => ({ default: m.BacktesterUI })));
const ResearchStudy = lazy(() => import('./components/ResearchStudy'));
const ModelLeaderboard = lazy(() => import('./components/ModelLeaderboard').then(m => ({ default: m.ModelLeaderboard })));
const PredictionHistory = lazy(() => import('./components/PredictionHistory').then(m => ({ default: m.PredictionHistory })));

export default function App() {
  const [showSplash, setShowSplash] = useState(true);
  const [selectedAssetClass, setSelectedAssetClass] = useState('INDIAN_EQUITY');
  const [availableAssets, setAvailableAssets] = useState([]);
  const [selectedAsset, setSelectedAsset] = useState('RELIANCE');
  const [selectedModel, setSelectedModel] = useState('XGBoost');

  const [historyData, setHistoryData] = useState([]);
  const [predictionData, setPredictionData] = useState(null);
  const [performanceData, setPerformanceData] = useState(null);
  const [predictionsHistory, setPredictionsHistory] = useState([]);

  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [dataError, setDataError] = useState(null);

  // Global Keyboard Listener for '/' Search Shortcut
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === '/' && !isSearchOpen && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'SELECT') {
        e.preventDefault();
        setIsSearchOpen(true);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isSearchOpen]);

  useEffect(() => {
    loadAssetsForClass(selectedAssetClass);
  }, [selectedAssetClass]);

  const symbolCacheRef = useRef({});

  // Preload stock data & predictions with Stale-While-Revalidate Client Caching
  useEffect(() => {
    if (!selectedAsset) return;

    const controller = new AbortController();
    const { signal } = controller;

    const cleanSymbol = selectedAsset.toUpperCase().strip ? selectedAsset.toUpperCase().strip() : selectedAsset.toUpperCase();
    const cacheKey = `${cleanSymbol}_${selectedModel}`;
    const cached = symbolCacheRef.current[cacheKey];

    // If cached in client memory, render immediately while revalidating in background
    if (cached) {
      setHistoryData(cached.history || []);
      setPredictionData(cached.prediction || null);
      setDataError(null);
    } else {
      setHistoryData([]);
      setPredictionData(null);
      setDataError(null);
    }

    api.getDashboardData(selectedAsset, selectedModel, { signal })
      .then(res => {
        const dashData = res.data;
        if (dashData) {
          const newHist = dashData.history?.data || [];
          const newPred = dashData.prediction || null;

          setHistoryData(newHist);
          setPredictionData(newPred);

          symbolCacheRef.current[cacheKey] = {
            history: newHist,
            prediction: newPred,
            timestamp: Date.now()
          };
        }
      })
      .catch(err => {
        if (err?.name !== 'CanceledError' && err?.name !== 'AbortError') {
          if (!cached) {
            console.error("Failed to load dashboard data:", err);
            setDataError(`Connecting to live market feed for '${selectedAsset}'...`);
          }
        }
      });

    return () => controller.abort();
  }, [selectedAsset, selectedModel]);

  useEffect(() => {
    loadGlobalMetrics();
  }, []);

  const loadAssetsForClass = async (cls) => {
    try {
      const res = await api.getAssets(cls);
      const assetsList = res.data.assets || [];
      setAvailableAssets(assetsList);
    } catch (err) {
      console.error("Failed to load assets for class:", err);
    }
  };

  const loadGlobalMetrics = async () => {
    try {
      const [perfRes, logsRes] = await Promise.all([
        api.getPerformance().catch(() => ({ data: null })),
        api.getPredictionsHistory('', 50).catch(() => ({ data: { predictions: [] } }))
      ]);
      setPerformanceData(perfRes.data);
      setPredictionsHistory(logsRes.data?.predictions || []);
    } catch (err) {
      console.error("Failed to load global metrics:", err);
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await api.triggerRefresh();
      setTimeout(() => {
        loadAssetsForClass(selectedAssetClass);
        loadGlobalMetrics();
        setIsRefreshing(false);
      }, 2500);
    } catch (err) {
      console.error("Refresh failed:", err);
      setIsRefreshing(false);
    }
  };

  const handleSelectSymbolAndSwitchTab = (sym) => {
    setSelectedAsset(sym);
    setActiveTab('dashboard');
  };

  return (
    <>
      {/* Smart Startup Splash Screen (~1.2s max, preloads data concurrently) */}
      {showSplash && <SplashScreen onFinish={() => setShowSplash(false)} />}

      {/* Top Benchmark Market Ticker Bar */}
      <TopMarketBar onSelectTicker={handleSelectSymbolAndSwitchTab} />

      <div className="app-container">
        {/* Navigation Header */}
        <Header
          assetClasses={["INDIAN_EQUITY", "US_EQUITY", "CRYPTO", "FOREX", "INDEX"]}
          selectedAssetClass={selectedAssetClass}
          onSelectAssetClass={setSelectedAssetClass}
          availableAssets={availableAssets}
          selectedAsset={selectedAsset}
          onSelectAsset={setSelectedAsset}
          onRefresh={handleRefresh}
          isRefreshing={isRefreshing}
          activeTab={activeTab}
          onSelectTab={setActiveTab}
          onOpenSearch={() => setIsSearchOpen(true)}
        />

        {/* System Health Status Bar */}
        <SystemStatusBanner />

        {/* Error Fallback Banner if API fails */}
        {dataError && (
          <ErrorFallbackCard 
            title="Market Data Reconnecting..." 
            message={dataError} 
            onRetry={() => loadAssetsForClass(selectedAssetClass)} 
          />
        )}

        {/* Main Tab Content */}
        {activeTab === 'dashboard' && (
          <>
            {/* Dashboard Hero */}
            <DashboardHero 
              onOpenSearch={() => setIsSearchOpen(true)} 
              selectedSymbol={selectedAsset}
              onSelectSymbol={setSelectedAsset}
            />

            {/* Watchlist Quick Switcher */}
            <Watchlist 
              selectedSymbol={selectedAsset} 
              onSelectSymbol={setSelectedAsset} 
              onOpenSearch={() => setIsSearchOpen(true)}
            />

            {/* Dominant Chart View */}
            {historyData.length > 0 ? (
              <AdvancedStockChart 
                historyData={historyData} 
                symbol={selectedAsset} 
                predictionData={predictionData} 
              />
            ) : (
              <ChartSkeleton />
            )}

            {/* AI Direction & Explainability Grid */}
            <div className="responsive-grid-2col">
              {predictionData ? (
                <PredictionCard
                  prediction={predictionData}
                  symbol={selectedAsset}
                  selectedModel={selectedModel}
                  onSelectModel={setSelectedModel}
                />
              ) : (
                <PredictionSkeleton />
              )}

              <ExplanationCard explanations={predictionData?.explanations} />
            </div>

            {/* Phase 14 AI Trade Setup Panel */}
            <div style={{ marginTop: '24px' }}>
              <TradeSetupPanel symbol={selectedAsset} />
            </div>

            {/* Phase 16 Production Monitor & Live Validation */}
            <div style={{ marginTop: '24px' }}>
              <ProductionMonitor symbol={selectedAsset} />
            </div>

            {/* Phase 18 Shadow Forward Validation Monitor */}
            <div style={{ marginTop: '24px' }}>
              <Phase18ShadowMonitor symbol={selectedAsset} />
            </div>

            {/* Phase 19A Live Data Pipeline & Diagnostic Monitor */}
            <div style={{ marginTop: '24px' }}>
              <Phase19AMonitor symbol={selectedAsset} />
            </div>

            {/* Phase 19 Forward Decision Support Dashboard */}
            <div style={{ marginTop: '24px' }}>
              <Phase19DecisionDashboard />
            </div>

            {/* Phase 15 Research Pattern Analysis Card */}
            <div style={{ marginTop: '24px' }}>
              <PatternAnalysisCard symbol={selectedAsset} />
            </div>

          </>
        )}



        {/* Lazy Loaded Market Universe & Research Tabs */}
        <Suspense fallback={<ChartSkeleton />}>
          {activeTab === 'markets' && (
            <MarketsPage onSelectSymbol={handleSelectSymbolAndSwitchTab} />
          )}

          {activeTab === 'live-research' && (
            <LiveResearchPage activeSymbol={selectedAsset} onSelectSymbol={setSelectedAsset} />
          )}

          {activeTab === 'ablation' && (
            <ResearchStudy symbol={selectedAsset} />
          )}

          {activeTab === 'leaderboard' && (
            <ModelLeaderboard performanceData={performanceData} symbol={selectedAsset} />
          )}

          {activeTab === 'tracking' && (
            <PredictionHistory predictions={predictionsHistory} symbol={selectedAsset} />
          )}

          {activeTab === 'backtest' && (
            <BacktesterUI symbol={selectedAsset} />
          )}
        </Suspense>

        {/* Global Search Overlay Modal */}
        <SearchModal 
          isOpen={isSearchOpen} 
          onClose={() => setIsSearchOpen(false)} 
          onSelectAsset={handleSelectSymbolAndSwitchTab} 
        />

        {/* Mobile Navigation Bar */}
        <MobileNav activeTab={activeTab} onSelectTab={setActiveTab} />

        {/* Footer */}
        <footer style={{ marginTop: '50px', paddingTop: '24px', borderTop: '1px solid var(--border-color)', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8rem', lineHeight: '1.6' }}>
          <div>StockSense AI — Scalable Multi-Asset Machine Learning Platform | Predict. Explain. Verify.</div>
          <div style={{ fontSize: '0.74rem', opacity: 0.7, marginTop: '4px' }}>
            Assets dynamically loaded on-demand via provider feeds. Not financial advice. Powered by Finnhub Realtime & XGBoost ML.
          </div>
        </footer>
      </div>
    </>
  );
}
