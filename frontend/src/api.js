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

const clientCache = {};

function cachedGet(url, config = {}, ttlMs = 15000) {
  const key = JSON.stringify({ url, params: config.params || {} });
  const now = Date.now();
  const cached = clientCache[key];
  
  if (cached && (now - cached.timestamp < ttlMs)) {
    return cached.promise;
  }
  
  const promise = axios.get(url, config).catch(err => {
    delete clientCache[key];
    throw err;
  });
  
  clientCache[key] = {
    promise,
    timestamp: now
  };
  
  return promise;
}

export const api = {
  getDashboardData: (symbol, modelName = 'XGBoost', options = {}) =>
    cachedGet(`${API_BASE_URL}/stocks/${symbol}/dashboard-data`, { params: { model_name: modelName }, ...options }, 15000),
  search: (query = '', limit = 20, options = {}) => axios.get(`${API_BASE_URL}/search`, { params: { q: query, limit }, ...options }),
  getMarkets: (params = {}, options = {}) => cachedGet(`${API_BASE_URL}/markets`, { params, ...options }, 30000),
  getAssetClasses: (options = {}) => cachedGet(`${API_BASE_URL}/asset-classes`, options, 60000),
  getAssets: (assetClass = '', options = {}) => cachedGet(`${API_BASE_URL}/assets`, { params: { asset_class: assetClass }, ...options }, 30000),
  getAssetDetail: (symbol, options = {}) => cachedGet(`${API_BASE_URL}/assets/${symbol}`, options, 30000),
  getUniverse: (options = {}) => cachedGet(`${API_BASE_URL}/stocks`, options, 30000),
  getHistory: (symbol, limit = null, options = {}) => 
    cachedGet(`${API_BASE_URL}/stocks/${symbol}/history`, { params: limit ? { limit } : {}, ...options }, 30000),
  getFeatures: (symbol, options = {}) => cachedGet(`${API_BASE_URL}/stocks/${symbol}/features`, options, 10000),
  getPrediction: (symbol, modelName = 'XGBoost', options = {}) => 
    cachedGet(`${API_BASE_URL}/stocks/${symbol}/prediction`, { params: { model_name: modelName }, ...options }, 10000),
  getModels: (options = {}) => cachedGet(`${API_BASE_URL}/models`, options, 30000),
  trainModel: (symbol) => axios.post(`${API_BASE_URL}/models/train/${symbol}`),
  trainAllModels: () => axios.post(`${API_BASE_URL}/models/train-all`),
  getPredictionsHistory: (symbol = '', limit = 50, options = {}) => 
    cachedGet(`${API_BASE_URL}/predictions`, { params: { symbol, limit }, ...options }, 10000),
  getPerformance: (options = {}) => cachedGet(`${API_BASE_URL}/performance`, options, 30000),
  runBacktest: (params, options = {}) => axios.post(`${API_BASE_URL}/backtest`, params, options),
  triggerRefresh: (options = {}) => axios.post(`${API_BASE_URL}/refresh`, {}, options),
  getAssetFundamentals: (symbol, options = {}) => cachedGet(`${API_BASE_URL}/assets/${symbol}/fundamentals`, options, 60000),
  getAssetNews: (symbol, options = {}) => cachedGet(`${API_BASE_URL}/assets/${symbol}/news`, options, 30000),
  getAssetSentiment: (symbol, options = {}) => cachedGet(`${API_BASE_URL}/assets/${symbol}/sentiment`, options, 30000),
  getFeatureAvailability: (symbol, options = {}) => cachedGet(`${API_BASE_URL}/assets/${symbol}/feature-availability`, options, 30000),
  getAblationSummary: (options = {}) => cachedGet(`${API_BASE_URL}/research/ablation`, options, 30000),
  runAblation: (options = {}) => axios.post(`${API_BASE_URL}/research/run-ablation`, {}, options),
  getRealtimeStatus: (options = {}) => cachedGet(`${API_BASE_URL}/realtime/status`, options, 5000),
  getRealtimeQuote: (symbol, options = {}) => cachedGet(`${API_BASE_URL}/realtime/quote/${symbol}`, options, 5000),
  subscribeRealtime: (symbol, options = {}) => axios.post(`${API_BASE_URL}/realtime/subscribe`, { symbol }, options),
  unsubscribeRealtime: (symbol, options = {}) => axios.post(`${API_BASE_URL}/realtime/unsubscribe`, { symbol }, options),
  getLivePrediction: (symbol, modelName = "XGBoost", options = {}) => 
    cachedGet(`${API_BASE_URL}/assets/${symbol}/live-prediction?model_name=${modelName}`, options, 5000),
  resolvePredictions: (options = {}) => axios.post(`${API_BASE_URL}/research/resolve-predictions`, {}, options),
  getPredictionTrackerStats: (symbol, options = {}) => cachedGet(`${API_BASE_URL}/assets/${symbol}/prediction-tracker-stats`, options, 10000),
  getLiveCollectionStatus: (options = {}) => cachedGet(`${API_BASE_URL}/research/live-collection-status`, options, 10000),
  getLivePredictionsHistory: (symbol, page = 1, limit = 50, options = {}) => 
    cachedGet(`${API_BASE_URL}/research/live-predictions/${symbol}?page=${page}&limit=${limit}`, options, 10000),
  getLiveAnalytics: (symbol, options = {}) => cachedGet(`${API_BASE_URL}/research/live-analytics/${symbol}`, options, 10000),
  getLivePredictionsCsvUrl: (symbol) => `${API_BASE_URL}/research/live-predictions/${symbol}/csv`,
  getTechnicalAnalysis: (symbol, options = {}) => cachedGet(`${API_BASE_URL}/assets/${symbol}/technical-analysis`, options, 15000),
  getTradeSetup: (symbol, options = {}) => cachedGet(`${API_BASE_URL}/assets/${symbol}/trade-setup`, options, 10000),
  getTradeSetupBacktest: (symbol, options = {}) => cachedGet(`${API_BASE_URL}/assets/${symbol}/trade-setup/backtest`, options, 30000),
  getTradeSetupHistory: (symbol, limit = 50, options = {}) => cachedGet(`${API_BASE_URL}/assets/${symbol}/trade-setup/history`, { params: { limit }, ...options }, 10000),
  getPaperPerformance: (symbol, options = {}) => cachedGet(`${API_BASE_URL}/assets/${symbol}/paper-performance`, options, 15000),
  getPhase15ResearchStatus: (options = {}) => cachedGet(`${API_BASE_URL}/research/phase15/status`, options, 30000),
  getSystemStatus: (options = {}) => cachedGet(`${API_BASE_URL}/system/status`, options, 5000),
  getHealth: (options = {}) => cachedGet(`${BACKEND_ROOT_URL}/health`, options, 5000),
  getDataQuality: (symbol, options = {}) => cachedGet(`${API_BASE_URL}/data-quality/${symbol}`, options, 30000),
  getModelMonitor: (symbol, options = {}) => cachedGet(`${API_BASE_URL}/model-monitor/${symbol}`, options, 30000),
  getModelMonitorAll: (options = {}) => cachedGet(`${API_BASE_URL}/model-monitor/all`, options, 30000),
  getModelCalibration: (symbol, options = {}) => cachedGet(`${API_BASE_URL}/model-monitor/${symbol}/calibration`, options, 30000),
  getModelDrift: (symbol, options = {}) => cachedGet(`${API_BASE_URL}/model-monitor/${symbol}/drift`, options, 30000),
  getProductionHealth: (options = {}) => cachedGet(`${API_BASE_URL}/production-health`, options, 10000),
  getPhase18Status: (options = {}) => cachedGet(`${API_BASE_URL}/research/phase18/status`, options, 30000),
  getPhase18Comparison: (symbol = '', options = {}) => cachedGet(`${API_BASE_URL}/research/phase18/comparison`, { params: symbol ? { symbol } : {}, ...options }, 30000),
  getPhase18Trades: (options = {}) => cachedGet(`${API_BASE_URL}/research/phase18/trades`, options, 30000),
  getPhase18Statistics: (options = {}) => cachedGet(`${API_BASE_URL}/research/phase18/statistics`, options, 30000),
  getPhase19Status: (options = {}) => cachedGet(`${API_BASE_URL}/research/phase19/status`, options, 30000),
  getPhase19Summary: (options = {}) => cachedGet(`${API_BASE_URL}/research/phase19/summary`, options, 30000),
  getPhase19Rolling: (options = {}) => cachedGet(`${API_BASE_URL}/research/phase19/rolling`, options, 30000),
  getPhase19Symbols: (options = {}) => cachedGet(`${API_BASE_URL}/research/phase19/symbols`, options, 30000),
  getPhase19Regimes: (options = {}) => cachedGet(`${API_BASE_URL}/research/phase19/regimes`, options, 30000),
  getPhase19Calibration: (options = {}) => cachedGet(`${API_BASE_URL}/research/phase19/calibration`, options, 30000),
  getPhase19Trades: (options = {}) => cachedGet(`${API_BASE_URL}/research/phase19/trades`, options, 30000),
  getPhase19Statistics: (options = {}) => cachedGet(`${API_BASE_URL}/research/phase19/statistics`, options, 30000),
  getPhase19PromotionReadiness: (options = {}) => cachedGet(`${API_BASE_URL}/research/phase19/promotion-readiness`, options, 30000),
  getPhase19DataQuality: (options = {}) => cachedGet(`${API_BASE_URL}/research/phase19/data-quality`, options, 30000),
  getPhase19AStatus: (options = {}) => cachedGet(`${API_BASE_URL}/research/phase19a/status`, options, 30000),
  getPhase19ASymbolStatus: (symbol, options = {}) => cachedGet(`${API_BASE_URL}/research/phase19a/${encodeURIComponent(symbol)}`, options, 30000),
  getPhase20Status: (options = {}) => cachedGet(`${API_BASE_URL}/research/phase20/status`, options, 30000),
  getPhase20Comparison: (options = {}) => cachedGet(`${API_BASE_URL}/research/phase20/comparison`, options, 30000),
  getPhase20Forward: (options = {}) => cachedGet(`${API_BASE_URL}/research/phase20/forward`, options, 30000),
  getPhase20Regimes: (options = {}) => cachedGet(`${API_BASE_URL}/research/phase20/regimes`, options, 30000),
  getPhase20Calibration: (options = {}) => cachedGet(`${API_BASE_URL}/research/phase20/calibration`, options, 30000),
  getPhase20Drift: (options = {}) => cachedGet(`${API_BASE_URL}/research/phase20/drift`, options, 30000),
  getPhase20Readiness: (options = {}) => cachedGet(`${API_BASE_URL}/research/phase20/readiness`, options, 30000),
  getPhase20Symbol: (symbol, options = {}) => cachedGet(`${API_BASE_URL}/research/phase20/${encodeURIComponent(symbol)}`, options, 30000),
  getProviderHealth: (options = {}) => cachedGet(`${API_BASE_URL}/research/phase21/provider-health`, options, 10000),
  getSymbolProviderHealth: (symbol, options = {}) => cachedGet(`${API_BASE_URL}/research/phase21/provider-health/${encodeURIComponent(symbol)}`, options, 10000),
  getMarketAnalysis: (symbol, interval = '1d', limit = 300, options = {}) => cachedGet(`${API_BASE_URL}/market/${encodeURIComponent(symbol)}/analysis`, { params: { interval, limit }, ...options }, 10000),
  getMarketCandles: (symbol, interval = '1d', limit = 300, options = {}) => cachedGet(`${API_BASE_URL}/market/${encodeURIComponent(symbol)}/candles`, { params: { interval, limit }, ...options }, 15000),
  getMarketQuote: (symbol, options = {}) => cachedGet(`${API_BASE_URL}/market/${encodeURIComponent(symbol)}/quote`, options, 5000),

  // Phase 21.6 v1 API Methods
  registerUser: (username, email, password, options = {}) => axios.post(`${API_BASE_URL}/v1/auth/register`, { username, email, password }, options),
  loginUser: (username_or_email, password, options = {}) => axios.post(`${API_BASE_URL}/v1/auth/login`, { username_or_email, password }, options),
  getAuthMe: (options = {}) => axios.get(`${API_BASE_URL}/v1/auth/me`, options), // Me call can be uncached or short cache
  getUserProfile: (options = {}) => cachedGet(`${API_BASE_URL}/v1/user/profile`, options, 15000),
  getUserPreferences: (options = {}) => cachedGet(`${API_BASE_URL}/v1/user/preferences`, options, 15000),
  updateUserPreferences: (updates, options = {}) => axios.patch(`${API_BASE_URL}/v1/user/preferences`, updates, options),
  requestWhatsAppVerify: (phoneNumber, options = {}) => axios.post(`${API_BASE_URL}/v1/user/whatsapp/verify/request`, { phone_number: phoneNumber }, options),
  confirmWhatsAppVerify: (verificationId, code, options = {}) => axios.post(`${API_BASE_URL}/v1/user/whatsapp/verify/confirm`, { verification_id: verificationId, code }, options),
  getWhatsAppStatus: (options = {}) => cachedGet(`${API_BASE_URL}/v1/user/whatsapp/status`, options, 5000),
  sendTestWhatsApp: (options = {}) => axios.post(`${API_BASE_URL}/v1/user/whatsapp/test`, {}, options),
  disableWhatsApp: (options = {}) => axios.delete(`${API_BASE_URL}/v1/user/whatsapp/disable`, options),
  createWebhook: (targetUrl, events, options = {}) => axios.post(`${API_BASE_URL}/v1/webhooks`, { target_url: targetUrl, events }, options),
  listWebhooks: (options = {}) => cachedGet(`${API_BASE_URL}/v1/webhooks`, options, 10000),
  deleteWebhook: (webhookId, options = {}) => axios.delete(`${API_BASE_URL}/v1/webhooks/${webhookId}`, options)
};













