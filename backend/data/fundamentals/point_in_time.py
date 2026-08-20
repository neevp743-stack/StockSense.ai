"""
StockSense AI — Point-in-Time Fundamental Observation Engine
Guarantees zero future fundamental data leakage by validating filing availability timestamps.
"""

from datetime import datetime, date
from typing import Dict, Any, List, Optional
import pandas as pd

def is_observation_available(available_timestamp: datetime, prediction_timestamp: datetime) -> bool:
    """
    Returns True if and only if the fundamental filing was publicly available
    strictly before or at the prediction timestamp.
    """
    if available_timestamp is None or prediction_timestamp is None:
        return False
    return available_timestamp <= prediction_timestamp

def filter_point_in_time_observations(
    observations: List[Dict[str, Any]], 
    prediction_timestamp: datetime
) -> List[Dict[str, Any]]:
    """Filters list of fundamental observations ensuring zero look-ahead bias."""
    valid_obs = []
    for obs in observations:
        avail_ts = obs.get("available_timestamp")
        if isinstance(avail_ts, str):
            try:
                avail_ts = datetime.fromisoformat(avail_ts)
            except Exception:
                continue
        if avail_ts and is_observation_available(avail_ts, prediction_timestamp):
            valid_obs.append(obs)
    return valid_obs
