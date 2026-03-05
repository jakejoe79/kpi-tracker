"""
API service for goal-related endpoints.
Handles retrieving current goals, historical goals, and managing profit targets.
"""

import logging
from datetime import datetime, date, timedelta
from typing import Optional, Dict, List
from motor.motor_asyncio import AsyncIOMotorDatabase

from db.schema import (
    get_goals_history_collection,
    get_profit_targets_collection,
    get_metrics_collection
)
from services.metrics import calculate_conversion_rate, calculate_booking_speed
from services.goals import recalculate_daily_goals, recalculate_weekly_goals, recalculate_biweekly_goals

logger = logging.getLogger(__name__)


async def get_current_goals(db: AsyncIOMotorDatabase, user_id: str) -> Dict:
    """
    Get current goals for all periods with progress and time remaining.
    
    Args:
        db: Motor async database instance
        user_id: User ID
        
    Returns:
        Dictionary with daily, weekly, and biweekly goals and progress
    """
    user_goals = db["user_goals"]
    daily_entries = db["daily_entries"]
    
    try:
        # Get current goals
        goals_doc = await user_goals.find_one({"user_id": user_id})
        
        if not goals_doc:
            return {
                "daily": None,
                "weekly": None,
                "biweekly": None,
            }
        
        goals_flat = goals_doc.get("goals", {})
        
        # Get date ranges for progress calculation
        today = date.today()
        today_str = today.isoformat()
        
        # Daily: just today
        daily_start = today
        daily_end = today
        
        # Weekly: last 7 days
        weekly_start = today - timedelta(days=6)
        weekly_end = today
        
        # Biweekly: last 14 days
        biweekly_start = today - timedelta(days=13)
        biweekly_end = today
        
        # Get entries for progress calculation
        daily_entries_list = await daily_entries.find({
            "user_id": user_id,
            "date": {"$gte": daily_start.isoformat(), "$lte": daily_end.isoformat()}
        }).to_list(None)
        
        weekly_entries_list = await daily_entries.find({
            "user_id": user_id,
            "date": {"$gte": weekly_start.isoformat(), "$lte": weekly_end.isoformat()}
        }).to_list(None)
        
        biweekly_entries_list = await daily_entries.find({
            "user_id": user_id,
            "date": {"$gte": biweekly_start.isoformat(), "$lte": biweekly_end.isoformat()}
        }).to_list(None)
        
        result = {}
        
        # Process each period type
        for period_type in ["daily", "weekly", "biweekly"]:
            profit_key = f"profit_{period_type}"
            calls_key = f"calls_{period_type}"
            reservations_key = f"reservations_{period_type}"
            
            if profit_key not in goals_flat:
                result[period_type] = None
                continue
            
            profit_target = goals_flat.get(profit_key, 0)
            calls_needed = goals_flat.get(calls_key, 0)
            reservations_needed = goals_flat.get(reservations_key, 0)
            
            # Get entries for this period
            if period_type == "daily":
                entries = daily_entries_list
                effective_date = today_str
            elif period_type == "weekly":
                entries = weekly_entries_list
                effective_date = weekly_end.isoformat()
            else:  # biweekly
                entries = biweekly_entries_list
                effective_date = biweekly_end.isoformat()
            
            # Calculate progress
            current_calls = sum(e.get("calls_received", 0) for e in entries)
            current_reservations = sum(len(e.get("bookings", [])) for e in entries)
            current_profit = sum(
                sum(b.get("profit", 0) for b in e.get("bookings", []))
                for e in entries
            )
            
            # Calculate progress percentage
            progress_percent = (current_calls / calls_needed * 100) if calls_needed > 0 else 0
            
            # For time, we don't have it in flat structure, so skip or estimate
            time_needed_minutes = 0  # Not stored in flat structure
            time_remaining = 0
            
            result[period_type] = {
                "profit_target": profit_target,
                "calls_needed": calls_needed,
                "reservations_needed": reservations_needed,
                "time_needed_minutes": time_needed_minutes,
                "current_calls": current_calls,
                "current_reservations": current_reservations,
                "current_profit": current_profit,
                "progress_percent": round(progress_percent, 1),
                "time_remaining_minutes": time_remaining,
                "effective_date": effective_date,
            }
        
        return result
    except Exception as e:
        logger.error(f"Failed to get current goals for {user_id}: {e}")
        return {
            "daily": None,
            "weekly": None,
            "biweekly": None,
        }


async def get_goals_history(
    db: AsyncIOMotorDatabase,
    user_id: str,
    start_date: str,
    end_date: str
) -> List[Dict]:
    """
    Get historical goals for a date range.
    
    Args:
        db: Motor async database instance
        user_id: User ID
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        
    Returns:
        List of historical goal records
    """
    goals_history_collection = await get_goals_history_collection(db)
    
    try:
        goals = await goals_history_collection.find({
            "user_id": user_id,
            "effective_date": {"$gte": start_date, "$lte": end_date}
        }).sort("effective_date", -1).to_list(None)
        
        # Convert ObjectId to string for JSON serialization
        for goal in goals:
            if "_id" in goal:
                goal["_id"] = str(goal["_id"])
        
        return goals
    except Exception as e:
        logger.error(f"Failed to get goals history for {user_id}: {e}")
        return []


async def set_profit_targets(
    db: AsyncIOMotorDatabase,
    user_id: str,
    daily_target: float,
    weekly_target: float,
    biweekly_target: float
) -> bool:
    """
    Set profit targets for a user.
    
    Args:
        db: Motor async database instance
        user_id: User ID
        daily_target: Daily profit target in dollars
        weekly_target: Weekly profit target in dollars
        biweekly_target: Biweekly profit target in dollars
        
    Returns:
        True if successful, False otherwise
    """
    targets_collection = await get_profit_targets_collection(db)
    
    try:
        await targets_collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "user_id": user_id,
                    "daily_target": daily_target,
                    "weekly_target": weekly_target,
                    "biweekly_target": biweekly_target,
                    "updated_at": datetime.utcnow(),
                }
            },
            upsert=True
        )
        return True
    except Exception as e:
        logger.error(f"Failed to set profit targets for {user_id}: {e}")
        return False


async def get_daily_metrics(
    db: AsyncIOMotorDatabase,
    user_id: str,
    metric_date: str
) -> Optional[Dict]:
    """
    Get daily metrics for a specific date.
    
    Args:
        db: Motor async database instance
        user_id: User ID
        metric_date: Date in YYYY-MM-DD format
        
    Returns:
        Dictionary with daily metrics or None if not found
    """
    metrics_collection = await get_metrics_collection(db)
    
    try:
        metrics = await metrics_collection.find_one({
            "user_id": user_id,
            "date": metric_date
        })
        
        if metrics:
            if "_id" in metrics:
                metrics["_id"] = str(metrics["_id"])
        
        return metrics
    except Exception as e:
        logger.error(f"Failed to get daily metrics for {user_id} on {metric_date}: {e}")
        return None
