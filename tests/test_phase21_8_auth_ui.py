import pytest
import uuid
from fastapi.testclient import TestClient
from backend.main import app
from backend.db.database import get_db, init_db
from backend.db.models import UserRecord

init_db()
client = TestClient(app)

def test_registration_with_fullname_and_phone():
    """Verify user registration handles full name and optional phone number correctly."""
    uid = uuid.uuid4().hex[:8]
    email = f"user_{uid}@stocksense.ai"
    password = "SecurePassword123!"
    full_name = "Jane Doe"
    phone_number = "+919876543210"

    # Register
    res = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "full_name": full_name,
        "phone_number": phone_number
    })
    assert res.status_code == 200, f"Registration failed: {res.text}"
    data = res.json()["data"]
    assert data["full_name"] == full_name
    assert "user_id" in data

    # Login
    login_res = client.post("/api/v1/auth/login", json={
        "username_or_email": email,
        "password": password
    })
    assert login_res.status_code == 200
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get Profile
    profile_res = client.get("/api/v1/user/profile", headers=headers)
    assert profile_res.status_code == 200
    pdata = profile_res.json()["data"]
    assert pdata["full_name"] == full_name
    assert pdata["whatsapp"]["phone_masked"] == "+91******3210"


def test_user_preferences_alerts_serialization():
    """Verify alerts and AI settings are correctly serialized inside preferences json."""
    uid = uuid.uuid4().hex[:8]
    email = f"user_{uid}@stocksense.ai"
    password = "SecurePassword123!"
    full_name = "John Preferences"

    # Register & Login
    client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "full_name": full_name
    })
    token = client.post("/api/v1/auth/login", json={
        "username_or_email": email,
        "password": password
    }).json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Patch alerts and AI settings preferences
    patch_res = client.patch("/api/v1/user/preferences", json={
        "alerts": {
            "liquidity_sweep": False,
            "confluence_threshold": 85
        },
        "ai_settings": {
            "preferred_analysis_mode": "Aggressive",
            "signal_sensitivity": 70
        }
    }, headers=headers)
    assert patch_res.status_code == 200
    pdata = patch_res.json()["data"]
    
    assert pdata["alerts"]["liquidity_sweep"] is False
    assert pdata["alerts"]["confluence_threshold"] == 85
    assert pdata["alerts"]["bos"] is True  # Default remains true
    assert pdata["ai_settings"]["preferred_analysis_mode"] == "Aggressive"
    assert pdata["ai_settings"]["signal_sensitivity"] == 70


def test_admin_diagnostics_protection():
    """Verify regular users cannot access diagnostics and admins can."""
    uid = uuid.uuid4().hex[:8]
    email = f"regular_{uid}@stocksense.ai"
    password = "SecurePassword123!"
    
    # 1. Regular User Access
    client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "Regular User"
    })
    reg_token = client.post("/api/v1/auth/login", json={
        "username_or_email": email,
        "password": password
    }).json()["data"]["access_token"]
    
    res_reg = client.get("/api/admin/diagnostics", headers={"Authorization": f"Bearer {reg_token}"})
    assert res_reg.status_code == 403
    assert res_reg.json()["detail"]["code"] == "FORBIDDEN"

    # 2. Admin Access
    # We query the database session directly to promote our regular user to admin
    db = next(get_db())
    try:
        user_record = db.query(UserRecord).filter(UserRecord.email == email).first()
        user_record.role = "ADMIN"
        db.commit()
    finally:
        db.close()

    res_admin = client.get("/api/admin/diagnostics", headers={"Authorization": f"Bearer {reg_token}"})
    assert res_admin.status_code == 200
    adata = res_admin.json()["data"]
    assert adata["backend_status"] == "ONLINE"
    assert adata["database_status"] == "CONNECTED"
    assert "memory_rss_mb" in adata
    assert "model_integrity" in adata
    
    # Verify no credentials leaked
    res_text = res_admin.text.lower()
    assert "key" not in res_text
    assert "secret" not in res_text
    assert "password" not in res_text
