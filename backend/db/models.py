from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Boolean, Text, UniqueConstraint, Index
from backend.db.database import Base


class AssetRecord(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, index=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    asset_class = Column(String(50), index=True, nullable=False)  # INDIAN_EQUITY, US_EQUITY, CRYPTO, FOREX, INDEX
    exchange = Column(String(50), nullable=False)
    market = Column(String(50), nullable=False)
    currency = Column(String(10), nullable=False)
    currency_symbol = Column(String(10), nullable=False)
    provider_symbol = Column(String(50), nullable=False)
    active = Column(Boolean, default=True)
    trading_calendar = Column(String(50), nullable=False)
    timezone = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class StockPrice(Base):
    __tablename__ = "stock_prices"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True, nullable=False)
    date = Column(Date, index=True, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)

    __table_args__ = (
        UniqueConstraint("symbol", "date", name="uix_symbol_date"),
        Index("idx_stock_price_symbol_date", "symbol", "date"),
    )

class FeatureRecord(Base):
    __tablename__ = "feature_records"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True, nullable=False)
    date = Column(Date, index=True, nullable=False)
    sma_10 = Column(Float, nullable=True)
    sma_20 = Column(Float, nullable=True)
    sma_50 = Column(Float, nullable=True)
    ema_10 = Column(Float, nullable=True)
    ema_20 = Column(Float, nullable=True)
    rsi = Column(Float, nullable=True)
    macd = Column(Float, nullable=True)
    macd_signal = Column(Float, nullable=True)
    macd_hist = Column(Float, nullable=True)
    bb_upper = Column(Float, nullable=True)
    bb_lower = Column(Float, nullable=True)
    bb_width = Column(Float, nullable=True)
    daily_return = Column(Float, nullable=True)
    rolling_volatility = Column(Float, nullable=True)
    volume_change = Column(Float, nullable=True)
    target = Column(Integer, nullable=True)  # 1 for UP, 0 for DOWN, NULL for latest row without next close

    __table_args__ = (
        UniqueConstraint("symbol", "date", name="uix_feature_symbol_date"),
        Index("idx_feature_symbol_date", "symbol", "date"),
    )

class ModelMetadata(Base):
    __tablename__ = "model_metadata"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(50), nullable=False)  # e.g., LogisticRegression, RandomForest, XGBoost, LSTM, Ensemble
    version = Column(String(20), nullable=False)
    symbol = Column(String(20), nullable=False)
    asset_class = Column(String(50), nullable=True)
    training_start = Column(Date, nullable=False)
    training_end = Column(Date, nullable=False)
    features_list = Column(Text, nullable=False)  # JSON string
    hyperparameters = Column(Text, nullable=False)  # JSON string
    metrics_json = Column(Text, nullable=False)  # JSON string (accuracy, precision, recall, f1, roc_auc, brier_score)
    file_path = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_model_meta_symbol_name", "symbol", "model_name"),
    )

class PredictionRecord(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    stock_symbol = Column(String(20), index=True, nullable=False)
    asset_class = Column(String(50), nullable=True)
    data_status = Column(String(20), nullable=True)              # LIVE, DELAYED, HISTORICAL, UNAVAILABLE
    prediction_date = Column(Date, index=True, nullable=False)  # Target date being predicted (T+1)
    as_of_date = Column(Date, nullable=False)                   # Date of features used (T)
    predicted_direction = Column(Integer, nullable=False)        # 1 = UP, 0 = DOWN
    probability_up = Column(Float, nullable=False)
    probability_down = Column(Float, nullable=False)
    risk_category = Column(String(20), nullable=False)           # LOW, MEDIUM, HIGH
    model_version = Column(String(50), nullable=False)
    explanation_json = Column(Text, nullable=True)             # Dynamic SHAP / indicator factors
    prediction_timestamp = Column(DateTime, default=datetime.utcnow)
    actual_direction = Column(Integer, nullable=True)           # Resolved later: 1 or 0
    is_correct = Column(Boolean, nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_prediction_symbol_date", "stock_symbol", "prediction_date"),
    )


class UserRecord(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="USER", nullable=False)  # USER, ADMIN
    created_at = Column(DateTime, default=datetime.utcnow)

class FundamentalObservation(Base):
    __tablename__ = "fundamental_observations"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True, nullable=False)
    metric = Column(String(50), index=True, nullable=False)  # eps, revenue, net_income, pe_ratio, roe, etc.
    value = Column(Float, nullable=True)
    period_end = Column(Date, nullable=False)
    filing_date = Column(Date, nullable=False)
    available_timestamp = Column(DateTime, nullable=False, index=True)
    source = Column(String(100), nullable=False)
    retrieval_timestamp = Column(DateTime, default=datetime.utcnow)

