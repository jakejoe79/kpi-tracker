"""
Token management - JWT access tokens and opaque refresh tokens
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
import secrets
import bcrypt
from jose import jwt
from fastapi import HTTPException, status

# db will be injected at runtime to avoid circular imports
db = None

# Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "dev-fake-secret-change-me!")
JWT_ALGO = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 30

# Key management with versioning for rotation
JWT_KEYS = {}  # Loaded at startup from secure storage or HSM


def load_jwt_keys() -> None:
    """Load multiple key versions for rotation."""
    # Current key
    JWT_KEYS["2024-01"] = {
        "secret": os.getenv("JWT_SECRET_2024_01", JWT_SECRET),
        "algorithm": "HS256"
    }
    # Previous key (for validating old tokens during rotation window)
    JWT_KEYS["2023-12"] = {
        "secret": os.getenv("JWT_SECRET_2023_12", JWT_SECRET),
        "algorithm": "HS256"
    }


def get_current_key_id() -> str:
    """Get the current key ID for token creation."""
    return "2024-01"


def create_access_token(user_id: str, tier: str, role: str) -> str:
    """
    Create JWT access token with key ID for rotation support
    
    Returns: JWT access token string
    """
    current_key_id = get_current_key_id()
    key = JWT_KEYS[current_key_id]
    
    access_payload = {
        "sub": user_id,
        "kid": current_key_id,  # Key identifier for rotation
        "tier": tier,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    
    return jwt.encode(
        access_payload,
        key["secret"],
        algorithm=key["algorithm"],
        headers={"kid": current_key_id}
    )


def decode_access_token(token: str) -> Dict:
    """
    Decode JWT access token with key rotation support
    
    Returns: payload dict with sub, tier, role, exp
    Raises: HTTPException(401) if invalid
    """
    # Decode without verification first to get kid
    try:
        unverified = jwt.decode(token, options={"verify_signature": False})
        kid = unverified.get("kid", "2023-12")  # Default to old key for legacy
    except jwt.JWTError:
        kid = "2023-12"  # Fallback for tokens without kid claim
    
    if kid not in JWT_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token (unknown key)",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    key = JWT_KEYS[kid]
    
    try:
        return jwt.decode(token, key["secret"], algorithms=[key["algorithm"]])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token expired",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def create_tokens(user_id: str, tier: str, role: str) -> Dict:
    """
    Create both access (JWT) and refresh (opaque) tokens
    
    Returns: {
        "access": str,      # JWT access token (15 min expiry)
        "refresh": str,     # Opaque refresh token (30 days)
        "jti": str,         # Refresh token ID for revocation
        "token_type": "bearer"
    }
    """
    if db is None:
        raise RuntimeError("db not initialized - call init_db() first")
    
    # JWT Access Token (short-lived, stateless)
    access_token = create_access_token(user_id, tier, role)
    
    # Opaque Refresh Token (long-lived, revocable, hashed in DB)
    jti = secrets.token_urlsafe(32)
    plain_refresh = secrets.token_urlsafe(64)
    token_hash = bcrypt.hashpw(plain_refresh.encode(), bcrypt.gensalt()).decode()
    
    # Store refresh token in DB
    await db.refresh_tokens.insert_one({
        "jti": jti,
        "user_id": user_id,
        "token_hash": token_hash,
        "created_at": {"$currentDate": True},
        "expires_at": datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        "revoked": False,
        "revoked_at": None
    })
    
    return {
        "access": access_token,
        "refresh": plain_refresh,
        "jti": jti,
        "token_type": "bearer"
    }


async def validate_access_token(token: str) -> Dict:
    """
    Validate a JWT access token (alias for decode_access_token)
    
    Returns: payload dict with sub, tier, exp
    Raises: HTTPException(401) if invalid
    """
    return decode_access_token(token)


async def validate_refresh_token(refresh_token: str, jti: str) -> Optional[Dict]:
    """
    Validate a refresh token and return its DB record
    
    Returns: DB document if valid, None if invalid/expired/revoked
    """
    if db is None:
        raise RuntimeError("db not initialized - call init_db() first")
    
    doc = await db.refresh_tokens.find_one({"jti": jti})
    
    if not doc:
        return None
    
    if doc.get("revoked", False):
        return None
    
    if doc.get("expires_at", datetime.min) < datetime.now(timezone.utc):
        return None
    
    if not bcrypt.checkpw(refresh_token.encode(), doc["token_hash"].encode()):
        return None
    
    return doc


async def rotate_refresh_token(refresh_token: str, jti: str) -> Dict:
    """
    Rotate refresh token - revoke old, create new
    
    Returns: New token set
    Raises: HTTPException(401) if rotation fails
    """
    if db is None:
        raise RuntimeError("db not initialized - call init_db() first")
    
    # Validate old token
    doc = await validate_refresh_token(refresh_token, jti)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Revoke old token
    await db.refresh_tokens.update_one(
        {"jti": jti},
        {
            "$set": {
                "revoked": True,
                "revoked_at": {"$currentDate": True},
                "rotated_to": secrets.token_urlsafe(32)  # Track rotation
            }
        }
    )
    
    # Get user info
    user = await db.users.find_one({"id": doc["user_id"]})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Create new tokens
    return await create_tokens(user["id"], user.get("tier", "pro"), user.get("role", "member"))


async def revoke_token(jti: str) -> bool:
    """
    Revoke a refresh token by JTI
    
    Returns: True if token was revoked
    """
    if db is None:
        raise RuntimeError("db not initialized - call init_db() first")
    
    result = await db.refresh_tokens.update_one(
        {"jti": jti},
        {
            "$set": {
                "revoked": True,
                "revoked_at": {"$currentDate": True}
            }
        }
    )
    return result.modified_count > 0


async def revoke_user_tokens(user_id: str) -> int:
    """
    Revoke all refresh tokens for a user (e.g., on password change)
    
    Returns: Number of tokens revoked
    """
    if db is None:
        raise RuntimeError("db not initialized - call init_db() first")
    
    result = await db.refresh_tokens.update_many(
        {"user_id": user_id},
        {
            "$set": {
                "revoked": True,
                "revoked_at": {"$currentDate": True}
            }
        }
    )
    return result.modified_count


async def cleanup_expired_tokens() -> int:
    """
    Clean up expired and revoked tokens
    
    Returns: Number of tokens deleted
    """
    if db is None:
        raise RuntimeError("db not initialized - call init_db() first")
    
    result = await db.refresh_tokens.delete_many({
        "$or": [
            {"expires_at": {"$lt": datetime.now(timezone.utc)}},
            {"revoked": True}
        ]
    })
    return result.deleted_count