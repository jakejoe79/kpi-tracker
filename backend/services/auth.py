"""
Authentication utilities - password hashing and verification
"""
import bcrypt
import re
from fastapi import HTTPException, status
from datetime import datetime, timezone

# db will be injected at runtime to avoid circular imports
db = None


def normalize_and_validate_email(email: str) -> str:
    """Normalize and validate an email address."""
    if not email or not isinstance(email, str):
        raise ValueError("Email must be a non-empty string")
    
    # Normalize: lowercase and strip whitespace
    email = email.lower().strip()
    
    # Basic validation regex
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValueError(f"Invalid email format: {email}")
    
    return email


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hash_: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode(), hash_.encode())


def get_password_hash_field() -> dict:
    """Return the password_hash field definition for MongoDB validator"""
    return {
        "password_hash": {
            "bsonType": "string",
            "minLength": 60,
            "maxLength": 255,
            "pattern": "^\\$2[aby]?\\$\\d{2}\\$[./A-Za-z0-9]{53}"
        }
    }


def get_allowed_create_fields() -> list:
    """Return list of fields allowed during user creation (excludes password_hash)"""
    return [
        "id", "email", "plan", "company_id", "team_id", "created_at"
    ]


async def revoke_all_user_tokens(user_id: str, reason: str = "manual") -> int:
    """
    Revoke all refresh tokens for a user (e.g., on logout-all)
    
    Returns: Number of tokens revoked
    """
    if db is None:
        raise RuntimeError("db not initialized - call init_db() first")
    
    from .tokens import revoke_user_tokens
    
    # Revoke all tokens
    count = await revoke_user_tokens(user_id)
    
    # Update user's last_logout timestamp
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"last_logout": datetime.now(timezone.utc)}}
    )
    
    return count
