import axios from 'axios';

function normalizeApiUrl(rawUrl) {

  if (!rawUrl) return null;
  let url = rawUrl.trim().replace(/\/+$/, '');
  if (url.endsWith('/api')) {
    return url;
  }
  return `${url}/api`;
}

const rawEnvUrl = import.meta.env.VITE_API_BASE_URL;

// Environment-aware API Base URL with automatic /api path normalization
export const API_BASE_URL = normalizeApiUrl(rawEnvUrl) ||
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
  getDashboardData: (symbol, modelName = 'XGBoost', options = {}) =>
    axios.get(`${API_BASE_URL}/stocks/${symbol}/dashboard-data`, { params: { model_name: modelName }, ...options }),
  search: (query = '', limit = 20, options = {}) => axios.get(`${API_BASE_URL}/search`, { params: { q: query, limit }, ...options }),
  getMarkets: (params = {}, options = {}) => axios.get(`${API_BASE_URL}/markets`, { params, ...options }),
  getAssetClasses: (options = {}) => axios.get(`${API_BASE_URL}/asset-classes`, options),
  getAssets: (assetClass = '', options = {}) => axios.get(`${API_BASE_URL}/assets`, { params: { asset_class: assetClass }, ...options }),
  getAssetDetail: (symbol, options = {}) => axios.get(`${API_BASE_URL}/assets/${symbol}`, options),
  getUniverse: (options = {}) => axios.get(`${API_BASE_URL}/stocks`, options),
  getHistory: (symbol, limit = null, options = {}) => 
    axios.get(`${API_BASE_URL}/stocks/${symbol}/history`, { params: limit ? { limit } : {}, ...options }),
  getFeatures: (symbol, options = {}) => axios.get(`${API_BASE_URL}/stocks/${symbol}/features`, options),
  getPrediction: (symbol, modelName = 'XGBoost', options = {}) => 
    axios.get(`${API_BASE_URL}/stocks/${symbol}/prediction`, { params: { model_name: modelName }, ...options }),
  getModels: (options = {}) => axios.get(`${API_BASE_URL}/models`, options),
  trainModel: (symbol) => axios.post(`${API_BASE_URL}/models/train/${symbol}`),
  trainAllModels: () => axios.post(`${API_BASE_URL}/models/train-all`),
  getPredictionsHistory: (symbol = '', limit = 50, options = {}) => 
    axios.get(`${API_BASE_URL}/predictions`, { params: { symbol, limit }, ...options }),
  getPerformance: (options = {}) => axios.get(`${API_BASE_URL}/performance`, options),
  runBacktest: (params, options = {}) => axios.post(`${API_BASE_URL}/backtest`, params, options),
  triggerRefresh: (options = {}) => axios.post(`${API_BASE_URL}/refresh`, {}, options),
  getAssetFundamentals: (symbol, options = {}) => axios.get(`${API_BASE_URL}/assets/${symbol}/fundamentals`, options),
  getAssetNews: (symbol, options = {}) => axios.get(`${API_BASE_URL}/assets/${symbol}/news`, options),
  getAssetSentiment: (symbol, options = {}) => axios.get(`${API_BASE_URL}/assets/${symbol}/sentiment`, options),
  getFeatureAvailability: (symbol, options = {}) => axios.get(`${API_BASE_URL}/assets/${symbol}/feature-availability`, options),
  getAblationSummary: (options = {}) => axios.get(`${API_BASE_URL}/research/ablation`, options),
  runAblation: (options = {}) => axios.post(`${API_BASE_URL}/research/run-ablation`, {}, options),
  getRealtimeStatus: (options = {}) => axios.get(`${API_BASE_URL}/realtime/status`, options),
  getRealtimeQuote: (symbol, options = {}) => axios.get(`${API_BASE_URL}/realtime/quote/${symbol}`, options),
  subscribeRealtime: (symbol, options = {}) => axios.post(`${API_BASE_URL}/realtime/subscribe`, { symbol }, options),
  unsubscribeRealtime: (symbol, options = {}) => axios.post(`${API_BASE_URL}/realtime/unsubscribe`, { symbol }, options),
  getLivePrediction: (symbol, modelName = "XGBoost", options = {}) => 
    axios.get(`${API_BASE_URL}/assets/${symbol}/live-prediction?model_name=${modelName}`, options),
  resolvePredictions: (options = {}) => axios.post(`${API_BASE_URL}/research/resolve-predictions`, {}, options),
  getPredictionTrackerStats: (symbol, options = {}) => axios.get(`${API_BASE_URL}/assets/${symbol}/prediction-tracker-stats`, options),
  getLiveCollectionStatus: (options = {}) => axios.get(`${API_BASE_URL}/research/live-collection-status`, options),
  getLivePredictionsHistory: (symbol, page = 1, limit = 50, options = {}) => 
    axios.get(`${API_BASE_URL}/research/live-predictions/${symbol}?page=${page}&limit=${limit}`, options),
  getLiveAnalytics: (symbol, options = {}) => axios.get(`${API_BASE_URL}/research/live-analytics/${symbol}`, options),
  getLivePredictionsCsvUrl: (symbol) => `${API_BASE_URL}/research/live-predictions/${symbol}/csv`,
  getTechnicalAnalysis: (symbol, options = {}) => axios.get(`${API_BASE_URL}/assets/${symbol}/technical-analysis`, options),
  getTradeSetup: (symbol, options = {}) => axios.get(`${API_BASE_URL}/assets/${symbol}/trade-setup`, options),
  getTradeSetupBacktest: (symbol, options = {}) => axios.get(`${API_BASE_URL}/assets/${symbol}/trade-setup/backtest`, options),
  getTradeSetupHistory: (symbol, limit = 50, options = {}) => axios.get(`${API_BASE_URL}/assets/${symbol}/trade-setup/history`, { params: { limit }, ...options }),
  getPaperPerformance: (symbol, options = {}) => axios.get(`${API_BASE_URL}/assets/${symbol}/paper-performance`, options),
  getSystemStatus: (options = {}) => axios.get(`${API_BASE_URL}/system/status`, options),
  getHealth: (options = {}) => axios.get(`${BACKEND_ROOT_URL}/health`, options)
};











