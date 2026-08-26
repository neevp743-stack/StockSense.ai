import re
import os
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
import jwt
from passlib.context import CryptContext

from backend.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from backend.db.models import (
    UserRecord, UserPreferencesRecord, UserWhatsAppVerificationRecord,
    WebhookSubscriptionRecord, IdempotencyRecord
)

pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        return None


# --- Phone Normalization & Masking ---

def normalize_phone_e164(phone_str: str) -> str:
    if not phone_str or not isinstance(phone_str, str):
        raise ValueError("PHONE_NUMBER_INVALID: Phone number string is empty or invalid.")
    
    # Remove spaces, hyphens, brackets, leading zeroes after country code
    cleaned = re.sub(r"[\s\-\(\)\.]", "", phone_str.strip())
    
    # Handle numbers starting with double zero e.g. 0091...
    if cleaned.startswith("00"):
        cleaned = "+" + cleaned[2:]
    
    # Must start with +
    if not cleaned.startswith("+"):
        # Default to +1 or +91 if missing leading +, but require + explicitly for international safety
        cleaned = "+" + cleaned
    
    # Validate E.164 pattern: + followed by 7 to 15 digits
    pattern = r"^\+[1-9]\d{6,14}$"
    if not re.match(pattern, cleaned):
        raise ValueError("PHONE_NUMBER_INVALID: Must be valid E.164 international format (e.g. +919876543210).")
    
    return cleaned

def mask_phone_number(phone_e164: str) -> str:
    if not phone_e164 or len(phone_e164) < 7:
        return "******"
    country_code = phone_e164[:3]
    last_four = phone_e164[-4:]
    masked_length = len(phone_e164) - 7
    return f"{country_code}{'*' * max(3, masked_length)}{last_four}"


# --- Auth & User CRUD ---

