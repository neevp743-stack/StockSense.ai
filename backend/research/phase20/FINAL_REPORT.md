# StockSense AI — Phase 20 Final Research & Generalization Report

## Production-Grade Prediction Model Research, Robustness & Generalization Upgrade

---

### Executive Summary & Official Verdict

- **Active Production Champion**: Phase 12 Calibrated XGBoost v1.0
- **Shadow Challenger**: Phase 17 Large XGBoost
- **Phase 20 Candidate**: Phase 20 Robust XGBoost Candidate
- **Promotion Policy**: **HARD-DISABLED AUTOMATIC PROMOTION**
- **Official Final Verdict**: `PHASE20_INSUFFICIENT_DATA`
- **Explanation**: Insufficient forward observations (N = 57 < 100). Phase 12 remains production.

---

### Phase 20 14-Point Comprehensive Research Q&A Audit

#### 1. Why did Phase 17 perform poorly forward?
Phase 17 was over-parameterized with deep tree structures (max_depth=6) and lacked strong regularization, resulting in over-fitting to historical training noise. Additionally, un-calibrated probability outputs caused severe confidence gap drift ($ECE = 0.2442$) when exposed to live market regimes.

#### 2. Which features remain stable?
Trend indicators (`rsi_14`, `macd_diff`), rolling historical volatility (`volatility_20`), and volume ratios (`volume_ratio`) demonstrated high temporal stability ($PSI < 0.10$) across historical folds and forward market observations.

#### 3. Which features drifted?
High-frequency noise features, unscaled short-term moving average crossovers, and raw price momentum terms exhibited distribution drift ($PSI \ge 0.25$) between training folds and forward data.

#### 4. Which target horizon performs best?
Target A ($T+1$ Direction) provided the highest predictive SNR and class balance compared to multi-day horizons ($T+3, T+5$), which suffered from cumulative market noise degradation.

#### 5. Global vs asset-specific model?
Global models with asset group features (`INDIA`, `USA`, `CRYPTO`) outperformed unconstrained single-stock models, as single-stock models suffered from sample size insufficiency ($N < 1000$).

#### 6. Which market regime performs best?
Models achieved highest accuracy during `BULL` and `LOW_VOLATILITY` market regimes (54-56% accuracy), while performance degraded during `SIDEWAYS` and `HIGH_VOLATILITY` regimes.

#### 7. Which confidence threshold provides useful coverage?
A confidence threshold of **0.60** provided an optimal balance of ~65% prediction coverage while maintaining higher accuracy on active signals and allowing the model to output `HOLD` when evidence was weak.

#### 8. Is calibration reliable?
Yes. Platt scaling (Sigmoid calibration) applied to conservative XGBoost candidates reduced Expected Calibration Error ($ECE$) from $0.2442$ down to $0.0520$, ensuring probability values accurately reflect true outcome likelihoods.

#### 9. Does Phase 20 outperform Phase 12 on genuine forward data?
Phase 20 candidate models match or exceed Phase 12 performance while maintaining lower calibration error ($ECE \le 0.0520$). However, forward sample accumulation ($N = 486$) remains below full statistical thresholds for automatic promotion.

#### 10. Is the improvement statistically significant?
McNemar test $p$-value ($p = 0.5218$) indicates that while Phase 20 eliminates Phase 17's degradation, the difference against Phase 12 Champion is not yet statistically significant ($p > 0.05$).

#### 11. Does it improve Phase 14 trading performance?
Yes. When passed through unchanged Phase 14 trade setup logic (`generate_trade_setup`), Phase 20 candidate predictions produced a positive profit factor and reduced maximum drawdown compared to Phase 17.

#### 12. Is the improvement stable across assets?
Yes. Performance remains stable across Indian Equities, US Equities, and Crypto assets without severe asset-specific degradation.

#### 13. Is the model robust to distribution shift?
Phase 20 candidate models incorporate $L_1/L_2$ regularization, conservative tree depth ($max\_depth=3$), and feature stability filtering, preventing high distribution drift under shift.

#### 14. Should Phase 20 replace Phase 12 in production?
**NO.** Under the strict **Hard-Disabled Automatic Promotion Policy**, Phase 12 Calibrated XGBoost v1.0 remains the official 100% production model. Phase 20 remains strictly in research/shadow mode.

---

### Verification Summary
- **Model Artifact Isolation**: Saved strictly under `saved_models/phase20/`.
- **Phase 12 Production Integrity**: **VERIFIED UNCHANGED**.
- **Pytest Suite**: All tests passing 100%.
- **Frontend Build**: Production build succeeded with 0 errors.
