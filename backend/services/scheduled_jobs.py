"""
Scheduled jobs for dynamic goal recalculation.
Handles daily, weekly, and biweekly goal recalculation at period boundaries.
"""

import logging
from datetime import datetime, date, timedelta
from typing import Optional, Dict, List
from motor.motor_asyncio import AsyncIOMotorDatabase

from .goals import recalculate_daily_goals, recalculate_weekly_goals, recalculate_biweekly_goals
from .metrics import calculate_metrics, calculate_rolling_average_metrics
from db.schema import (
    get_metrics_collection,
    get_goals_history_collection,
    get_profit_targets_collection
)

logger = logging.getLogger(__name__)

# Baseline metrics for first 14 days
BASELINE_BOOKING_SPEED = 30.0  # minutes per booking
BASELINE_AVG_PROFIT = 2.40  # dollars per booking
BASELINE_CONVERSION_RATE = 15.0  # percentage


async def get_user_profit_targets(db: AsyncIOMotorDatabase, user_id: str) -> Dict[str, float]:
    """
    Get user's profit targets or return defaults.
    
    Args:
        db: Motor async database instance
        user_id: User ID
        
    Returns:
        Dictionary with daily_target, weekly_target, biweekly_target
    """
    targets_collection = await get_profit_targets_collection(db)
    targets = await targets_collection.find_one({"user_id": user_id})
    
    if targets:
        return {
            "daily_target": targets.get("daily_target", 72.08),
            "weekly_target": targets.get("weekly_target", 504.56),
            "biweekly_target": targets.get("biweekly_target", 1009.12),
        }
    
    # Return default targets if not set
    return {
        "daily_target": 72.08,
        "weekly_target": 504.56,
        "biweekly_target": 1009.12,
    }


async def get_daily_entry_data(db: AsyncIOMotorDatabase, user_id: str, entry_date: str) -> Optional[Dict]:
    """
    Get daily entry data from the database.
    
    Args:
        db: Motor async database instance
        user_id: User ID
        entry_date: Date in YYYY-MM-DD format
        
    Returns:
        Daily entry data or None if not found
    """
    daily_entries = db["daily_entries"]
    entry = await daily_entries.find_one({
        "user_id": user_id,
        "date": entry_date
    })
    return entry


async def calculate_daily_metrics(db: AsyncIOMotorDatabase, user_id: str, entry_date: str) -> Optional[Dict]:
    """
    Calculate daily metrics from a daily entry.
    
    Args:
        db: Motor async database instance
        user_id: User ID
        entry_date: Date in YYYY-MM-DD format
        
    Returns:
        Dictionary with calculated metrics or None if entry not found
    """
    entry = await get_daily_entry_data(db, user_id, entry_date)
    
    if not entry:
        return None
    
    # Extract data from entry
    calls_received = entry.get("calls_received", 0)
    bookings = entry.get("bookings", [])
    total_bookings = len(bookings)
    
    # Calculate total time and profit
    total_time_minutes = entry.get("total_time_minutes", 0)
    total_profit = sum(b.get("profit", 0) for b in bookings)
    
    # Handle edge cases
    if total_bookings == 0 or calls_received == 0:
        return None
    
    try:
        metrics = calculate_metrics(
            total_time_minutes=total_time_minutes,
            bookings_count=total_bookings,
            calls_count=calls_received,
            total_profit=total_profit
        )
        
        metrics.update({
            "total_bookings": total_bookings,
            "total_calls": calls_received,
            "total_profit": total_profit,
            "total_time_minutes": total_time_minutes,
        })
        
        return metrics
    except ValueError:
        return None


