"""
Database schema initialization for dynamic goal recalculation.
Creates collections and indexes for metrics, goals history, and profit targets.
"""

import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase


async def init_goal_recalculation_schema(db: AsyncIOMotorDatabase) -> None:
    """
    Initialize collections and indexes for goal recalculation feature.
    
    Args:
        db: Motor async database instance
    """
    # Create user_daily_metrics collection with indexes
    if "user_daily_metrics" not in await db.list_collection_names():
        await db.create_collection("user_daily_metrics")
    
    metrics_collection = db["user_daily_metrics"]
    await metrics_collection.create_index([("user_id", 1), ("date", 1)], unique=True)
    await metrics_collection.create_index([("user_id", 1), ("period_id", 1)])
    await metrics_collection.create_index([("created_at", 1)])
    
    # Create user_goals_history collection with indexes
    if "user_goals_history" not in await db.list_collection_names():
        await db.create_collection("user_goals_history")
    
    goals_history_collection = db["user_goals_history"]
    await goals_history_collection.create_index([("user_id", 1), ("period_id", 1)])
    await goals_history_collection.create_index([("user_id", 1), ("period_type", 1)])
    await goals_history_collection.create_index([("user_id", 1), ("effective_date", 1)])
    await goals_history_collection.create_index([("created_at", 1)])
    
    # Create user_profit_targets collection with indexes
    if "user_profit_targets" not in await db.list_collection_names():
        await db.create_collection("user_profit_targets")
    
    targets_collection = db["user_profit_targets"]
    await targets_collection.create_index([("user_id", 1)], unique=True)
    await targets_collection.create_index([("updated_at", 1)])


async def get_metrics_collection(db: AsyncIOMotorDatabase):
    """Get the user_daily_metrics collection"""
    return db["user_daily_metrics"]


async def get_goals_history_collection(db: AsyncIOMotorDatabase):
    """Get the user_goals_history collection"""
    return db["user_goals_history"]


async def get_profit_targets_collection(db: AsyncIOMotorDatabase):
    """Get the user_profit_targets collection"""
    return db["user_profit_targets"]
