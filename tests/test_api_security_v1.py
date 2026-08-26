import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.user_service import (
    normalize_phone_e164, mask_phone_number, get_password_hash, verify_password
)

from backend.db.database import init_db

init_db()

client = TestClient(app)

def test_password_hashing():
    raw = "SecureP@ssw0rd2026!"
    hashed = get_password_hash(raw)
    assert hashed != raw
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_phone_normalization_e164():
    assert normalize_phone_e164("+91 98765 43210") == "+919876543210"
    assert normalize_phone_e164("+1 (555) 234-5678") == "+15552345678"
    assert normalize_phone_e164("00919876543210") == "+919876543210"
    
    with pytest.raises(ValueError):
        normalize_phone_e164("invalid_phone_123")

def test_phone_masking():
    assert mask_phone_number("+919876543210") == "+91******3210"

def test_unauthenticated_protected_route():
    response = client.get("/api/v1/user/profile")
    assert response.status_code == 401
    json_data = response.json()
    assert json_data["detail"]["code"] == "AUTH_REQUIRED"

def test_user_registration_login_and_profile_flow():
    import uuid
    uid = uuid.uuid4().hex[:8]
    username = f"user_{uid}"
    email = f"{username}@stocksense.ai"
    password = "TestPassword123!"

    # 1. Register
    reg_resp = client.post("/api/v1/auth/register", json={
        "username": username,
        "email": email,
        "password": password
    })
    assert reg_resp.status_code == 200
    assert reg_resp.json()["success"] is True
    assert reg_resp.json()["data"]["username"] == username

    # 2. Login
    login_resp = client.post("/api/v1/auth/login", json={
        "username_or_email": username,
        "password": password
    })
    assert login_resp.status_code == 200
    login_data = login_resp.json()["data"]
    token = login_data["access_token"]
    assert token is not None

    headers = {"Authorization": f"Bearer {token}"}

    # 3. Get Auth Me
    me_resp = client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["data"]["username"] == username

    # 4. Get Profile
    prof_resp = client.get("/api/v1/user/profile", headers=headers)
    assert prof_resp.status_code == 200
    assert prof_resp.json()["data"]["email"] == email

    # 5. Update Preferences
    pref_resp = client.patch("/api/v1/user/preferences", json={"default_market": "SOL-USD", "theme": "dark"}, headers=headers)
    assert pref_resp.status_code == 200
    assert pref_resp.json()["data"]["default_market"] == "SOL-USD"

def test_whatsapp_verification_flow():
    import uuid
    uid = uuid.uuid4().hex[:8]
    username = f"wa_user_{uid}"
    email = f"{username}@stocksense.ai"
    password = "TestPassword123!"

    client.post("/api/v1/auth/register", json={"username": username, "email": email, "password": password})
    login_resp = client.post("/api/v1/auth/login", json={"username_or_email": username, "password": password})
    token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Request WA verification
    wa_req = client.post("/api/v1/user/whatsapp/verify/request", json={"phone_number": "+91 98765 43210"}, headers=headers)
    assert wa_req.status_code == 200
    wa_data = wa_req.json()["data"]
    assert "verification_id" in wa_data
    assert wa_data["status"] in ["VERIFICATION_SENT", "WHATSAPP_NOT_CONFIGURED"]

    # Invalid code test
    conf_invalid = client.post("/api/v1/user/whatsapp/verify/confirm", json={
        "verification_id": wa_data["verification_id"],
        "code": "000000"
    }, headers=headers)
    assert conf_invalid.status_code == 400
    assert conf_invalid.json()["detail"]["code"] == "VERIFICATION_CODE_INVALID"

def test_webhooks_flow():
    import uuid
    uid = uuid.uuid4().hex[:8]
    username = f"wh_user_{uid}"
    email = f"{username}@stocksense.ai"
    password = "TestPassword123!"

    client.post("/api/v1/auth/register", json={"username": username, "email": email, "password": password})
    login_resp = client.post("/api/v1/auth/login", json={"username_or_email": username, "password": password})
    token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create Webhook
    wh_resp = client.post("/api/v1/webhooks", json={
        "target_url": "https://example.com/stocksense-webhook",
        "events": ["LIQUIDITY_SWEEP", "CONFLUENCE_SIGNAL"]
    }, headers=headers)
    assert wh_resp.status_code == 200
    wh_id = wh_resp.json()["data"]["webhook_id"]
    assert wh_id.startswith("wh_")

    # List Webhooks
    list_resp = client.get("/api/v1/webhooks", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()["data"]) >= 1

    # Test Webhook Trigger
    test_resp = client.post(f"/api/v1/webhooks/{wh_id}/test", headers=headers)
    assert test_resp.status_code == 200
    assert test_resp.json()["data"]["status"] == "TEST_DELIVERY_SIMULATED"

    # Delete Webhook
    del_resp = client.delete(f"/api/v1/webhooks/{wh_id}", headers=headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["data"]["deleted"] is True

def test_versioned_public_market_api():
    quote_resp = client.get("/api/v1/market/BTC-USD/quote")
    assert quote_resp.status_code == 200
    assert quote_resp.headers.get("X-Request-ID") is not None
    assert quote_resp.json()["success"] is True

    candles_resp = client.get("/api/v1/market/BTC-USD/candles?limit=10&page=1")
    assert candles_resp.status_code == 200
    assert "pagination" in candles_resp.json()

def test_idempotency_key_replay():
    import uuid
    ikey = f"idem_{uuid.uuid4().hex}"
    headers = {"Idempotency-Key": ikey}
    
    # Unauthenticated request returns error and records idempotency
    r1 = client.post("/api/v1/auth/register", json={"username": f"idem_{uuid.uuid4().hex[:6]}", "email": f"idem_{uuid.uuid4().hex[:6]}@test.com", "password": "pass"}, headers=headers)
    assert r1.status_code in [200, 201]
    
    # Replay request with same key
    r2 = client.post("/api/v1/auth/register", json={"username": f"idem_{uuid.uuid4().hex[:6]}", "email": f"idem_{uuid.uuid4().hex[:6]}@test.com", "password": "pass"}, headers=headers)
    assert r2.status_code in [200, 201]
    assert r2.headers.get("X-Idempotent-Replay") == "true"
