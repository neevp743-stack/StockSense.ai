# StockSense AI — Security & Compliance Specification

**Feature:** Security & Compliance Specification  
**Encryption Standard:** Bcrypt (12 rounds) for passwords, HMAC-SHA256 for JWT tokens  
**CORS Restriction:** `https://stock-sense-ai-lilac.vercel.app`  

---

## 1. Authentication & Role-Based Access Control (RBAC)

1. **JWT Access Tokens:** Issued upon successful authentication (`POST /api/v1/auth/login`). Subject claim contains stringified `user_id`, username, and role.
2. **User Roles:**
   - `USER`: Standard permissions for dashboard, market quotes, candles, predictions, and personal profile settings. Access to `/api/admin/*` is strictly blocked with **`403 Forbidden`**.
   - `ADMIN`: Authorized administrators with access to system diagnostics (`/api/admin/diagnostics`), telemetry, and infrastructure controls.
3. **Unauthenticated Access:** Requests to protected endpoints without a valid `Bearer` header return **`401 Unauthorized`**.

---

## 2. Secret Protection & Masking Rules

- **Zero Plaintext Secrets:** Plaintext passwords, password hashes, JWT secrets (`SECRET_KEY`), `CRON_SECRET`, and external API keys (`TWELVE_DATA_API_KEY`, `WHATSAPP_API_KEY`) are NEVER logged, printed in reports, or exposed in frontend static dist bundles.
- **Git Tracking Isolation:** `.env` files are explicitly listed in `.gitignore` and MUST NOT be tracked in Git.
- **Cron Protection:** The Watchtower trigger endpoint (`/api/watchtower/cron`) verifies `CRON_SECRET` authorization (`Authorization: Bearer <CRON_SECRET>`) and rejects unauthorized calls with `401 Unauthorized`.

---

## 3. CORS Policy & Web Security Headers

- **Allowed Origin:** Production backend Access-Control-Allow-Origin header is strictly configured for `https://stock-sense-ai-lilac.vercel.app`.
- **Preflight CORS:** HTTP OPTIONS preflight requests return `200 OK` with allowable headers (`Authorization`, `Content-Type`, `X-Process-Time-Ms`).
