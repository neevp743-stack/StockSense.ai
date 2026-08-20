import pytest
from datetime import datetime, timedelta
from backend.data.fundamentals.point_in_time import is_observation_available, filter_point_in_time_observations

def test_fundamental_point_in_time_availability():
    t_pred = datetime(2026, 2, 1, 10, 0, 0)
    t_past = datetime(2026, 1, 15, 16, 30, 0)
    t_future = datetime(2026, 2, 1, 16, 30, 0)

    assert is_observation_available(t_past, t_pred) is True
    assert is_observation_available(t_future, t_pred) is False

def test_filter_point_in_time_observations():
    t_pred = datetime(2026, 2, 1, 10, 0, 0)
    obs = [
        {"metric": "eps", "value": 2.5, "available_timestamp": datetime(2026, 1, 10)},
        {"metric": "eps", "value": 3.0, "available_timestamp": datetime(2026, 2, 5)}
    ]
    valid = filter_point_in_time_observations(obs, t_pred)
    assert len(valid) == 1
    assert valid[0]["value"] == 2.5
