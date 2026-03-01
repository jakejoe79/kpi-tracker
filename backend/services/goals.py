"""
Goal recalculation engine for dynamic goal adjustment.
Calculates goals based on profit targets and actual performance metrics.
"""

from typing import Dict, Optional
from datetime import datetime


def recalculate_goals(
    profit_target: float,
    booking_speed_interval: float,
    conversion_rate: float,
    avg_profit_per_booking: float
) -> Dict[str, float]:
    """
    Recalculate goals based on profit target and actual metrics.
    
    Formula:
    - reservations_needed = profit_target / avg_profit_per_booking
    - calls_needed = reservations_needed / (conversion_rate / 100)
    - time_needed_minutes = calls_needed * booking_speed_interval
    
    Args:
        profit_target: Target profit in dollars
        booking_speed_interval: Minutes per booking
        conversion_rate: Conversion rate as percentage (0-100)
        avg_profit_per_booking: Average profit per booking in dollars
        
    Returns:
        Dictionary with calls_needed, reservations_needed, and time_needed_minutes
        
    Raises:
        ValueError: If any metric is invalid or would cause division by zero
    """
    if avg_profit_per_booking <= 0:
        raise ValueError("avg_profit_per_booking must be greater than 0")
    
    if conversion_rate <= 0:
        raise ValueError("conversion_rate must be greater than 0")
    
    if booking_speed_interval <= 0:
        raise ValueError("booking_speed_interval must be greater than 0")
    
    if profit_target < 0:
        raise ValueError("profit_target cannot be negative")
    
    # Calculate reservations needed
    reservations_needed = profit_target / avg_profit_per_booking
    
    # Calculate calls needed
    # conversion_rate is a percentage, so divide by 100 to get decimal
    calls_needed = reservations_needed / (conversion_rate / 100)
    
    # Calculate time needed in minutes
    time_needed_minutes = calls_needed * booking_speed_interval
    
    return {
        "calls_needed": int(round(calls_needed)),
        "reservations_needed": int(round(reservations_needed)),
        "time_needed_minutes": time_needed_minutes,
    }


def recalculate_daily_goals(
    profit_target: float,
    booking_speed_interval: float,
    conversion_rate: float,
    avg_profit_per_booking: float
) -> Dict[str, any]:
    """
    Recalculate daily goals.
    
    Args:
        profit_target: Daily profit target in dollars
        booking_speed_interval: Minutes per booking
        conversion_rate: Conversion rate as percentage
        avg_profit_per_booking: Average profit per booking
        
    Returns:
        Dictionary with daily goals
    """
    goals = recalculate_goals(
        profit_target,
        booking_speed_interval,
        conversion_rate,
        avg_profit_per_booking
    )
    
    return {
        "period_type": "daily",
        "profit_target": profit_target,
        "calls_needed": goals["calls_needed"],
        "reservations_needed": goals["reservations_needed"],
        "time_needed_minutes": goals["time_needed_minutes"],
        "booking_speed_interval": booking_speed_interval,
        "conversion_rate": conversion_rate,
        "avg_profit_per_booking": avg_profit_per_booking,
    }


def recalculate_weekly_goals(
    profit_target: float,
    booking_speed_interval: float,
    conversion_rate: float,
    avg_profit_per_booking: float
) -> Dict[str, any]:
    """
    Recalculate weekly goals.
    
    Args:
        profit_target: Weekly profit target in dollars
        booking_speed_interval: Minutes per booking
        conversion_rate: Conversion rate as percentage
        avg_profit_per_booking: Average profit per booking
        
    Returns:
        Dictionary with weekly goals
    """
    goals = recalculate_goals(
        profit_target,
        booking_speed_interval,
        conversion_rate,
        avg_profit_per_booking
    )
    
    return {
        "period_type": "weekly",
        "profit_target": profit_target,
        "calls_needed": goals["calls_needed"],
        "reservations_needed": goals["reservations_needed"],
        "time_needed_minutes": goals["time_needed_minutes"],
        "booking_speed_interval": booking_speed_interval,
        "conversion_rate": conversion_rate,
        "avg_profit_per_booking": avg_profit_per_booking,
    }


def recalculate_biweekly_goals(
    profit_target: float,
    booking_speed_interval: float,
    conversion_rate: float,
    avg_profit_per_booking: float
) -> Dict[str, any]:
    """
    Recalculate biweekly goals.
    
    Args:
        profit_target: Biweekly profit target in dollars
        booking_speed_interval: Minutes per booking
        conversion_rate: Conversion rate as percentage
        avg_profit_per_booking: Average profit per booking
        
    Returns:
        Dictionary with biweekly goals
    """
    goals = recalculate_goals(
        profit_target,
        booking_speed_interval,
        conversion_rate,
        avg_profit_per_booking
    )
    
    return {
        "period_type": "biweekly",
        "profit_target": profit_target,
        "calls_needed": goals["calls_needed"],
        "reservations_needed": goals["reservations_needed"],
        "time_needed_minutes": goals["time_needed_minutes"],
        "booking_speed_interval": booking_speed_interval,
        "conversion_rate": conversion_rate,
        "avg_profit_per_booking": avg_profit_per_booking,
    }
