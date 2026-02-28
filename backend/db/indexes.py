"""
Database indexes - setup and management
"""
from typing import Dict, Any


def setup_indexes(db) -> None:
    """
    Setup all database indexes
    Call this during startup
    
    Indexes:
    - users.email: Unique - prevents duplicate accounts
    - users.id: Unique - prevents ID collision attacks
    - users.company_id + is_active: Compound - fast tenant queries
    - users.team_id + is_active: Compound - fast team queries
    - refresh_tokens.jti: Unique - prevents token duplication
    - refresh_tokens.user_id + revoked + expires_at: Compound - fast revocation
    - refresh_tokens.expires_at: TTL - auto-cleanup
    - invitations.token: Unique - prevents invite collision
    - teams.company_id + name: Unique - prevents duplicate team names
    """
    # Users indexes
    db.users.create_index("email", unique=True, name="email_unique")
    db.users.create_index("id", unique=True, name="id_unique")
    db.users.create_index([("company_id", 1), ("is_active", 1)])
    db.users.create_index([("team_id", 1), ("is_active", 1)])
    
    # Refresh tokens indexes
    db.refresh_tokens.create_index("jti", unique=True, name="jti_unique")
    db.refresh_tokens.create_index([("user_id", 1), ("revoked", 1), ("expires_at", 1)])
    db.refresh_tokens.create_index("expires_at", expireAfterSeconds=0)  # TTL index
    
    # Invitations indexes
    db.invitations.create_index("token", unique=True, name="token_unique")
    
    # Teams indexes
    db.teams.create_index(
        [("company_id", 1), ("name", 1)],
        unique=True,
        name="company_team_name_unique",
        partialFilterExpression={"company_id": {"$ne": None}}  # Only for company teams
    )
    
    # Daily entries indexes
    db.daily_entries.create_index([("user_id", 1), ("date", 1)], unique=True)
    db.daily_entries.create_index([("user_id", 1), ("period_id", 1)])
    db.daily_entries.create_index("archived")
    
    # Period logs indexes
    db.period_logs.create_index([("user_id", 1), ("period_id", 1)], unique=True)
    
    # User goals indexes
    db.user_goals.create_index("user_id", unique=True)
    
    # Daily archives indexes
    db.daily_archives.create_index([("user_id", 1), ("date", 1), ("type", 1)])
    
    # Daily snapshots indexes
    db.daily_snapshots.create_index([("user_id", 1), ("period_id", 1), ("snapshot_date", 1)])
    db.daily_snapshots.create_index("generated_at")
    
    # Alert cooldowns indexes
    db.alert_cooldowns.create_index("key", unique=True)
    db.alert_cooldowns.create_index("timestamp")
    
    # Signal history indexes
    db.signal_history.create_index([("user_id", 1), ("timestamp", -1)])


async def verify_unique_indexes(db) -> None:
    """
    Fail startup if unique indexes missing - cannot operate safely
    """
    required = {
        "users": ["email_unique", "id_unique"],
        "refresh_tokens": ["jti_unique"],
        "invitations": ["token_unique"]
    }
    
    for collection, indexes in required.items():
        info = await db[collection].index_information()
        for idx in indexes:
            if idx not in info:
                raise RuntimeError(
                    f"FATAL: Missing unique index {idx} on {collection}. "
                    f"Cannot guarantee identity integrity. Refusing to start."
                )
            if not info[idx].get("unique"):
                raise RuntimeError(
                    f"FATAL: Index {idx} exists but is not unique. "
                    f"Data corruption risk. Refusing to start."
                )
    
    logger.info("All critical unique indexes verified")
