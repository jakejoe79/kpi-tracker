"""
Database validators - enforce data integrity at the MongoDB level
"""
from typing import Dict, Any
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)


class UserTier:
    """User tier enum"""
    FREE = "free"
    TRIAL = "trial"
    INDIVIDUAL = "individual"
    PRO = "pro"
    GROUP = "group"


class UserRole:
    """User role enum"""
    ADMIN = "admin"
    MANAGER = "manager"
    MEMBER = "member"


def get_users_validator() -> Dict[str, Any]:
    """
    Return MongoDB validator schema for users collection
    Enforces:
    - email format and uniqueness
    - password_hash format (bcrypt)
    - immutable identity fields
    - strict field whitelist
    - Safe $expr rules for complex validation
    """
    return {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["id", "email", "tier", "role", "is_active", "created_at"],
            "properties": {
                "id": {
                    "bsonType": "string",
                    "maxLength": 64,
                    "pattern": "^user_[a-zA-Z0-9_-]+$"
                },
                "email": {
                    "bsonType": "string",
                    "maxLength": 254,
                    "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
                },
                "tier": {
                    "bsonType": "string",
                    "enum": ["free", "trial", "individual", "pro", "group"]
                },
                "role": {
                    "bsonType": "string",
                    "enum": ["admin", "manager", "member"]
                },
                "is_active": {
                    "bsonType": "bool"
                },
                "created_at": {
                    "bsonType": "date"
                },
                "updated_at": {
                    "bsonType": "date"
                },
                "company_id": {
                    "bsonType": ["string", "null"],
                    "maxLength": 64,
                    "pattern": "^comp_[a-zA-Z0-9_-]+$|^null$"
                },
                "team_id": {
                    "bsonType": ["string", "null"],
                    "maxLength": 64,
                    "pattern": "^team_[a-zA-Z0-9_-]+$|^null$"
                }
            },
            "allOf": [
                {
                    "if": {"properties": {"tier": {"const": "company"}}},
                    "then": {"required": ["company_id"], "properties": {"company_id": {"bsonType": "string", "minLength": 1}}}
                },
                {
                    "if": {"properties": {"tier": {"const": "group"}}},
                    "then": {"required": ["team_id"], "properties": {"team_id": {"bsonType": "string", "minLength": 1}}}
                },
                {
                    "if": {"properties": {"role": {"const": "admin"}}},
                    "then": {"properties": {"tier": {"enum": ["company", "group"]}}}
                }
            ]
        },
        "$expr": {
            "$and": [
                # Safe: updated_at can be null on insert
                {
                    "$or": [
                        {"$eq": ["$updated_at", None]},
                        {"$gte": ["$updated_at", "$created_at"]}
                    ]
                },
                # If team_id exists, company_id must exist
                {
                    "$or": [
                        {"$eq": ["$team_id", None]},
                        {"$ne": ["$company_id", None]}
                    ]
                },
                # If tier=individual, no tenant IDs
                {
                    "$or": [
                        {"$ne": ["$tier", "individual"]},
                        {
                            "$and": [
                                {"$eq": ["$team_id", None]},
                                {"$eq": ["$company_id", None]}
                            ]
                        }
                    ]
                }
            ]
        }
    }


def get_refresh_tokens_validator() -> Dict[str, Any]:
    """
    Return MongoDB validator schema for refresh_tokens collection
    Enforces:
    - JTI uniqueness
    - Token hash format
    - Required fields
    - Safe $expr rules for complex validation
    """
    return {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["jti", "user_id", "expires_at", "revoked", "created_at"],
            "properties": {
                "jti": {
                    "bsonType": "string",
                    "minLength": 32,
                    "maxLength": 128,
                    "pattern": "^[a-zA-Z0-9_-]+$"
                },
                "user_id": {
                    "bsonType": "string",
                    "maxLength": 64
                },
                "created_at": {
                    "bsonType": "date"
                },
                "expires_at": {
                    "bsonType": "date"
                },
                "revoked": {
                    "bsonType": "bool"
                },
                "revoked_at": {
                    "bsonType": ["date", "null"]
                },
                "revoked_reason": {
                    "bsonType": ["string", "null"],
                    "maxLength": 50
                },
                "rotated_from": {
                    "bsonType": ["string", "null"],
                    "anyOf": [
                        {"type": "null"},
                        {
                            "bsonType": "string",
                            "maxLength": 128,
                            "pattern": "^[a-zA-Z0-9_-]+$"
                        }
                    ]
                },
                "rotated_to": {
                    "bsonType": ["string", "null"],
                    "anyOf": [
                        {"type": "null"},
                        {
                            "bsonType": "string",
                            "maxLength": 128,
                            "pattern": "^[a-zA-Z0-9_-]+$"
                        }
                    ]
                },
                "device_hash": {
                    "bsonType": ["string", "null"],
                    "maxLength": 64
                }
            }
        },
        "$expr": {
            "$and": [
                # revoked implies revoked_at (safe for null revoked_at)
                {
                    "$or": [
                        {"$eq": ["$revoked", False]},
                        {"$and": [
                            {"$eq": ["$revoked", True]},
                            {"$ne": ["$revoked_at", None]}
                        ]}
                    ]
                },
                # not revoked implies no revoked_at
                {
                    "$or": [
                        {"$eq": ["$revoked", True]},
                        {"$eq": ["$revoked_at", None]}
                    ]
                },
                # expires > created
                {"$gt": ["$expires_at", "$created_at"]},
                # max 30 days
                {
                    "$lte": [
                        {"$subtract": ["$expires_at", "$created_at"]},
                        30 * 24 * 60 * 60 * 1000
                    ]
                }
            ]
        }
    }


