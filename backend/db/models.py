"""
Database models for dynamic goal recalculation feature.
Defines schemas for metrics, goals history, and profit targets.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class UserDailyMetrics(BaseModel):
    """Daily metrics calculated at period boundaries"""
    user_id: str
    date: str  # YYYY-MM-DD
    period_id: str
    booking_speed_interval: float  # minutes per booking
    conversion_rate: float  # percentage (0-100)
    avg_profit_per_booking: float  # dollars
    total_bookings: int
    total_calls: int
    total_profit: float
    total_time_minutes: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "date": "2026-03-01",
                "period_id": "2026-03-01",
                "booking_speed_interval": 30.0,
                "conversion_rate": 16.0,
                "avg_profit_per_booking": 2.40,
                "total_bookings": 16,
                "total_calls": 100,
                "total_profit": 38.40,
                "total_time_minutes": 480.0,
            }
        }


class UserGoalsHistory(BaseModel):
    """Historical record of goals at each recalculation"""
    user_id: str
    period_id: str
    period_type: str  # daily|weekly|biweekly
    profit_target: float
    calls_needed: int
    reservations_needed: int
    time_needed_minutes: float
    booking_speed_interval: float
    conversion_rate: float
    avg_profit_per_booking: float
    effective_date: str  # YYYY-MM-DD
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "period_id": "2026-03-01",
                "period_type": "daily",
                "profit_target": 72.08,
                "calls_needed": 188,
                "reservations_needed": 30,
                "time_needed_minutes": 5640.0,
                "booking_speed_interval": 30.0,
                "conversion_rate": 16.0,
                "avg_profit_per_booking": 2.40,
                "effective_date": "2026-03-01",
            }
        }


class UserProfitTargets(BaseModel):
    """User's profit targets for each period type"""
    user_id: str
    daily_target: float
    weekly_target: float
    biweekly_target: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "daily_target": 72.08,
                "weekly_target": 504.56,
                "biweekly_target": 1009.12,
            }
        }