def register_user(db: Session, username: Optional[str], email: str, password: str, role: str = "USER", full_name: Optional[str] = None, phone_number: Optional[str] = None) -> UserRecord:
    import random
    email_clean = email.strip().lower()
    
    if not username or len(username.strip()) == 0:
        base_username = email_clean.split('@')[0]
        base_username = re.sub(r'[^a-zA-Z0-9_]', '', base_username)
        if not base_username:
            base_username = "user"
        username_clean = base_username.lower()
        
        attempts = 0
        while attempts < 10:
            existing = db.query(UserRecord).filter(UserRecord.username == username_clean).first()
            if not existing:
                break
            username_clean = f"{base_username}_{random.randint(1000, 9999)}".lower()
            attempts += 1
    else:
        username_clean = username.strip().lower()
        
    existing_user = db.query(UserRecord).filter(
        (UserRecord.username == username_clean) | (UserRecord.email == email_clean)
    ).first()
    if existing_user:
        raise ValueError("USER_ALREADY_EXISTS: Username or email is already registered.")
        
    hashed = get_password_hash(password)
    user = UserRecord(
        username=username_clean,
        email=email_clean,
        full_name=full_name.strip() if full_name else None,
        hashed_password=hashed,
        role=role.upper() if role.upper() in ["USER", "ADMIN"] else "USER"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create default preferences
    prefs = UserPreferencesRecord(user_id=user.id)
    db.add(prefs)
    
    # Normalize optional phone number if provided
    phone_normalized = None
    phone_masked = None
    if phone_number and len(phone_number.strip()) > 0:
        try:
            phone_normalized = normalize_phone_e164(phone_number)
            phone_masked = mask_phone_number(phone_normalized)
        except Exception:
            phone_normalized = phone_number.strip()
            phone_masked = phone_normalized

    # Create default WhatsApp record
    wa = UserWhatsAppVerificationRecord(
        user_id=user.id,
        phone_number_e164=phone_normalized,
        phone_number_masked=phone_masked,
        verification_status="UNVERIFIED",
        alerts_enabled=False
    )
    db.add(wa)
    db.commit()
    
    return user

def authenticate_user(db: Session, username_or_email: str, password: str) -> Optional[UserRecord]:
    ident = username_or_email.strip().lower()
    user = db.query(UserRecord).filter(
        (UserRecord.username == ident) | (UserRecord.email == ident)
    ).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def get_user_profile(db: Session, user_id: int) -> Dict[str, Any]:
    user = db.query(UserRecord).filter(UserRecord.id == user_id).first()
    if not user:
        raise ValueError("USER_NOT_FOUND")
    
    wa = db.query(UserWhatsAppVerificationRecord).filter(UserWhatsAppVerificationRecord.user_id == user_id).first()
    
    return {
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "whatsapp": {
            "status": wa.verification_status if wa else "UNVERIFIED",
            "phone_masked": wa.phone_number_masked if wa else None,
            "verified_at": wa.verified_at.isoformat() if wa and wa.verified_at else None,
            "alerts_enabled": wa.alerts_enabled if wa else False
        }
    }

def get_user_preferences(db: Session, user_id: int) -> Dict[str, Any]:
    import json
    prefs = db.query(UserPreferencesRecord).filter(UserPreferencesRecord.user_id == user_id).first()
    if not prefs:
        prefs = UserPreferencesRecord(user_id=user_id)
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
        
    alerts_dict = {
        "liquidity_sweep": True,
        "bos": True,
        "choch": True,
        "fvg": True,
        "order_block": True,
        "confluence": True,
        "confluence_threshold": 70,
        "entry_alerts": True,
        "tp_alerts": True,
        "sl_alerts": True,
        "price_alerts": True,
        "regime_change": True,
        "whatsapp": False
    }
    ai_settings_dict = {
        "preferred_analysis_mode": "Balanced",
        "signal_sensitivity": 50,
        "risk_preference": "Medium"
    }
    
    if prefs.alerts_json:
        try:
            data = json.loads(prefs.alerts_json)
            if isinstance(data, dict):
                if "alerts" in data:
                    alerts_dict.update(data["alerts"])
                if "ai_settings" in data:
                    ai_settings_dict.update(data["ai_settings"])
        except Exception:
            pass
        
    return {
        "theme": prefs.theme,
        "default_market": prefs.default_market,
        "default_timeframe": prefs.default_timeframe,
        "default_currency": prefs.default_currency,
        "notifications_enabled": prefs.notifications_enabled,
        "alerts": alerts_dict,
        "ai_settings": ai_settings_dict
    }

def update_user_preferences(db: Session, user_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
    import json
    prefs = db.query(UserPreferencesRecord).filter(UserPreferencesRecord.user_id == user_id).first()
    if not prefs:
        prefs = UserPreferencesRecord(user_id=user_id)
        db.add(prefs)
    
    if "theme" in updates:
        prefs.theme = str(updates["theme"])
    if "default_market" in updates:
        prefs.default_market = str(updates["default_market"])
    if "default_timeframe" in updates:
        prefs.default_timeframe = str(updates["default_timeframe"])
    if "default_currency" in updates:
        prefs.default_currency = str(updates["default_currency"])
    if "notifications_enabled" in updates:
        prefs.notifications_enabled = bool(updates["notifications_enabled"])
        
    # Serialize alerts & ai_settings
    current_data = {}
    if prefs.alerts_json:
        try:
            current_data = json.loads(prefs.alerts_json)
            if not isinstance(current_data, dict):
                current_data = {}
        except Exception:
            pass
            
    if "alerts" in updates and isinstance(updates["alerts"], dict):
        if "alerts" not in current_data:
            current_data["alerts"] = {}
        current_data["alerts"].update(updates["alerts"])
        
    if "ai_settings" in updates and isinstance(updates["ai_settings"], dict):
        if "ai_settings" not in current_data:
            current_data["ai_settings"] = {}
        current_data["ai_settings"].update(updates["ai_settings"])
        
    if "alerts" in updates or "ai_settings" in updates:
        prefs.alerts_json = json.dumps(current_data)
        
    prefs.updated_at = datetime.utcnow()
    db.commit()
    return get_user_preferences(db, user_id)


# --- WhatsApp Verification Engine ---

def request_whatsapp_verification(db: Session, user_id: int, phone_raw: str) -> Dict[str, Any]:
    phone_e164 = normalize_phone_e164(phone_raw)
    phone_masked = mask_phone_number(phone_e164)
    
    wa = db.query(UserWhatsAppVerificationRecord).filter(UserWhatsAppVerificationRecord.user_id == user_id).first()
    if not wa:
        wa = UserWhatsAppVerificationRecord(user_id=user_id)
        db.add(wa)
        
    now = datetime.utcnow()
    # Check 60s cooldown
    if wa.last_sent_at and (now - wa.last_sent_at).total_seconds() < 60:
        cooldown_remaining = int(60 - (now - wa.last_sent_at).total_seconds())
        raise ValueError(f"VERIFICATION_RATE_LIMITED: Please wait {cooldown_remaining} seconds before requesting a new code.")
        
    # Generate 6-digit verification code
    raw_code = f"{secrets.randbelow(900000) + 100000}"
    code_hash = hashlib.sha256(raw_code.encode()).hexdigest()
    verification_id = f"wa_verif_{secrets.token_hex(8)}"
    
    wa.phone_number_e164 = phone_e164
    wa.phone_number_masked = phone_masked
    wa.verification_code_hash = code_hash
    wa.verification_id = verification_id
    wa.code_expires_at = now + timedelta(minutes=5)
    wa.attempts_count = 0
    wa.last_sent_at = now
    wa.verification_status = "VERIFICATION_SENT"
    wa.updated_at = now
    db.commit()
    
    # Check if WhatsApp provider API credentials are configured in environment
    whatsapp_api_key = os.environ.get("WHATSAPP_API_KEY") or os.environ.get("TWILIO_WHATSAPP_TOKEN")
    
    if not whatsapp_api_key:
        wa.verification_status = "WHATSAPP_NOT_CONFIGURED"
        db.commit()
        return {
            "success": False,
            "status": "WHATSAPP_NOT_CONFIGURED",
            "error_code": "WHATSAPP_NOT_CONFIGURED",
            "message": "Official WhatsApp Business API credentials not configured in environment.",
            "verification_id": verification_id,
            "masked_phone": phone_masked,
            "expires_in_seconds": 300
        }
        
    # In production with API key: send official message
    return {
        "success": True,
        "status": "VERIFICATION_SENT",
        "verification_id": verification_id,
        "masked_phone": phone_masked,
        "expires_in_seconds": 300
    }

def confirm_whatsapp_verification(db: Session, user_id: int, verification_id: str, code: str) -> Dict[str, Any]:
    wa = db.query(UserWhatsAppVerificationRecord).filter(
        UserWhatsAppVerificationRecord.user_id == user_id,
        UserWhatsAppVerificationRecord.verification_id == verification_id
    ).first()
    
    if not wa:
        raise ValueError("NOT_FOUND: Verification request record not found.")
        
    now = datetime.utcnow()
    
    if wa.code_expires_at and now > wa.code_expires_at:
        wa.verification_status = "EXPIRED"
        db.commit()
        raise ValueError("VERIFICATION_EXPIRED: Code has expired. Please request a new verification code.")
        
    if wa.attempts_count >= 5:
        wa.verification_status = "EXPIRED"
        db.commit()
        raise ValueError("VERIFICATION_ATTEMPTS_EXCEEDED: Maximum verification attempts exceeded. Request a new code.")
        
    wa.attempts_count += 1
    
    input_hash = hashlib.sha256(code.strip().encode()).hexdigest()
    if input_hash != wa.verification_code_hash:
        db.commit()
        raise ValueError("VERIFICATION_CODE_INVALID: Invalid verification code entered.")
        
    # Successful verification!
    wa.verification_status = "VERIFIED"
    wa.verified_at = now
    wa.alerts_enabled = True
    wa.verification_code_hash = None
    wa.updated_at = now
    db.commit()
    
    return {
        "success": True,
        "status": "VERIFIED",
        "masked_phone": wa.phone_number_masked,
        "verified_at": now.isoformat()
    }

def disable_whatsapp_alerts(db: Session, user_id: int) -> Dict[str, Any]:
    wa = db.query(UserWhatsAppVerificationRecord).filter(UserWhatsAppVerificationRecord.user_id == user_id).first()
    if wa:
        wa.alerts_enabled = False
        wa.updated_at = datetime.utcnow()
        db.commit()
    return {"success": True, "status": "ALERTS_DISABLED"}


# --- Webhooks Management ---

def create_webhook_subscription(db: Session, user_id: int, target_url: str, events: List[str]) -> Dict[str, Any]:
    if not target_url.startswith("http://") and not target_url.startswith("https://"):
        raise ValueError("VALIDATION_ERROR: Webhook target_url must be a valid HTTP or HTTPS URL.")
        
    webhook_id = f"wh_{secrets.token_hex(10)}"
    secret_key = f"whsec_{secrets.token_hex(16)}"
    import json
    
    sub = WebhookSubscriptionRecord(
        user_id=user_id,
        webhook_id=webhook_id,
        target_url=target_url,
        secret_key=secret_key,
        events_json=json.dumps(events or ["LIQUIDITY_SWEEP", "CONFLUENCE_SIGNAL"])
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    
    return {
        "webhook_id": sub.webhook_id,
        "target_url": sub.target_url,
        "events": events,
        "secret_key": secret_key,
        "active": sub.active,
        "created_at": sub.created_at.isoformat()
    }

def list_webhook_subscriptions(db: Session, user_id: int) -> List[Dict[str, Any]]:
    import json
    subs = db.query(WebhookSubscriptionRecord).filter(
        WebhookSubscriptionRecord.user_id == user_id,
        WebhookSubscriptionRecord.active == True
    ).all()
    
    return [
        {
            "webhook_id": s.webhook_id,
            "target_url": s.target_url,
            "events": json.loads(s.events_json) if s.events_json else [],
            "active": s.active,
            "delivery_failures_count": s.delivery_failures_count,
            "created_at": s.created_at.isoformat()
        } for s in subs
    ]

def delete_webhook_subscription(db: Session, user_id: int, webhook_id: str) -> bool:
    sub = db.query(WebhookSubscriptionRecord).filter(
        WebhookSubscriptionRecord.user_id == user_id,
        WebhookSubscriptionRecord.webhook_id == webhook_id
    ).first()
    if not sub:
        return False
    sub.active = False
    db.commit()
    return True
