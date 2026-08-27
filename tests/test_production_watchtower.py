"""
StockSense AI — Production Watchtower & Uptime Monitoring Unit Tests
Verifies health classification, outage threshold, alert deduplication,
recovery threshold, WhatsApp failure isolation, CRON_SECRET security,
secret redaction, and bounded telemetry storage.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from backend.main import app
from backend.services.production_watchtower_service import ProductionWatchtower, production_watchtower
from backend.db.database import SessionLocal, init_db
from backend.db.models_watchtower import WatchtowerStateRecord, WatchtowerCheckRecord

client = TestClient(app)


def test_01_health_classification():
    """Verifies health response classification rules."""
    pw = ProductionWatchtower()

    assert pw.classify_health_response(200, {"app_state": "READY"}, None) == "HEALTHY"
    assert pw.classify_health_response(200, {"app_state": "INITIALIZING"}, None) == "INITIALIZING"
    assert pw.classify_health_response(200, {"app_state": "DEGRADED"}, None) == "DEGRADED"
    assert pw.classify_health_response(500, None, None) == "BACKEND_ERROR"
    assert pw.classify_health_response(502, None, None) == "BACKEND_ERROR"
    assert pw.classify_health_response(503, None, None) == "BACKEND_ERROR"
    assert pw.classify_health_response(504, None, None) == "BACKEND_ERROR"
    assert pw.classify_health_response(None, None, "TIMEOUT") == "TIMEOUT"
    assert pw.classify_health_response(None, None, "OFFLINE") == "OFFLINE"


def test_02_outage_state_machine_3_failure_threshold_and_deduplication():
    """3 consecutive failures trigger OUTAGE_ACTIVE and exactly 1 alert."""
    init_db()
    db = SessionLocal()
    try:
        # Reset state
        db.query(WatchtowerStateRecord).delete()
        db.query(WatchtowerCheckRecord).delete()
        db.commit()

        alerts_sent = []

        def mock_alert(alert_type, details):
            alerts_sent.append(alert_type)
            return "SENT"

        pw = ProductionWatchtower()

        with patch.object(pw, 'send_whatsapp_alert', side_effect=mock_alert):
            with patch('urllib.request.urlopen', side_effect=Exception("Connection Refused")):
                # Failure 1
                res1 = pw.run_check(db=db, target_url="http://mock.test/health")
                assert res1["consecutive_failures"] == 1
                assert not res1["is_outage_active"]
                assert len(alerts_sent) == 0

                # Failure 2
                res2 = pw.run_check(db=db, target_url="http://mock.test/health")
                assert res2["consecutive_failures"] == 2
                assert not res2["is_outage_active"]
                assert len(alerts_sent) == 0

                # Failure 3 -> Threshold reached! Outage declared
                res3 = pw.run_check(db=db, target_url="http://mock.test/health")
                assert res3["consecutive_failures"] == 3
                assert res3["is_outage_active"]
                assert len(alerts_sent) == 1
                assert alerts_sent[0] == "OUTAGE"

                # Failure 4 -> Outage remains active, NO duplicate alert!
                res4 = pw.run_check(db=db, target_url="http://mock.test/health")
                assert res4["consecutive_failures"] == 4
                assert res4["is_outage_active"]
                assert len(alerts_sent) == 1  # Still 1 alert total
    finally:
        db.close()


def test_03_recovery_state_machine_2_success_threshold_and_deduplication():
    """2 consecutive successes after outage trigger RECOVERY and exactly 1 alert."""
    init_db()
    db = SessionLocal()
    try:
        alerts_sent = []

        def mock_alert(alert_type, details):
            alerts_sent.append(alert_type)
            return "SENT"

        pw = ProductionWatchtower()

        # Set initial active outage state
        state = db.query(WatchtowerStateRecord).filter(WatchtowerStateRecord.id == 1).first()
        if not state:
            state = WatchtowerStateRecord(id=1)
            db.add(state)
        state.is_outage_active = True
        state.consecutive_failures = 5
        state.consecutive_successes = 0
        db.commit()

        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b'{"app_state": "READY"}'
        mock_resp.__enter__.return_value = mock_resp

        with patch.object(pw, 'send_whatsapp_alert', side_effect=mock_alert):
            with patch('urllib.request.urlopen', return_value=mock_resp):
                # Success 1
                res1 = pw.run_check(db=db, target_url="http://mock.test/health")
                assert res1["consecutive_successes"] == 1
                assert res1["is_outage_active"]  # Still active until 2 consecutive successes
                assert len(alerts_sent) == 0

                # Success 2 -> Recovery declared!
                res2 = pw.run_check(db=db, target_url="http://mock.test/health")
                assert res2["consecutive_successes"] == 2
                assert not res2["is_outage_active"]
                assert len(alerts_sent) == 1
                assert alerts_sent[0] == "RECOVERY"

                # Success 3 -> Normal operation, NO duplicate recovery alert!
                res3 = pw.run_check(db=db, target_url="http://mock.test/health")
                assert res3["consecutive_successes"] == 3
                assert not res3["is_outage_active"]
                assert len(alerts_sent) == 1  # Still 1 alert total
    finally:
        db.close()


def test_04_cron_secret_security():
    """Cron endpoint must reject unauthorized requests when CRON_SECRET is configured."""
    with patch.dict(os.environ, {"CRON_SECRET": "super_secret_cron_key_123"}):
        # Missing auth header -> 401 Unauthorized
        resp = client.get("/api/watchtower/cron")
        assert resp.status_code == 401

        # Invalid auth header -> 401 Unauthorized
        resp = client.get("/api/watchtower/cron", headers={"Authorization": "Bearer wrong_secret"})
        assert resp.status_code == 401

        # Valid auth header -> 200 OK
        resp = client.get("/api/watchtower/cron", headers={"Authorization": "Bearer super_secret_cron_key_123"})
        assert resp.status_code == 200


def test_05_whatsapp_failure_isolation():
    """WhatsApp failure or missing credentials must never crash Watchtower."""
    pw = ProductionWatchtower()

    # Unconfigured credentials
    with patch.dict(os.environ, {"WHATSAPP_API_KEY": ""}, clear=True):
        res = pw.send_whatsapp_alert("OUTAGE", {})
        assert res == "WHATSAPP_NOT_CONFIGURED"

    # Exception during delivery
    with patch.dict(os.environ, {"WHATSAPP_API_KEY": "dummy_key"}):
        with patch.object(ProductionWatchtower, 'send_whatsapp_alert', side_effect=Exception("API Error")):
            # Run check should catch Exception and return cleanly
            mock_resp = MagicMock()
            mock_resp.status = 200
            mock_resp.read.return_value = b'{"app_state": "READY"}'
            mock_resp.__enter__.return_value = mock_resp
            with patch('urllib.request.urlopen', return_value=mock_resp):
                res = pw.run_check(target_url="http://mock.test/health")
                assert res["success"] is True


def test_06_bounded_storage():
    """Watchtower check history records must be bounded to MAX_HISTORY_RECORDS (50)."""
    init_db()
    db = SessionLocal()
    try:
        pw = ProductionWatchtower()
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b'{"app_state": "READY"}'
        mock_resp.__enter__.return_value = mock_resp

        with patch('urllib.request.urlopen', return_value=mock_resp):
            for _ in range(55):
                pw.run_check(db=db, target_url="http://mock.test/health")

        count = db.query(WatchtowerCheckRecord).count()
        assert count <= 50
    finally:
        db.close()


def test_07_secret_redaction():
    """Watchtower telemetry summaries must not expose secrets."""
    init_db()
    db = SessionLocal()
    try:
        pw = ProductionWatchtower()
        summary = pw.get_status_summary(db)
        summary_str = str(summary)

        for secret_key in ["REALTIME_API_KEY", "TWELVE_DATA_API_KEY", "SECRET_KEY", "CRON_SECRET"]:
            val = os.environ.get(secret_key)
            if val and len(val) > 6:
                assert val not in summary_str
    finally:
        db.close()