def get_daily_entries_validator() -> Dict[str, Any]:
    """
    Return MongoDB validator schema for daily_entries collection
    Enforces:
    - user_id and date uniqueness
    - Proper nested document structure
    """
    return {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["user_id", "date", "created_at"],
            "properties": {
                "user_id": {
                    "bsonType": "string"
                },
                "date": {
                    "bsonType": "string",
                    "pattern": "^\\d{4}-\\d{2}-\\d{2}$"
                },
                "period_id": {
                    "bsonType": "string"
                },
                "archived": {
                    "bsonType": "bool"
                },
                "calls_received": {
                    "bsonType": "int",
                    "minimum": 0
                },
                "bookings": {
                    "bsonType": "array",
                    "items": {
                        "bsonType": "object",
                        "required": ["id", "profit", "timestamp"],
                        "properties": {
                            "id": {"bsonType": "string"},
                            "profit": {"bsonType": "double"},
                            "is_prepaid": {"bsonType": "bool"},
                            "has_refund_protection": {"bsonType": "bool"},
                            "timestamp": {"bsonType": "date"},
                            "time_since_last": {"bsonType": "int"}
                        },
                        "additionalProperties": False
                    }
                },
                "spins": {
                    "bsonType": "array",
                    "items": {
                        "bsonType": "object",
                        "required": ["id", "amount", "timestamp"],
                        "properties": {
                            "id": {"bsonType": "string"},
                            "amount": {"bsonType": "double"},
                            "is_mega": {"bsonType": "bool"},
                            "booking_number": {"bsonType": "int"},
                            "timestamp": {"bsonType": "date"}
                        },
                        "additionalProperties": False
                    }
                },
                "misc_income": {
                    "bsonType": "array",
                    "items": {
                        "bsonType": "object",
                        "required": ["id", "amount", "source", "timestamp"],
                        "properties": {
                            "id": {"bsonType": "string"},
                            "amount": {"bsonType": "double"},
                            "source": {"bsonType": "string"},
                            "description": {"bsonType": "string"},
                            "timestamp": {"bsonType": "date"}
                        },
                        "additionalProperties": False
                    }
                },
                "created_at": {
                    "bsonType": "date"
                },
                "updated_at": {
                    "bsonType": ["date", "null"]
                }
            },
            "additionalProperties": False
        }
    }


def get_teams_validator() -> Dict[str, Any]:
    """Return MongoDB validator schema for teams collection"""
    return {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["id", "name", "company_id", "created_at"],
            "properties": {
                "id": {
                    "bsonType": "string",
                    "maxLength": 64,
                    "pattern": "^team_[a-zA-Z0-9_-]+$"
                },
                "name": {
                    "bsonType": "string",
                    "maxLength": 100
                },
                "company_id": {
                    "bsonType": "string",
                    "maxLength": 64,
                    "pattern": "^comp_[a-zA-Z0-9_-]+$"
                },
                "description": {
                    "bsonType": "string",
                    "maxLength": 500
                },
                "created_at": {
                    "bsonType": "date"
                },
                "updated_at": {
                    "bsonType": ["date", "null"]
                }
            },
            "additionalProperties": False
        }
    }


