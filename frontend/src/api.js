import axios from 'axios';

// Environment-aware API Base URL
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ||
  (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
    ? 'http://localhost:8000/api'
    : 'https://stocksense-ai-backend-sdyo.onrender.com/api');

export const BACKEND_ROOT_URL = API_BASE_URL.replace(/\/api\/?$/, '');

// Dynamic WebSocket URL generator based on backend protocol & host
export function getWebSocketUrl(symbol) {
  const cleanSymbol = encodeURIComponent(symbol.toUpperCase ? symbol.toUpperCase() : symbol);
  const isSecure = BACKEND_ROOT_URL.startsWith('https:');
  const wsProtocol = isSecure ? 'wss:' : 'ws:';
  const host = BACKEND_ROOT_URL.replace(/^https?:\/\//, '');
  return `${wsProtocol}//${host}/ws/market/${cleanSymbol}`;
}

export const api = {
  getAssetClasses: () => axios.get(`${API_BASE_URL}/asset-classes`),
  getAssets: (assetClass = '') => axios.get(`${API_BASE_URL}/assets`, { params: { asset_class: assetClass } }),
  getAssetDetail: (symbol) => axios.get(`${API_BASE_URL}/assets/${symbol}`),
  getUniverse: () => axios.get(`${API_BASE_URL}/stocks`),
  getHistory: (symbol) => axios.get(`${API_BASE_URL}/stocks/${symbol}/history`),
  getFeatures: (symbol) => axios.get(`${API_BASE_URL}/stocks/${symbol}/features`),
  getPrediction: (symbol, modelName = 'XGBoost') => 
    axios.get(`${API_BASE_URL}/stocks/${symbol}/prediction`, { params: { model_name: modelName } }),
  getModels: () => axios.get(`${API_BASE_URL}/models`),
  getPredictionsHistory: (symbol = '', limit = 50) => 
    axios.get(`${API_BASE_URL}/predictions`, { params: { symbol, limit } }),
  getPerformance: () => axios.get(`${API_BASE_URL}/performance`),
  runBacktest: (params) => axios.post(`${API_BASE_URL}/backtest`, params),
  triggerRefresh: () => axios.post(`${API_BASE_URL}/refresh`),
  getAssetFundamentals: (symbol) => axios.get(`${API_BASE_URL}/assets/${symbol}/fundamentals`),
  getAssetNews: (symbol) => axios.get(`${API_BASE_URL}/assets/${symbol}/news`),
  getAssetSentiment: (symbol) => axios.get(`${API_BASE_URL}/assets/${symbol}/sentiment`),
  getFeatureAvailability: (symbol) => axios.get(`${API_BASE_URL}/assets/${symbol}/feature-availability`),
  getAblationSummary: () => axios.get(`${API_BASE_URL}/research/ablation`),
  runAblation: () => axios.post(`${API_BASE_URL}/research/run-ablation`),
  getRealtimeStatus: () => axios.get(`${API_BASE_URL}/realtime/status`),
  getRealtimeQuote: (symbol) => axios.get(`${API_BASE_URL}/realtime/quote/${symbol}`),
  subscribeRealtime: (symbol) => axios.post(`${API_BASE_URL}/realtime/subscribe`, { symbol }),
  unsubscribeRealtime: (symbol) => axios.post(`${API_BASE_URL}/realtime/unsubscribe`, { symbol }),
  getLivePrediction: (symbol, modelName = "XGBoost") => axios.get(`${API_BASE_URL}/assets/${symbol}/live-prediction?model_name=${modelName}`),
  resolvePredictions: () => axios.post(`${API_BASE_URL}/research/resolve-predictions`),
  getPredictionTrackerStats: (symbol) => axios.get(`${API_BASE_URL}/assets/${symbol}/prediction-tracker-stats`),
  getLiveCollectionStatus: () => axios.get(`${API_BASE_URL}/research/live-collection-status`),
  getLivePredictionsHistory: (symbol, page = 1, limit = 50) => axios.get(`${API_BASE_URL}/research/live-predictions/${symbol}?page=${page}&limit=${limit}`),
  getLiveAnalytics: (symbol) => axios.get(`${API_BASE_URL}/research/live-analytics/${symbol}`),
  getLivePredictionsCsvUrl: (symbol) => `${API_BASE_URL}/research/live-predictions/${symbol}/csv`,
  getTechnicalAnalysis: (symbol) => axios.get(`${API_BASE_URL}/assets/${symbol}/technical-analysis`),
  getSystemStatus: () => axios.get(`${API_BASE_URL}/system/status`),
  getHealth: () => axios.get(`${BACKEND_ROOT_URL}/health`)
};









