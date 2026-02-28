"""
Migration 001: Security Hardening

This migration:
- Adds validators to enforce data integrity
- Creates critical unique indexes
- Sets up TTL index for refresh token expiration
- Configures strict validation mode

Run during startup if validators/indexes don't exist
"""
from typing import Dict, Any


async def apply(db) -> Dict[str, Any]:
    """
    Apply migration 001 - security hardening
    
    Returns: Migration result summary
    """
    from backend.db.validators import (
        get_users_validator,
        get_refresh_tokens_validator,
        get_daily_entries_validator,
        enforce_corrected_validation,
        setup_critical_unique_indexes
    )
    
    result = {
        "migration": "001_hardening",
        "status": "success",
        "changes": []
    }
    
    try:
        # Apply validators
        enforce_corrected_validation(db)
        result["changes"].append("validators_applied")
        
        # Create unique indexes
        setup_critical_unique_indexes(db)
        result["changes"].append("unique_indexes_created")
        
        # Setup all indexes
        from backend.db.indexes import setup_indexes
        setup_indexes(db)
        result["changes"].append("all_indexes_setup")
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
    
    return result


async def rollback(db) -> Dict[str, Any]:
    """
    Rollback migration 001
    
    WARNING: This will remove data integrity protections!
    Only use in development environments.
    """
    result = {
        "migration": "001_hardening",
        "status": "success",
        "changes": []
    }
    
    try:
        # Drop unique indexes
        try:
            db.users.drop_index("email_1")
            result["changes"].append("dropped_users_email_index")
        except Exception:
            pass
        
        try:
            db.refresh_tokens.drop_index("jti_1")
            result["changes"].append("dropped_refresh_tokens_jti_index")
        except Exception:
            pass
        
        try:
            db.daily_entries.drop_index("user_id_1_date_1")
            result["changes"].append("dropped_daily_entries_unique_index")
        except Exception:
            pass
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
    
    return result


if __name__ == "__main__":
    import asyncio
    from motor.motor_asyncio import AsyncIOMotorClient
    import os
    
    async def main():
        client = AsyncIOMotorClient(os.getenv("MONGO_URL"))
        db = client[os.getenv("DB_NAME", "kpi_tracker")]
        
        print("Applying migration 001...")
        result = await apply(db)
        print(f"Result: {result}")
        
        client.close()
    
    asyncio.run(main())
