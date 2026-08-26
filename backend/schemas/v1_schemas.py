from typing import Generic, TypeVar, Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

T = TypeVar("T")

class ResponseMeta(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    request_id: str = "req_unknown"
    version: str = "v1"

class StandardResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T
    meta: ResponseMeta

class ErrorDetail(BaseModel):
    code: str
    message: str

class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail
    meta: ResponseMeta

# Auth Schemas
class UserRegisterRequest(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None
    username: Optional[str] = None
    phone_number: Optional[str] = None

class UserLoginRequest(BaseModel):
    username_or_email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int = 14400

# WhatsApp Verification Schemas
class WhatsAppVerifyRequest(BaseModel):
    phone_number: str

class WhatsAppConfirmRequest(BaseModel):
    verification_id: str
    code: str

# Webhook Schemas
class WebhookCreateRequest(BaseModel):
    target_url: str
    events: List[str] = ["LIQUIDITY_SWEEP", "CONFLUENCE_SIGNAL"]

# Preferences Schemas
class UserPreferencesUpdateRequest(BaseModel):
    theme: Optional[str] = None
    default_market: Optional[str] = None
    default_timeframe: Optional[str] = None
    default_currency: Optional[str] = None
    notifications_enabled: Optional[bool] = None
    alerts: Optional[Dict[str, Any]] = None
    ai_settings: Optional[Dict[str, Any]] = None

# Pagination Schemas
class PaginationMeta(BaseModel):
    page: int
    limit: int
    total_records: int
    has_more: bool
