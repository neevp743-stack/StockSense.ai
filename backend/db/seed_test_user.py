"""
StockSense AI — Standalone Development/Testing Seed Script (Phase 21.9.2)
Seeds or safely updates the development/test account in local/test databases.

USAGE:
    python backend/db/seed_test_user.py

IMPORTANT SECURITY RULES:
- This script MUST NOT be invoked automatically during production Render startup.
- Plaintext passwords, password hashes, JWT secrets, and API keys are NEVER logged or printed.
- The test account is strictly granted ROLE = USER (never ADMIN).
"""

import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from backend.db.database import SessionLocal, init_db
from backend.db.models import UserRecord, UserPreferencesRecord
from backend.services.user_service import get_password_hash

TEST_EMAIL = "test@stocksense.local"
TEST_USERNAME = "stocksense_test_user"
TEST_FULL_NAME = "StockSense Test User"
TEST_RAW_PASSWORD = "StockSense@2026"
TEST_ROLE = "USER"


def seed_test_user():
    init_db()
    db = SessionLocal()
    try:
        email_clean = TEST_EMAIL.strip().lower()
        user = db.query(UserRecord).filter(
            (UserRecord.email == email_clean) | (UserRecord.username == TEST_USERNAME)
        ).first()

        hashed = get_password_hash(TEST_RAW_PASSWORD)

        if user:
            user.hashed_password = hashed
            user.full_name = TEST_FULL_NAME
            user.role = TEST_ROLE
            db.commit()
            db.refresh(user)
            print(f"SUCCESS: Test account '{email_clean}' updated cleanly. Role: {user.role}")
        else:
            new_user = UserRecord(
                username=TEST_USERNAME,
                email=email_clean,
                full_name=TEST_FULL_NAME,
                hashed_password=hashed,
                role=TEST_ROLE
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)

            # Seed default preferences record
            prefs = db.query(UserPreferencesRecord).filter(UserPreferencesRecord.user_id == new_user.id).first()
            if not prefs:
                db.add(UserPreferencesRecord(user_id=new_user.id))
                db.commit()

            print(f"SUCCESS: Test account '{email_clean}' created cleanly. User ID: {new_user.id}, Role: {new_user.role}")

    except Exception as e:
        db.rollback()
        print(f"ERROR: Failed to seed test account: {type(e).__name__}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    seed_test_user()
