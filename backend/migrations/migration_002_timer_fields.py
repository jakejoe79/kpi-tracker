"""
Migration 002: Add Timer Fields to Daily Entries

This migration:
- Updates the daily_entries validator to include work_timer_start and total_time_minutes fields
- Adds the id field as required
- Ensures existing documents are compatible with the new schema

Run during startup to update the schema
"""
from typing import Dict, Any


async def apply(db) -> Dict[str, Any]:
    """
    Apply migration 002 - add timer fields to daily entries

    Returns: Migration result summary
    """
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from db.validators import get_daily_entries_validator

    result = {
        "migration": "002_timer_fields",
        "status": "success",
        "changes": []
    }

    try:
        # Update the daily_entries collection validator
        validator = get_daily_entries_validator()
        await db.command({
            "collMod": "daily_entries",
            "validator": validator
        })
        result["changes"].append("daily_entries_validator_updated")

        # Add default values for total_time_minutes to existing documents that don't have it
        await db.daily_entries.update_many(
            {"total_time_minutes": {"$exists": False}},
            {"$set": {"total_time_minutes": 0.0}}
        )
        result["changes"].append("total_time_minutes_defaults_added")

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result


async def rollback(db) -> Dict[str, Any]:
    """
    Rollback migration 002 - remove timer fields from daily entries

    Returns: Rollback result summary
    """
    result = {
        "migration": "002_timer_fields",
        "operation": "rollback",
        "status": "success",
        "changes": []
    }

    try:
        # Remove the validator update (revert to previous schema)
        # Note: This is a simplified rollback - in production you'd want the exact previous validator
        await db.command({
            "collMod": "daily_entries",
            "validator": {}
        })
        result["changes"].append("daily_entries_validator_rolled_back")

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result