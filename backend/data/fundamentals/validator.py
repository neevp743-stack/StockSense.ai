"""
StockSense AI — Fundamental Data Validator
Validates point-in-time fundamental observations for integrity and timestamp sanity.
"""

from typing import Dict, Any, List
from datetime import datetime, date

def validate_fundamental_observation(obs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates a fundamental observation record.
    Returns dict with is_valid (bool) and errors (list).
    """
    errors = []
    symbol = obs.get("symbol")
    metric = obs.get("metric")
    val = obs.get("value")
    avail_ts = obs.get("available_timestamp")

    if not symbol:
        errors.append("Missing symbol")
    if not metric:
        errors.append("Missing metric")
    if avail_ts is None:
        errors.append("Missing available_timestamp (cannot verify point-in-time)")

    if isinstance(avail_ts, datetime) and avail_ts > datetime.utcnow():
        errors.append("Available timestamp is in the future")

    return {
        "is_valid": len(errors) == 0,
        "errors": errors
    }