async def get_metrics_for_period(
    db: AsyncIOMotorDatabase,
    user_id: str,
    start_date: str,
    end_date: str
) -> Optional[Dict]:
    """
    Calculate aggregated metrics for a period.
    
    Args:
        db: Motor async database instance
        user_id: User ID
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        
    Returns:
        Dictionary with aggregated metrics or None if no data
    """
    daily_entries = db["daily_entries"]
    
    # Query entries for the period
    entries = await daily_entries.find({
        "user_id": user_id,
        "date": {"$gte": start_date, "$lte": end_date}
    }).to_list(None)
    
    if not entries:
        return None
    
    # Aggregate data
    total_time = 0
    total_bookings = 0
    total_calls = 0
    total_profit = 0
    
    for entry in entries:
        total_time += entry.get("total_time_minutes", 0)
        bookings = entry.get("bookings", [])
        total_bookings += len(bookings)
        total_calls += entry.get("calls_received", 0)
        total_profit += sum(b.get("profit", 0) for b in bookings)
    
    if total_bookings == 0 or total_calls == 0:
        return None
    
    try:
        metrics = calculate_metrics(
            total_time_minutes=total_time,
            bookings_count=total_bookings,
            calls_count=total_calls,
            total_profit=total_profit
        )
        
        metrics.update({
            "total_bookings": total_bookings,
            "total_calls": total_calls,
            "total_profit": total_profit,
            "total_time_minutes": total_time,
        })
        
        return metrics
    except ValueError:
        return None


async def get_rolling_average_metrics(
    db: AsyncIOMotorDatabase,
    user_id: str,
    days: int = 14
) -> Optional[Dict]:
    """
    Get rolling average metrics from the last N days.
    
    Args:
        db: Motor async database instance
        user_id: User ID
        days: Number of days to average (default 14)
        
    Returns:
        Dictionary with averaged metrics or None if insufficient data
    """
    metrics_collection = await get_metrics_collection(db)
    
    # Get metrics from last N days
    end_date = date.today().isoformat()
    start_date = (date.today() - timedelta(days=days)).isoformat()
    
    metrics_list = await metrics_collection.find({
        "user_id": user_id,
        "date": {"$gte": start_date, "$lte": end_date}
    }).to_list(None)
    
    if len(metrics_list) < days:
        return None
    
    try:
        return calculate_rolling_average_metrics(metrics_list)
    except ValueError:
        return None


async def select_metrics_for_recalculation(
    db: AsyncIOMotorDatabase,
    user_id: str,
    period_type: str
) -> Dict[str, float]:
    """
    Select metrics for goal recalculation based on data availability.
    
    Uses 2-week rolling average if user has >= 14 days of data,
    otherwise uses baseline or actual period metrics.
    
    Args:
        db: Motor async database instance
        user_id: User ID
        period_type: "daily", "weekly", or "biweekly"
        
    Returns:
        Dictionary with booking_speed_interval, conversion_rate, avg_profit_per_booking
    """
    # Check if user has 14+ days of data
    rolling_avg = await get_rolling_average_metrics(db, user_id, days=14)
    
    if rolling_avg:
        logger.info(f"Using 2-week rolling average for {user_id}")
        return rolling_avg
    
    # Fall back to baseline
    logger.info(f"Using baseline metrics for {user_id}")
    return {
        "booking_speed_interval": BASELINE_BOOKING_SPEED,
        "conversion_rate": BASELINE_CONVERSION_RATE,
        "avg_profit_per_booking": BASELINE_AVG_PROFIT,
    }


async def store_daily_metrics(
    db: AsyncIOMotorDatabase,
    user_id: str,
    entry_date: str,
    period_id: str,
    metrics: Dict
) -> bool:
    """
    Store calculated daily metrics in the database.
    
    Args:
        db: Motor async database instance
        user_id: User ID
        entry_date: Date in YYYY-MM-DD format
        period_id: Period ID
        metrics: Dictionary with calculated metrics
        
    Returns:
        True if successful, False otherwise
    """
    metrics_collection = await get_metrics_collection(db)
    
    try:
        await metrics_collection.update_one(
            {"user_id": user_id, "date": entry_date},
            {
                "$set": {
                    "user_id": user_id,
                    "date": entry_date,
                    "period_id": period_id,
                    "booking_speed_interval": metrics["booking_speed_interval"],
                    "conversion_rate": metrics["conversion_rate"],
                    "avg_profit_per_booking": metrics["avg_profit_per_booking"],
                    "total_bookings": metrics["total_bookings"],
                    "total_calls": metrics["total_calls"],
                    "total_profit": metrics["total_profit"],
                    "total_time_minutes": metrics["total_time_minutes"],
                    "updated_at": datetime.utcnow(),
                }
            },
            upsert=True
        )
        return True
    except Exception as e:
        logger.error(f"Failed to store metrics for {user_id} on {entry_date}: {e}")
        return False