class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(String(100), unique=True, index=True, nullable=False)
    symbol = Column(String(20), index=True, nullable=False)
    headline = Column(Text, nullable=False)
    published_timestamp = Column(DateTime, nullable=False, index=True)
    source = Column(String(100), nullable=False)
    url = Column(Text, nullable=True)
    sentiment_score = Column(Float, nullable=False)
    sentiment_label = Column(String(20), nullable=False)  # POSITIVE, NEUTRAL, NEGATIVE
    retrieval_timestamp = Column(DateTime, default=datetime.utcnow)

class SentimentRecord(Base):
    __tablename__ = "sentiment_records"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True, nullable=False)
    date = Column(Date, index=True, nullable=False)
    mean_sentiment = Column(Float, nullable=False)
    median_sentiment = Column(Float, nullable=False)
    pos_count = Column(Integer, default=0)
    neg_count = Column(Integer, default=0)
    neu_count = Column(Integer, default=0)
    news_volume = Column(Integer, default=0)
    sentiment_3d_avg = Column(Float, nullable=True)
    sentiment_7d_avg = Column(Float, nullable=True)

    __table_args__ = (
        UniqueConstraint("symbol", "date", name="uix_sentiment_symbol_date"),
    )

class LivePredictionRecord(Base):
    __tablename__ = "live_prediction_records"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True, nullable=False)
    prediction_timestamp = Column(DateTime, nullable=False, index=True, default=datetime.utcnow)
    market_timestamp = Column(DateTime, nullable=True)
    feature_timestamp = Column(DateTime, nullable=True, default=datetime.utcnow)
    model_version = Column(String(50), nullable=False, default="XGBoost v1.0")
    predicted_direction = Column(String(10), nullable=False)  # UP, DOWN
    probability_up = Column(Float, nullable=False)
    probability_down = Column(Float, nullable=False)
    confidence = Column(String(20), nullable=True)           # HIGH, MODERATE, LOW
    trend_regime = Column(String(20), nullable=True)         # BULL, BEAR, SIDEWAYS
    volatility_regime = Column(String(20), nullable=True)    # HIGH_VOLATILITY, LOW_VOLATILITY
    combined_regime = Column(String(50), nullable=True)     # e.g., BULL_LOW_VOLATILITY
    current_price = Column(Float, nullable=True)
    prediction_horizon = Column(Integer, default=1)
    feature_version = Column(String(20), default="v12")
    data_status = Column(String(20), nullable=False, default="LIVE")  # LIVE, DELAYED, STALE

    # Resolution fields
    resolved = Column(Boolean, default=False, index=True)
    resolution_timestamp = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)  # Backward compatibility
    actual_price = Column(Float, nullable=True)
    actual_direction = Column(String(10), nullable=True)  # UP, DOWN
    resolved_direction = Column(String(10), nullable=True)  # Backward compatibility
    actual_return = Column(Float, nullable=True)
    correct = Column(Boolean, nullable=True)
    is_correct = Column(Boolean, nullable=True)  # Backward compatibility
    brier_score = Column(Float, nullable=True)
    error_reason = Column(String(255), nullable=True)

    __table_args__ = (
        Index("idx_live_pred_sym_time", "symbol", "prediction_timestamp"),
        Index("idx_live_pred_sym_resolved", "symbol", "resolved"),
        Index("idx_live_pred_sym_model", "symbol", "model_version"),
        Index("idx_live_pred_model_resolved", "model_version", "resolved"),
    )


