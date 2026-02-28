"""
User management utilities
"""
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from backend.server import db
from services.auth import hash_password, get_allowed_create_fields


async def create_user(email: str, password: str, plan: str = "free", 
                      company_id: str = "", team_id: str = "") -> dict:
    """
    Create a new user with hashed password
    
    Args:
        email: User's email (will be validated and normalized)
        password: Plain text password (will be hashed)
        plan: User's subscription plan
        company_id: Tenant company ID (for multi-tenant)
        team_id: Team ID within company (for multi-tenant)
    
    Returns:
        Created user document (without password_hash)
    
    Raises:
        ValueError: If email is invalid or user already exists
    """
    from services.auth import normalize_and_validate_email
    
    # Validate and normalize email
    normalized_email = normalize_and_validate_email(email)
    
    # Check if user already exists
    existing = await db.users.find_one({"email": normalized_email})
    if existing:
        raise ValueError("User with this email already exists")
    
    # Create user document
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    created_at = datetime.utcnow()
    
    user_doc = {
        "id": user_id,
        "email": normalized_email,
        "plan": plan,
        "password_hash": hash_password(password),
        "company_id": company_id,
        "team_id": team_id,
        "created_at": created_at,
        "updated_at": created_at
    }
    
    # Insert into database
    await db.users.insert_one(user_doc)
    
    # Return user without password_hash
    return {k: v for k, v in user_doc.items() if k != "password_hash"}


async def update_user(user_id: str, updates: Dict[str, Any]) -> Optional[dict]:
    """
    Update user fields (excluding sensitive fields)
    
    Args:
        user_id: User ID to update
        updates: Dictionary of fields to update
    
    Returns:
        Updated user document or None if not found
    
    Raises:
        ValueError: If trying to update immutable fields
    """
    from services.auth import normalize_and_validate_email
    
    # Immutable fields that cannot be updated
    immutable_fields = {"id", "email", "created_at"}
    
    # Check for immutable field updates
    for field in immutable_fields:
        if field in updates:
            raise ValueError(f"Cannot update immutable field: {field}")
    
    # Normalize email if being updated
    if "email" in updates:
        updates["email"] = normalize_and_validate_email(updates["email"])
    
    # Only allow whitelisted fields
    allowed_fields = get_allowed_create_fields()
    safe_updates = {k: v for k, v in updates.items() if k in allowed_fields}
    
    if not safe_updates:
        return None
    
    # Add timestamp
    safe_updates["updated_at"] = datetime.utcnow()
    
    # Update in database
    result = await db.users.find_one_and_update(
        {"id": user_id},
        {"$set": safe_updates},
        return_document=True
    )
    
    if result:
        # Remove password_hash from response
        return {k: v for k, v in result.items() if k != "password_hash"}
    
    return None


async def get_user_by_id(user_id: str) -> Optional[dict]:
    """Get user by ID"""
    user = await db.users.find_one({"id": user_id})
    if user:
        # Remove password_hash from response
        return {k: v for k, v in user.items() if k != "password_hash"}
    return None


async def get_user_by_email(email: str) -> Optional[dict]:
    """Get user by email"""
    user = await db.users.find_one({"email": email.lower()})
    if user:
        # Remove password_hash from response
        return {k: v for k, v in user.items() if k != "password_hash"}
    return None


async def delete_user(user_id: str) -> bool:
    """Delete a user"""
    result = await db.users.delete_one({"id": user_id})
    return result.deleted_count > 0