async def store_goal_history(
    db: AsyncIOMotorDatabase,
    user_id: str,
    period_id: str,
    period_type: str,
    profit_target: float,
    goals: Dict,
    metrics: Dict,
    effective_date: str
) -> bool:
    """
    Store goal snapshot in history.
    
    Args:
        db: Motor async database instance
        user_id: User ID
        period_id: Period ID
        period_type: "daily", "weekly", or "biweekly"
        profit_target: Profit target for this period
        goals: Dictionary with calculated goals
        metrics: Dictionary with metrics used for calculation
        effective_date: Date when goals become effective
        
    Returns:
        True if successful, False otherwise
    """
    goals_history_collection = await get_goals_history_collection(db)
    
    try:
        await goals_history_collection.insert_one({
            "user_id": user_id,
            "period_id": period_id,
            "period_type": period_type,
            "profit_target": profit_target,
            "calls_needed": goals["calls_needed"],
            "reservations_needed": goals["reservations_needed"],
            "time_needed_minutes": goals["time_needed_minutes"],
            "booking_speed_interval": metrics["booking_speed_interval"],
            "conversion_rate": metrics["conversion_rate"],
            "avg_profit_per_booking": metrics["avg_profit_per_booking"],
            "effective_date": effective_date,
            "created_at": datetime.utcnow(),
        })
        return True
    except Exception as e:
        logger.error(f"Failed to store goal history for {user_id}: {e}")
        return False


async def update_user_goals(
    db: AsyncIOMotorDatabase,
    user_id: str,
    period_type: str,
    goals: Dict
) -> bool:
    """
    Update the current goals for a user.
    
    Args:
        db: Motor async database instance
        user_id: User ID
        period_type: "daily", "weekly", or "biweekly"
        goals: Dictionary with calculated goals
        
    Returns:
        True if successful, False otherwise
    """
    user_goals = db["user_goals"]
    
    try:
        await user_goals.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    f"{period_type}_goals": goals,
                    "updated_at": datetime.utcnow(),
                }
            },
            upsert=True
        )
        return True
    except Exception as e:
        logger.error(f"Failed to update goals for {user_id}: {e}")
        return False