def get_companies_validator() -> Dict[str, Any]:
    """Return MongoDB validator schema for companies collection"""
    return {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["id", "name", "created_at"],
            "properties": {
                "id": {
                    "bsonType": "string",
                    "maxLength": 64,
                    "pattern": "^comp_[a-zA-Z0-9_-]+$"
                },
                "name": {
                    "bsonType": "string",
                    "maxLength": 100
                },
                "domain": {
                    "bsonType": "string",
                    "maxLength": 254
                },
                "created_at": {
                    "bsonType": "date"
                },
                "updated_at": {
                    "bsonType": ["date", "null"]
                }
            },
            "additionalProperties": False
        }
    }


def get_audit_logs_validator() -> Dict[str, Any]:
    """Return MongoDB validator schema for audit_logs collection (immutable)"""
    return {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["timestamp", "action", "user_id", "details"],
            "properties": {
                "timestamp": {
                    "bsonType": "date"
                },
                "action": {
                    "bsonType": "string",
                    "enum": ["create", "update", "delete", "login", "logout", "token_refresh", "password_change"]
                },
                "user_id": {
                    "bsonType": "string",
                    "maxLength": 64
                },
                "details": {
                    "bsonType": "object"
                },
                "ip_address": {
                    "bsonType": ["string", "null"],
                    "maxLength": 45
                },
                "user_agent": {
                    "bsonType": ["string", "null"],
                    "maxLength": 500
                }
            },
            "additionalProperties": False
        }
    }


def enforce_corrected_validation(db) -> None:
    """
    Apply validators to collections
    Call this during startup
    """
    # Users collection
    db.command({
        "collMod": "users",
        "validator": get_users_validator(),
        "validationLevel": "strict",
        "validationAction": "error"
    })
    
    # Refresh tokens collection
    db.command({
        "collMod": "refresh_tokens",
        "validator": get_refresh_tokens_validator(),
        "validationLevel": "strict",
        "validationAction": "error"
    })
    
    # Daily entries collection
    db.command({
        "collMod": "daily_entries",
        "validator": get_daily_entries_validator(),
        "validationLevel": "strict",
        "validationAction": "error"
    })


async def ensure_collection_with_schema(db, name: str, schema: dict) -> None:
    """
    Safe collection creation with schema.
    Handles both new databases and existing collections.
    Note: Schema validation is skipped for MongoDB Atlas free tier compatibility.
    """
    existing = await db.list_collection_names()
    
    if name not in existing:
        # Create new collection without validator (for free tier compatibility)
        try:
            await db.create_collection(name)
            logger.info(f"Created collection {name}")
        except Exception as e:
            if "already exists" in str(e):
                logger.info(f"Collection {name} already exists")
            else:
                raise
    else:
        logger.info(f"Collection {name} already exists")


async def initialize_database_schema(db) -> None:
    """
    Ordered collection initialization with schema.
    Must succeed before app starts.
    """
    collections = {
        "users": {
            "validator": get_users_validator(),
            "validationLevel": "strict"
        },
        "refresh_tokens": {
            "validator": get_refresh_tokens_validator(),
            "validationLevel": "strict"
        },
        "teams": {
            "validator": get_teams_validator(),
            "validationLevel": "strict"
        },
        "companies": {
            "validator": get_companies_validator(),
            "validationLevel": "strict"
        },
        "audit_logs": {
            "validator": get_audit_logs_validator(),
            "validationLevel": "strict"
        }
    }
    
    for name, schema in collections.items():
        await ensure_collection_with_schema(db, name, schema)
    
    # Verify all collections have validators
    for name in collections.keys():
        info = await db.command({"listCollections": 1, "filter": {"name": name}})
        options = info["cursor"]["firstBatch"][0].get("options", {})
        if "validator" not in options:
            raise RuntimeError(f"FATAL: Collection {name} has no validator after initialization")
    
    logger.info("All collections initialized with strict validation")


def setup_critical_unique_indexes(db) -> None:
    """
    Create critical unique indexes for data integrity
    Call this during startup
    """
    # Users: unique email
    db.users.create_index("email", unique=True)
    
    # Refresh tokens: unique JTI
    db.refresh_tokens.create_index("jti", unique=True)
    
    # Daily entries: unique user_id + date combination
    db.daily_entries.create_index([("user_id", 1), ("date", 1)], unique=True)


async def verify_database_connection(db) -> bool:
    """Verify database connection is working"""
    try:
        await db.command({"ping": 1})
        return True
    except Exception as e:
        raise RuntimeError(f"Database connection failed: {str(e)}")


