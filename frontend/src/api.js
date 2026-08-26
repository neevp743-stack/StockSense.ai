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

// Automatic Auth Token & X-Request-ID Header Interceptor
axios.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('stocksense_token');
    if (token && !config.headers.Authorization) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
}, (error) => Promise.reject(error));

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
  getPhase15ResearchStatus: (options = {}) => axios.get(`${API_BASE_URL}/research/phase15/status`, options),
  getSystemStatus: (options = {}) => axios.get(`${API_BASE_URL}/system/status`, options),
  getHealth: (options = {}) => axios.get(`${BACKEND_ROOT_URL}/health`, options),
  getDataQuality: (symbol, options = {}) => axios.get(`${API_BASE_URL}/data-quality/${symbol}`, options),
  getModelMonitor: (symbol, options = {}) => axios.get(`${API_BASE_URL}/model-monitor/${symbol}`, options),
  getModelMonitorAll: (options = {}) => axios.get(`${API_BASE_URL}/model-monitor/all`, options),
  getModelCalibration: (symbol, options = {}) => axios.get(`${API_BASE_URL}/model-monitor/${symbol}/calibration`, options),
  getModelDrift: (symbol, options = {}) => axios.get(`${API_BASE_URL}/model-monitor/${symbol}/drift`, options),
  getProductionHealth: (options = {}) => axios.get(`${API_BASE_URL}/production-health`, options),
  getPhase18Status: (options = {}) => axios.get(`${API_BASE_URL}/research/phase18/status`, options),
  getPhase18Comparison: (symbol = '', options = {}) => axios.get(`${API_BASE_URL}/research/phase18/comparison`, { params: symbol ? { symbol } : {}, ...options }),
  getPhase18Trades: (options = {}) => axios.get(`${API_BASE_URL}/research/phase18/trades`, options),
  getPhase18Statistics: (options = {}) => axios.get(`${API_BASE_URL}/research/phase18/statistics`, options),
  getPhase19Status: (options = {}) => axios.get(`${API_BASE_URL}/research/phase19/status`, options),
  getPhase19Summary: (options = {}) => axios.get(`${API_BASE_URL}/research/phase19/summary`, options),
  getPhase19Rolling: (options = {}) => axios.get(`${API_BASE_URL}/research/phase19/rolling`, options),
  getPhase19Symbols: (options = {}) => axios.get(`${API_BASE_URL}/research/phase19/symbols`, options),
  getPhase19Regimes: (options = {}) => axios.get(`${API_BASE_URL}/research/phase19/regimes`, options),
  getPhase19Calibration: (options = {}) => axios.get(`${API_BASE_URL}/research/phase19/calibration`, options),
  getPhase19Trades: (options = {}) => axios.get(`${API_BASE_URL}/research/phase19/trades`, options),
  getPhase19Statistics: (options = {}) => axios.get(`${API_BASE_URL}/research/phase19/statistics`, options),
  getPhase19PromotionReadiness: (options = {}) => axios.get(`${API_BASE_URL}/research/phase19/promotion-readiness`, options),
  getPhase19DataQuality: (options = {}) => axios.get(`${API_BASE_URL}/research/phase19/data-quality`, options),
  getPhase19AStatus: (options = {}) => axios.get(`${API_BASE_URL}/research/phase19a/status`, options),
  getPhase19ASymbolStatus: (symbol, options = {}) => axios.get(`${API_BASE_URL}/research/phase19a/${encodeURIComponent(symbol)}`, options),
  getPhase20Status: (options = {}) => axios.get(`${API_BASE_URL}/research/phase20/status`, options),
  getPhase20Comparison: (options = {}) => axios.get(`${API_BASE_URL}/research/phase20/comparison`, options),
  getPhase20Forward: (options = {}) => axios.get(`${API_BASE_URL}/research/phase20/forward`, options),
  getPhase20Regimes: (options = {}) => axios.get(`${API_BASE_URL}/research/phase20/regimes`, options),
  getPhase20Calibration: (options = {}) => axios.get(`${API_BASE_URL}/research/phase20/calibration`, options),
  getPhase20Drift: (options = {}) => axios.get(`${API_BASE_URL}/research/phase20/drift`, options),
  getPhase20Readiness: (options = {}) => axios.get(`${API_BASE_URL}/research/phase20/readiness`, options),
  getPhase20Symbol: (symbol, options = {}) => axios.get(`${API_BASE_URL}/research/phase20/${encodeURIComponent(symbol)}`, options),
  getProviderHealth: (options = {}) => axios.get(`${API_BASE_URL}/research/phase21/provider-health`, options),
  getSymbolProviderHealth: (symbol, options = {}) => axios.get(`${API_BASE_URL}/research/phase21/provider-health/${encodeURIComponent(symbol)}`, options),
  getMarketAnalysis: (symbol, interval = '1d', limit = 300, options = {}) => axios.get(`${API_BASE_URL}/market/${encodeURIComponent(symbol)}/analysis`, { params: { interval, limit }, ...options }),
  getMarketCandles: (symbol, interval = '1d', limit = 300, options = {}) => axios.get(`${API_BASE_URL}/market/${encodeURIComponent(symbol)}/candles`, { params: { interval, limit }, ...options }),
  getMarketQuote: (symbol, options = {}) => axios.get(`${API_BASE_URL}/market/${encodeURIComponent(symbol)}/quote`, options),

  // Phase 21.6 v1 API Methods
  registerUser: (username, email, password, options = {}) => axios.post(`${API_BASE_URL}/v1/auth/register`, { username, email, password }, options),
  loginUser: (username_or_email, password, options = {}) => axios.post(`${API_BASE_URL}/v1/auth/login`, { username_or_email, password }, options),
  getAuthMe: (options = {}) => axios.get(`${API_BASE_URL}/v1/auth/me`, options),
  getUserProfile: (options = {}) => axios.get(`${API_BASE_URL}/v1/user/profile`, options),
  getUserPreferences: (options = {}) => axios.get(`${API_BASE_URL}/v1/user/preferences`, options),
  updateUserPreferences: (updates, options = {}) => axios.patch(`${API_BASE_URL}/v1/user/preferences`, updates, options),
  requestWhatsAppVerify: (phoneNumber, options = {}) => axios.post(`${API_BASE_URL}/v1/user/whatsapp/verify/request`, { phone_number: phoneNumber }, options),
  confirmWhatsAppVerify: (verificationId, code, options = {}) => axios.post(`${API_BASE_URL}/v1/user/whatsapp/verify/confirm`, { verification_id: verificationId, code }, options),
  getWhatsAppStatus: (options = {}) => axios.get(`${API_BASE_URL}/v1/user/whatsapp/status`, options),
  sendTestWhatsApp: (options = {}) => axios.post(`${API_BASE_URL}/v1/user/whatsapp/test`, {}, options),
  disableWhatsApp: (options = {}) => axios.delete(`${API_BASE_URL}/v1/user/whatsapp/disable`, options),
  createWebhook: (targetUrl, events, options = {}) => axios.post(`${API_BASE_URL}/v1/webhooks`, { target_url: targetUrl, events }, options),
  listWebhooks: (options = {}) => axios.get(`${API_BASE_URL}/v1/webhooks`, options),
  deleteWebhook: (webhookId, options = {}) => axios.delete(`${API_BASE_URL}/v1/webhooks/${webhookId}`, options)
};













