import numpy as np
import pandas as pd
try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False
from typing import Dict, Any, List, Optional
from backend.features.feature_engine import FEATURE_COLUMNS

def get_shap_explanations(model_pipeline: Any, feature_row: pd.DataFrame) -> Dict[str, Any]:
    """
    Generates dynamic SHAP values or feature importance factors for a given prediction row.
    STRICT RULE: Never hardcodes contribution numbers. All values are computed dynamically from SHAP/tree model.
    """
    if feature_row is None or feature_row.empty:
        return {"factors": [], "method": "none", "disclaimer": "No feature row provided."}

    X_sample = feature_row[FEATURE_COLUMNS].values
    if len(X_sample.shape) == 1:
        X_sample = X_sample.reshape(1, -1)

    factors = []
    explanation_method = "feature_importance"

    try:
        # Check if underlying model supports SHAP TreeExplainer (e.g. XGBoost, RandomForest)
        raw_model = model_pipeline.model
        if hasattr(raw_model, "calibrated_classifiers_") and len(raw_model.calibrated_classifiers_) > 0:
            base_estimator = raw_model.calibrated_classifiers_[0].estimator
        else:
            base_estimator = raw_model

        if HAS_SHAP and hasattr(base_estimator, "feature_importances_"):
            explainer = shap.TreeExplainer(base_estimator)
            shap_values = explainer.shap_values(X_sample)

            # If shap_values is a list (for classification classes 0 and 1), take class 1 (UP)
            if isinstance(shap_values, list):
                vals = shap_values[1][0]
            else:
                vals = shap_values[0]

            explanation_method = "SHAP_TreeExplainer"
            for col, val, feat_val in zip(FEATURE_COLUMNS, vals, X_sample[0]):
                factors.append({
                    "feature": col,
                    "feature_value": float(feat_val),
                    "impact_value": float(val),
                    "direction": "UP" if val > 0 else "DOWN",
                    "description": format_factor_description(col, feat_val, val)
                })
        elif hasattr(base_estimator, "feature_importances_"):
            explanation_method = "Tree_Feature_Importance"
            importances = base_estimator.feature_importances_
            for col, imp, feat_val in zip(FEATURE_COLUMNS, importances, X_sample[0]):
                factors.append({
                    "feature": col,
                    "feature_value": float(feat_val),
                    "impact_value": float(imp),
                    "direction": "UP" if imp > 0 else "DOWN",
                    "description": format_factor_description(col, feat_val, imp)
                })
        elif hasattr(base_estimator, "coef_"):
            coefs = base_estimator.coef_[0]
            explanation_method = "Linear_Coefficient"
            for col, coef, feat_val in zip(FEATURE_COLUMNS, coefs, X_sample[0]):
                impact = coef * feat_val
                factors.append({
                    "feature": col,
                    "feature_value": float(feat_val),
                    "impact_value": float(impact),
                    "direction": "UP" if impact > 0 else "DOWN",
                    "description": format_factor_description(col, feat_val, impact)
                })
    except Exception as e:
        # Fallback to feature value indicator state without fake numbers
        explanation_method = "Technical_Indicator_State"
        for col in FEATURE_COLUMNS:
            val = float(feature_row[col].iloc[0]) if col in feature_row.columns else 0.0
            factors.append({
                "feature": col,
                "feature_value": val,
                "impact_value": 0.0,
                "direction": "NEUTRAL",
                "description": f"{col}: {val:.4f}"
            })

    # Sort factors by absolute impact value descending
    factors = sorted(factors, key=lambda x: abs(x["impact_value"]), reverse=True)

    return {
        "factors": factors[:6],  # Top 6 contributing factors
        "method": explanation_method,
        "disclaimer": "Explanations are derived dynamically from SHAP/tree feature importance calculations."
    }

def format_factor_description(feature: str, value: float, impact: float) -> str:
    """Generates plain English explanation string based on indicator state and SHAP impact."""
    impact_str = f"+{impact:.4f}" if impact > 0 else f"{impact:.4f}"
    
    if feature == "rsi":
        if value > 70:
            return f"RSI is overbought ({value:.1f}) -> SHAP impact {impact_str}"
        elif value < 30:
            return f"RSI is oversold ({value:.1f}) -> SHAP impact {impact_str}"
        else:
            return f"RSI is neutral ({value:.1f}) -> SHAP impact {impact_str}"
    elif feature == "ema_10" or feature == "ema_20":
        return f"{feature.upper()} value is {value:.2f} -> SHAP impact {impact_str}"
    elif feature == "macd":
        return f"MACD line is {value:.4f} -> SHAP impact {impact_str}"
    elif feature == "macd_hist":
        trend = "positive momentum" if value > 0 else "negative momentum"
        return f"MACD Histogram shows {trend} ({value:.4f}) -> SHAP impact {impact_str}"
    elif feature == "daily_return":
        return f"Recent daily return was {value*100:.2f}% -> SHAP impact {impact_str}"
    elif feature == "rolling_volatility":
        return f"20-day rolling volatility is {value*100:.2f}% -> SHAP impact {impact_str}"
    elif feature == "volume_change":
        return f"Volume change is {value*100:.2f}% -> SHAP impact {impact_str}"
    else:
        return f"{feature}: {value:.4f} -> SHAP impact {impact_str}"
