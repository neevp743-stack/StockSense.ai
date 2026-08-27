# StockSense AI — Project Naming & Documentation Standards

**Official Product Name:** StockSense AI  
**Repository Name:** `Stock Sense Ai`  
**Production Backend URL:** `https://stocksense-ai-backend-sdyo.onrender.com`  
**Production Frontend URL:** `https://stock-sense-ai-lilac.vercel.app`  

---

## 1. Naming Guidelines

1. **Product & Brand Identity:**  
   The project must always be referenced as **StockSense AI** (or `StockSense AI` in technical specs). Avoid unofficial shorthand or inconsistent casing.

2. **Production Feature Naming Standard:**  
   - **Production Watchtower & Uptime Monitoring:** Must be referenced strictly as `StockSense AI — Production Watchtower & Uptime Monitoring`. Do NOT assign Phase numbers to this monitoring system.
   - **Production Stability Validation:** Must be referenced strictly as `StockSense AI — Production Stability Validation`.

3. **Database & Service Layer Naming:**  
   - Database tables must use lowercase snake_case (`watchtower_state`, `watchtower_checks`, `assets`, `users`).
   - Service classes must use PascalCase (`ProductionWatchtower`, `UserService`).
   - API endpoints must follow RESTful standards (`/api/v1/...`, `/api/watchtower/...`).

---

## 2. Security & Redaction Standards

- Never print or log secret environment variable values (`CRON_SECRET`, `JWT_SECRET`, `TWELVE_DATA_API_KEY`, passwords, or `.env` contents).
- Maintain test user account standard: `test@stocksense.local` / `StockSense@2026` with `ROLE = USER` and `STATUS = ACTIVE`.