class PaperPredictionRecord(Base):
    __tablename__ = "paper_prediction_records"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True, nullable=False)
    prediction_timestamp = Column(DateTime, nullable=False, index=True, default=datetime.utcnow)
    as_of_date = Column(Date, nullable=False)
    prediction_date = Column(Date, nullable=False)
    signal = Column(String(10), nullable=False)  # BUY, SELL, HOLD
    probability_up = Column(Float, nullable=False)
    probability_down = Column(Float, nullable=False)
    confidence = Column(String(20), nullable=False)  # HIGH, MODERATE, LOW
    trend_regime = Column(String(20), nullable=False)
    volatility_regime = Column(String(20), nullable=False)
    combined_regime = Column(String(50), nullable=False)
    current_price = Column(Float, nullable=False)
    entry_low = Column(Float, nullable=False)
    entry_high = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=False)
    target_1 = Column(Float, nullable=False)
    target_2 = Column(Float, nullable=False)
    risk_reward_target_1 = Column(Float, nullable=False)
    risk_reward_target_2 = Column(Float, nullable=False)
    model_version = Column(String(50), nullable=False, default="XGBoost v1.0")
    horizon_days = Column(Integer, default=1)
    
    # Resolution fields
    actual_direction = Column(String(10), nullable=True)
    actual_close_price = Column(Float, nullable=True)
    target_hit = Column(Boolean, nullable=True)
    stop_hit = Column(Boolean, nullable=True)
    outcome = Column(String(25), nullable=True)  # TARGET_1_HIT, TARGET_2_HIT, STOP_HIT, EXPIRED_HOLD, AMBIGUOUS, PENDING
    realized_return_pct = Column(Float, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    is_correct = Column(Boolean, nullable=True)

    __table_args__ = (
        Index("idx_paper_pred_symbol_time", "symbol", "prediction_timestamp"),
        Index("idx_paper_pred_symbol_resolved", "symbol", "resolved_at"),
        Index("idx_paper_pred_symbol_model", "symbol", "model_version"),
    )


class UserPreferencesRecord(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, index=True, nullable=False)
    theme = Column(String(20), default="dark", nullable=False)
    default_market = Column(String(50), default="BTC-USD", nullable=False)
    default_timeframe = Column(String(20), default="1d", nullable=False)
    default_currency = Column(String(10), default="USD", nullable=False)
    notifications_enabled = Column(Boolean, default=True, nullable=False)
    alerts_json = Column(Text, nullable=True)  # JSON string for alert toggles
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserWhatsAppVerificationRecord(Base):
    __tablename__ = "user_whatsapp_verifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, index=True, nullable=False)
    phone_number_e164 = Column(String(30), nullable=True)
    phone_number_masked = Column(String(30), nullable=True)
    verification_status = Column(String(30), default="UNVERIFIED", nullable=False)  # UNVERIFIED, VERIFICATION_SENT, VERIFIED, EXPIRED
    verification_code_hash = Column(String(255), nullable=True)
    verification_id = Column(String(100), nullable=True, index=True)
    code_expires_at = Column(DateTime, nullable=True)
    attempts_count = Column(Integer, default=0, nullable=False)
    last_sent_at = Column(DateTime, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    verification_provider = Column(String(50), default="OFFICIAL_WHATSAPP_BUSINESS", nullable=False)
    alerts_enabled = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WebhookSubscriptionRecord(Base):
    __tablename__ = "webhook_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    webhook_id = Column(String(100), unique=True, index=True, nullable=False)
    target_url = Column(String(255), nullable=False)
    secret_key = Column(String(100), nullable=False)
    events_json = Column(Text, nullable=False)  # JSON list of event names
    active = Column(Boolean, default=True, nullable=False)
    delivery_failures_count = Column(Integer, default=0, nullable=False)
    last_delivery_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"

    id = Column(Integer, primary_key=True, index=True)
    idempotency_key = Column(String(100), unique=True, index=True, nullable=False)
    user_id = Column(String(50), nullable=True, index=True)
    request_path = Column(String(255), nullable=False)
    response_code = Column(Integer, nullable=False)
    response_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)





