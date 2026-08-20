import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { StockChart } from './components/StockChart';
import { AdvancedStockChart } from './components/AdvancedStockChart';
import { PredictionCard } from './components/PredictionCard';
import { SystemStatusBanner } from './components/SystemStatusBanner';


import { ExplanationCard } from './components/ExplanationCard';
import { ModelLeaderboard } from './components/ModelLeaderboard';
import { PredictionHistory } from './components/PredictionHistory';
import { BacktesterUI } from './components/BacktesterUI';
import { LiveResearchPage } from './components/LiveResearchPage';
import ResearchStudy from './components/ResearchStudy';
import { api } from './api';

export default function App() {

  const [selectedAssetClass, setSelectedAssetClass] = useState('INDIAN_EQUITY');
  const [availableAssets, setAvailableAssets] = useState([]);
  const [selectedAsset, setSelectedAsset] = useState('RELIANCE');
  const [selectedModel, setSelectedModel] = useState('XGBoost');

  const [historyData, setHistoryData] = useState([]);
  const [predictionData, setPredictionData] = useState(null);
  const [performanceData, setPerformanceData] = useState(null);
  const [predictionsHistory, setPredictionsHistory] = useState([]);

  const [isRefreshing, setIsRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState('dashboard'); // 'dashboard', 'leaderboard', 'tracking', 'backtest', 'ablation'

  // Load assets whenever asset class changes
  useEffect(() => {
    loadAssetsForClass(selectedAssetClass);
  }, [selectedAssetClass]);

  // Load asset data on asset change or model change
  useEffect(() => {
    if (selectedAsset) {
      loadStockData(selectedAsset, selectedModel);
    }
  }, [selectedAsset, selectedModel]);

  useEffect(() => {
    loadGlobalMetrics();
  }, []);

  const loadAssetsForClass = async (cls) => {
    try {
      const res = await api.getAssets(cls);
      const assetsList = res.data.assets || [];
      setAvailableAssets(assetsList);
      if (assetsList.length > 0) {
        setSelectedAsset(assetsList[0].symbol);
      }
    } catch (err) {
      console.error("Failed to load assets for class:", err);
    }
  };

  const loadStockData = async (symbol, modelName) => {
    try {
      const [histRes, predRes] = await Promise.all([
        api.getHistory(symbol).catch(() => ({ data: { data: [] } })),
        api.getPrediction(symbol, modelName).catch(() => ({ data: null }))
      ]);

      setHistoryData(histRes.data.data || []);
      setPredictionData(predRes.data);
    } catch (err) {
      console.error("Failed to load asset data:", err);
    }
  };

  const loadGlobalMetrics = async () => {
    try {
      const [perfRes, logsRes] = await Promise.all([
        api.getPerformance().catch(() => ({ data: null })),
        api.getPredictionsHistory('', 50).catch(() => ({ data: { predictions: [] } }))
      ]);

      setPerformanceData(perfRes.data);
      setPredictionsHistory(logsRes.data.predictions || []);
    } catch (err) {
      console.error("Failed to load global metrics:", err);
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await api.triggerRefresh();
      setTimeout(() => {
        loadStockData(selectedAsset, selectedModel);
        loadGlobalMetrics();
        setIsRefreshing(false);
      }, 3000);
    } catch (err) {
      console.error("Refresh failed:", err);
      setIsRefreshing(false);
    }
  };

  return (
    <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '24px 20px' }}>
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
      />

      <SystemStatusBanner />


      {/* Navigation Tabs */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '24px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px', flexWrap: 'wrap' }}>
        <button 
          className={`btn-secondary ${activeTab === 'dashboard' ? 'active' : ''}`}
          onClick={() => setActiveTab('dashboard')}
        >
          📊 Asset Overview & Predictions
        </button>
        <button 
          className={`btn-secondary ${activeTab === 'ablation' ? 'active' : ''}`}
          onClick={() => setActiveTab('ablation')}
        >
          🧪 Feature Study & Ablation
        </button>
        <button 
          className={`btn-secondary ${activeTab === 'leaderboard' ? 'active' : ''}`}
          onClick={() => setActiveTab('leaderboard')}
        >
          🏆 Model Evaluation Leaderboard
        </button>
        <button 
          className={`btn-secondary ${activeTab === 'tracking' ? 'active' : ''}`}
          onClick={() => setActiveTab('tracking')}
        >
          📜 Prediction Resolution Log
        </button>
        <button 
          className={`btn-secondary ${activeTab === 'backtest' ? 'active' : ''}`}
          onClick={() => setActiveTab('backtest')}
        >
          ⚡ Research Backtester
        </button>
      </div>

      {/* Main Tab Content */}
      {activeTab === 'dashboard' && (
        <>
          <AdvancedStockChart historyData={historyData} symbol={selectedAsset} predictionData={predictionData} />

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '24px', marginBottom: '24px' }}>
            <PredictionCard
              prediction={predictionData}
              symbol={selectedAsset}
              selectedModel={selectedModel}
              onSelectModel={setSelectedModel}
            />
            <ExplanationCard explanations={predictionData?.explanations} />
          </div>
        </>
      )}


      {activeTab === 'ablation' && (
        <ResearchStudy symbol={selectedAsset} />
      )}

      {activeTab === 'live-research' && (
        <LiveResearchPage activeSymbol={selectedAsset} onSelectSymbol={setSelectedAsset} />
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


      {/* Footer */}
      <footer style={{ marginTop: '40px', paddingTop: '20px', borderTop: '1px solid var(--border-color)', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
        StockSense AI — Multi-Asset Machine Learning Research Platform | Predict. Explain. Verify. | Educational Market Prediction Evaluation
      </footer>
    </div>
  );
}