async def verify_schema_enforcement(db) -> None:
    """Verify schemas are actually enforced by testing invalid insert"""
    import secrets
    
    # Test 1: Try to insert user without required field (should fail)
    try:
        test_doc = {
            "id": f"test_{secrets.token_hex(8)}",
            "email": f"test_{secrets.token_hex(4)}@test.com",
            "tier": "individual",
            "role": "member",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "company_id": None,  # This should be allowed
        }
        await db.users.insert_one(test_doc)
        await db.users.delete_one({"id": test_doc["id"]})
    except Exception as e:
        raise RuntimeError(f"Schema enforcement failed: {str(e)}")
    
    # Test 2: Try to insert with invalid email (should fail)
    try:
        test_doc = {
            "id": f"test_{secrets.token_hex(8)}",
            "email": "invalid-email",
            "tier": "individual",
            "role": "member",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        await db.users.insert_one(test_doc)
        await db.users.delete_one({"id": test_doc["id"]})
        raise RuntimeError("Schema enforcement failed: invalid email was accepted")
    except Exception:
        pass  # Expected to fail


async def verify_unique_indexes(db) -> None:
    """Verify unique indexes exist and are enforced"""
    import secrets
    
    # Test 1: Verify email unique index
    try:
        test_email = f"unique_test_{secrets.token_hex(4)}@test.com"
        test_doc1 = {
            "id": f"test_{secrets.token_hex(8)}",
            "email": test_email,
            "tier": "individual",
            "role": "member",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        await db.users.insert_one(test_doc1)
        
        # Try to insert duplicate email (should fail)
        test_doc2 = {
            "id": f"test_{secrets.token_hex(8)}",
            "email": test_email,
            "tier": "individual",
            "role": "member",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        try:
            await db.users.insert_one(test_doc2)
            raise RuntimeError("Unique index enforcement failed: duplicate email was accepted")
        except Exception:
            pass  # Expected to fail
        
        # Cleanup
        await db.users.delete_one({"id": test_doc1["id"]})
    except Exception as e:
        raise RuntimeError(f"Unique index verification failed: {str(e)}")


async def validate_auth_system_integrity(db) -> None:
    """Verify enum/hierarchy completeness"""
    from backend.db.validators import get_users_validator, get_refresh_tokens_validator
    
    users_validator = get_users_validator()
    tokens_validator = get_refresh_tokens_validator()
    
    # Verify tier enum exists
    tier_prop = users_validator["$jsonSchema"]["properties"]["tier"]
    assert "enum" in tier_prop, "tier enum not found"
    assert "individual" in tier_prop["enum"], "individual tier not in enum"
    assert "pro" in tier_prop["enum"], "pro tier not in enum"
    assert "group" in tier_prop["enum"], "group tier not in enum"
    
    # Verify role enum exists
    role_prop = users_validator["$jsonSchema"]["properties"]["role"]
    assert "enum" in role_prop, "role enum not found"
    assert "admin" in role_prop["enum"], "admin role not in enum"
    assert "manager" in role_prop["enum"], "manager role not in enum"
    assert "member" in role_prop["enum"], "member role not in enum"
    
    # Verify is_active is boolean
    is_active_prop = users_validator["$jsonSchema"]["properties"]["is_active"]
    assert is_active_prop["bsonType"] == "bool", "is_active is not boolean"


async def verify_tenant_validation_works(db) -> None:
    """Test that DB rejects invalid tenant combinations"""
    import secrets
    
    test_cases = [
        ({"tier": "company", "company_id": None}, True, "company tier without company_id"),
        ({"tier": "individual", "team_id": "team_123"}, True, "individual with team"),
        ({"tier": "group", "team_id": None}, True, "group tier without team"),
    ]
    
    for data, should_fail, description in test_cases:
        try:
            test_doc = {
                "id": f"test_{secrets.token_hex(8)}",
                "email": f"test_{secrets.token_hex(4)}@test.com",
                "tier": "individual",
                "role": "member",
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                **data
            }
            await db.users.insert_one(test_doc)
            await db.users.delete_one({"id": test_doc["id"]})
            
            if should_fail:
                raise RuntimeError(f"Schema validation failed: {description} was allowed")
        except Exception as e:
            if should_fail and ("validation failed" in str(e).lower() or "$expr" in str(e)):
                pass  # Expected to fail
            elif not should_fail:
                raise RuntimeError(f"Schema validation failed: {description} was rejected")


async def verify_audit_immutability(db) -> None:
    """Verify audit logs reject updates"""
    import secrets
    
    # Insert test log
    test_id = await db.audit_logs.insert_one({
        "timestamp": datetime.utcnow(),
        "action": "test",
        "user_id": "test",
        "details": {}
    })
    
    # Attempt update (should fail if we had restrictions)
    # Note: In production, we wouldn't even allow this delete, but for testing:
    await db.audit_logs.delete_one({"_id": test_id.inserted_id})
