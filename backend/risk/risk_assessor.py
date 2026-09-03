from typing import Dict, Any, Optional

def categorize_risk_and_signal(prob_up: float, brier_score: Optional[float] = None) -> Dict[str, Any]:
    """
    Categorizes directional prediction into Risk/Signal category (LOW, MEDIUM, HIGH)
    and attaches mandatory calibration disclaimers.
    
    STRICT RULE: Probability is NOT certainty or guaranteed accuracy.
    """
    prob_max = max(prob_up, 1.0 - prob_up)

    if prob_max < 0.55:
        category = "LOW"
        signal_strength = "Weak / Low Confidence Signal"
    elif prob_max < 0.65:
        category = "MEDIUM"
        signal_strength = "Moderate Directional Conviction"
    else:
        category = "HIGH"
        signal_strength = "Strong Directional Conviction"

    pct = prob_up * 100.0
    direction = "UP" if prob_up >= 0.5 else "DOWN"

    calibration_note = ""
    if brier_score is not None:
        calibration_note = f" (Model Brier Calibration Score: {brier_score:.4f})"

    disclaimer = (
        f"IMPORTANT: A {pct:.1f}% {direction} directional probability is an empirical model output "
        f"and does NOT imply a {pct:.1f}% guaranteed trading win rate or financial return{calibration_note}."
    )

    return {
        "probability_up": prob_up,
        "probability_down": 1.0 - prob_up,
        "predicted_direction": direction,
        "risk_category": category,
        "signal_strength": signal_strength,
        "brier_score": brier_score,
        "disclaimer": disclaimer
    }