async def recalculate_daily_goals_job(
    db: AsyncIOMotorDatabase,
    user_id: str
) -> bool:
    """
    Scheduled job to recalculate daily goals at 12:00 AM UTC.
    
    Args:
        db: Motor async database instance
        user_id: User ID
        
    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Starting daily goal recalculation for {user_id}")
    
    try:
        # Get yesterday's date
        yesterday = date.today() - timedelta(days=1)
        yesterday_str = yesterday.isoformat()
        today_str = date.today().isoformat()
        
        # Calculate yesterday's metrics
        daily_metrics = await calculate_daily_metrics(db, user_id, yesterday_str)
        
        if daily_metrics:
            # Store metrics
            await store_daily_metrics(db, user_id, yesterday_str, yesterday_str, daily_metrics)
        
        # Select metrics for recalculation
        metrics = await select_metrics_for_recalculation(db, user_id, "daily")
        
        # Get profit target
        targets = await get_user_profit_targets(db, user_id)
        profit_target = targets["daily_target"]
        
        # Recalculate goals
        goals = recalculate_daily_goals(
            profit_target=profit_target,
            booking_speed_interval=metrics["booking_speed_interval"],
            conversion_rate=metrics["conversion_rate"],
            avg_profit_per_booking=metrics["avg_profit_per_booking"]
        )
        
        # Store goal history
        await store_goal_history(
            db, user_id, today_str, "daily", profit_target, goals, metrics, today_str
        )
        
        # Update current goals
        await update_user_goals(db, user_id, "daily", goals)
        
        logger.info(f"Successfully recalculated daily goals for {user_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to recalculate daily goals for {user_id}: {e}")
        return False


async def recalculate_weekly_goals_job(
    db: AsyncIOMotorDatabase,
    user_id: str
) -> bool:
    """
    Scheduled job to recalculate weekly goals at Saturday 12:00 AM UTC.
    
    Args:
        db: Motor async database instance
        user_id: User ID
        
    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Starting weekly goal recalculation for {user_id}")
    
    try:
        # Get this week's date range (Sunday to Saturday)
        today = date.today()
        # Saturday is weekday 5
        days_since_saturday = (today.weekday() - 5) % 7
        last_saturday = today - timedelta(days=days_since_saturday)
        last_sunday = last_saturday - timedelta(days=6)
        
        week_start = last_sunday.isoformat()
        week_end = last_saturday.isoformat()
        
        # Calculate this week's metrics
        weekly_metrics = await get_metrics_for_period(db, user_id, week_start, week_end)
        
        # Select metrics for recalculation
        metrics = await select_metrics_for_recalculation(db, user_id, "weekly")
        
        # Get profit target
        targets = await get_user_profit_targets(db, user_id)
        profit_target = targets["weekly_target"]
        
        # Recalculate goals
        goals = recalculate_weekly_goals(
            profit_target=profit_target,
            booking_speed_interval=metrics["booking_speed_interval"],
            conversion_rate=metrics["conversion_rate"],
            avg_profit_per_booking=metrics["avg_profit_per_booking"]
        )
        
        # Store goal history
        period_id = f"{week_start}_to_{week_end}"
        today_str = date.today().isoformat()
        await store_goal_history(
            db, user_id, period_id, "weekly", profit_target, goals, metrics, today_str
        )
        
        # Update current goals
        await update_user_goals(db, user_id, "weekly", goals)
        
        logger.info(f"Successfully recalculated weekly goals for {user_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to recalculate weekly goals for {user_id}: {e}")
        return False


async def recalculate_biweekly_goals_job(
    db: AsyncIOMotorDatabase,
    user_id: str
) -> bool:
    """
    Scheduled job to recalculate biweekly goals at 1st/16th 12:00 AM UTC.
    
    Args:
        db: Motor async database instance
        user_id: User ID
        
    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Starting biweekly goal recalculation for {user_id}")
    
    try:
        today = date.today()
        
        # Determine period boundaries (1st-15th or 16th-end of month)
        if today.day <= 15:
            period_start = date(today.year, today.month, 1)
            period_end = date(today.year, today.month, 15)
        else:
            period_start = date(today.year, today.month, 16)
            # Last day of month
            if today.month == 12:
                period_end = date(today.year + 1, 1, 1) - timedelta(days=1)
            else:
                period_end = date(today.year, today.month + 1, 1) - timedelta(days=1)
        
        period_start_str = period_start.isoformat()
        period_end_str = period_end.isoformat()
        
        # Calculate this period's metrics
        biweekly_metrics = await get_metrics_for_period(db, user_id, period_start_str, period_end_str)
        
        # Select metrics for recalculation
        metrics = await select_metrics_for_recalculation(db, user_id, "biweekly")
        
        # Get profit target
        targets = await get_user_profit_targets(db, user_id)
        profit_target = targets["biweekly_target"]
        
        # Recalculate goals
        goals = recalculate_biweekly_goals(
            profit_target=profit_target,
            booking_speed_interval=metrics["booking_speed_interval"],
            conversion_rate=metrics["conversion_rate"],
            avg_profit_per_booking=metrics["avg_profit_per_booking"]
        )
        
        # Store goal history
        period_id = f"{period_start_str}_to_{period_end_str}"
        today_str = date.today().isoformat()
        await store_goal_history(
            db, user_id, period_id, "biweekly", profit_target, goals, metrics, today_str
        )
        
        # Update current goals
        await update_user_goals(db, user_id, "biweekly", goals)
        
        logger.info(f"Successfully recalculated biweekly goals for {user_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to recalculate biweekly goals for {user_id}: {e}")
        return False
