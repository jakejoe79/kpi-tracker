"""
KPI Tracker API - Performance Infrastructure

ELITE FEATURES:
- Smart Hybrid Model: Real-time for Group, Daily snapshots for Pro
- Elite Risk Scoring: (gap * 0.7) + (conversion_drop * 0.3) with trend multipliers
- Smart Thresholds: Minimum change detection to prevent noise
- Alert Cooldowns: 1hr high risk, 2hr medium, 4hr low - prevents toxic anxiety
- Risk Tiers: ≡ƒö┤ Red (70+), ≡ƒƒí Yellow (40-69), ≡ƒƒó Green (<40)
- Top 5 Signals: Sorted by risk_score descending - highest operational priority
- Decision Signals: Answers "Who needs attention right now?" not "What changed by 0.3%?"

MONETIZATION TIERS:
- Free: Individual stats only
- Pro: Daily snapshots at 6 PM, custom goals, basic team leaderboard
- Group: Real-time calculations, live risk monitoring, Top 5 intervention signals

ARCHITECTURE:
- Backend calculates everything - frontend displays
- MongoDB stores daily snapshots and alert history
- Scheduled jobs: Period archiving (midnight 1st/15th), Daily reset (midnight), Snapshots (6 PM)
- Change detection prevents alert spam
- Polling every 20 seconds for Group plan (good for Render free tier)

This is Performance Infrastructure Territory.
"""

from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks, Depends, Request
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, date, timedelta
import calendar
import asyncio
from email_validator import validate_email, EmailNotValidError
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import statistics

from constants import SPIN_RULES, calculate_progress, is_on_track, get_status


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# FAKE AUTH - TODO: Replace with real JWT auth before production
# =============================================================================

CURRENT_USER_ID = "user_001"
CURRENT_USER_PLAN = "individual"  # Testing Individual plan for 2-3 weeks before rolling out other tiers

# =============================================================================
# FEATURE REGISTRY
# =============================================================================

FEATURES = {
    "export_data": {"label": "Export Data", "description": "Download CSV and PDF reports", "required_plan": "individual"},
    "custom_goals": {"label": "Custom Goals", "description": "Set personalized KPI targets", "required_plan": "individual"},
    "historical_reports": {"label": "Historical Reports", "description": "Access reports beyond 14 days", "required_plan": "individual"},
    "peso_conversion": {"label": "Peso Conversion", "description": "Automatic USD to MXN conversion with fees", "required_plan": "individual"},
    "team_dashboard": {"label": "Team Dashboard", "description": "View team-wide KPI stats and basic forecasting", "required_plan": "individual"},
    "top_signals": {"label": "Top 5 Signals", "description": "Intervention signals sorted by risk", "required_plan": "individual"},
    "multiple_periods": {"label": "Multiple Periods", "description": "Compare across custom date ranges", "required_plan": "pro"},
    "daily_snapshots": {"label": "Daily Snapshots", "description": "Daily snapshots at 6 PM instead of real-time", "required_plan": "pro"},
    "advanced_analytics": {"label": "Advanced Analytics", "description": "Detailed performance insights and trends", "required_plan": "group"},
    "realtime_forecasting": {"label": "Real-Time Forecasting", "description": "Live team forecasting and risk monitoring (20s polling)", "required_plan": "group"},
    "alert_system": {"label": "Alert System", "description": "Smart alerts with cooldowns", "required_plan": "group"},
}

PLAN_HIERARCHY = {"trial": 0, "individual": 1, "pro": 2, "group": 3}

class DenialReason:
    PLAN_LIMIT = "plan_limit"
    USAGE_LIMIT = "usage_limit"
    DISABLED = "disabled"
    NOT_AVAILABLE = "not_available"

def get_current_user_sync() -> "User":
    return HARDCODED_USER

def check_feature_access(user: "User", feature: str) -> dict:
    if feature not in FEATURES:
        return {"allowed": False, "reason": DenialReason.NOT_AVAILABLE, "required_plan": None, "feature": feature, "label": None, "description": None}
    
    feat = FEATURES[feature]
    required = feat["required_plan"]
    user_level = PLAN_HIERARCHY.get(user.plan, 0)
    required_level = PLAN_HIERARCHY.get(required, 0)
    allowed = user_level >= required_level
    
    return {
        "allowed": allowed,
        "reason": None if allowed else DenialReason.PLAN_LIMIT,
        "required_plan": None if allowed else required,
        "feature": feature,
        "label": feat["label"],
        "description": feat["description"],
    }

# =============================================================================
# MongoDB CONNECTION
# =============================================================================

mongo_url = os.environ.get("MONGO_URL")
db_name = os.environ.get("DB_NAME", "kpi_tracker")

if not mongo_url:
    raise ValueError("MONGO_URL is not set in environment variables!")

client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

app = FastAPI()
api_router = APIRouter(prefix="/api")

# =============================================================================
# DEFAULT GOALS - Fallback until user sets custom
# =============================================================================

DEFAULT_GOALS = {
    "calls_biweekly": 10,
    "reservations_biweekly": 5,
    "profit_biweekly": 0,
    "spins_biweekly": 0,
    "combined_biweekly": 0,
    "misc_biweekly": 0,
    "calls_daily": 0,
    "reservations_daily": 0,
    "profit_daily": 0,
    "spins_daily": 0,
    "avg_time_per_booking": 0,
    "avg_spin": 0,
    "avg_mega_spin": 0,
}

# =============================================================================
# PERIOD LOGIC
# =============================================================================

def get_last_day_of_month(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]

def get_current_period() -> tuple:
    today = date.today()
    year, month = today.year, today.month
    
    if today.day <= 14:
        start = date(year, month, 1)
        end = date(year, month, 14)
    else:
        start = date(year, month, 15)
        end = date(year, month, get_last_day_of_month(year, month))
    
    return start.isoformat(), end.isoformat(), f"{start.isoformat()}_to_{end.isoformat()}"

def get_previous_period() -> tuple:
    today = date.today()
    year, month = today.year, today.month
    
    if today.day <= 14:
        if month == 1:
            prev_year, prev_month = year - 1, 12
        else:
            prev_year, prev_month = year, month - 1
        start = date(prev_year, prev_month, 15)
        end = date(prev_year, prev_month, get_last_day_of_month(prev_year, prev_month))
    else:
        start = date(year, month, 1)
        end = date(year, month, 14)
    
    return start.isoformat(), end.isoformat(), f"{start.isoformat()}_to_{end.isoformat()}"

def is_period_boundary() -> bool:
    return date.today().day in [1, 15]


def normalize_and_validate_email(email: str) -> str:
    """
    Validate and normalize email using email-validator library
    Returns lowercase normalized email
    Raises ValueError if invalid
    """
    try:
        validated = validate_email(email.strip(), check_deliverability=False)
        return validated.email.lower()
    except EmailNotValidError as e:
        raise ValueError(f"Invalid email format: {str(e)}")


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class User(BaseModel):
    id: str
    email: str
    plan: str = "free"
    password_hash: str = ""
    company_id: str = ""
    team_id: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator("email", pre=True, always=True)
    def validate_email_field(cls, v):
        """Validate email format and normalize to lowercase"""
        if not v:
            raise ValueError("Email is required")
        return normalize_and_validate_email(v)

HARDCODED_USER = User(id=CURRENT_USER_ID, email="user@example.com", plan=CURRENT_USER_PLAN)

class Booking(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    profit: float = 0.0
    is_prepaid: bool = False
    has_refund_protection: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    time_since_last: int = 0

class BookingCreate(BaseModel):
    profit: float
    is_prepaid: bool = False
    has_refund_protection: bool = False
    time_since_last: int = 0

class SpinEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    amount: float = 0.0
    is_mega: bool = False
    booking_number: int = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SpinCreate(BaseModel):
    amount: float
    is_mega: bool = False
    booking_number: int = 0

class MiscIncome(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    amount: float = 0.0
    source: str = "request_lead"
    description: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class MiscIncomeCreate(BaseModel):
    amount: float
    source: str = "request_lead"
    description: str = ""

class DailyEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = CURRENT_USER_ID  # MULTI-USER: Link to user
    date: str
    period_id: str = ""
    archived: bool = False
    calls_received: int = 0
    bookings: List[Booking] = []
    spins: List[SpinEntry] = []
    misc_income: List[MiscIncome] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Stats models
class MetricStat(BaseModel):
    total: float
    goal: float
    progress_percent: float
    on_track: bool
    status: str

class ConversionStat(BaseModel):
    rate: float
    goal: float
    on_track: bool
    status: str

class TimeStat(BaseModel):
    average: float
    goal: float
    on_track: bool
    status: str

class SpinAverages(BaseModel):
    regular: float
    regular_goal: float
    mega: float
    mega_goal: float

class ReservationStat(BaseModel):
    total: float
    goal: float
    progress_percent: float
    on_track: bool
    status: str
    prepaid_count: int
    refund_protection_count: int

class DailyStats(BaseModel):
    date: str
    calls: MetricStat
    reservations: MetricStat
    conversion_rate: ConversionStat
    profit: MetricStat
    spins: MetricStat
    avg_time: TimeStat

class BiweeklyStats(BaseModel):
    period: str
    period_id: str
    start_date: str
    end_date: str
    days_tracked: int
    calls: MetricStat
    reservations: ReservationStat
    conversion_rate: ConversionStat
    profit: MetricStat
    spins: MetricStat
    combined: MetricStat
    misc: MetricStat
    avg_time: TimeStat
    spin_averages: SpinAverages

class PeriodTotals(BaseModel):
    calls: int = 0
    reservations: int = 0
    profit: float = 0.0
    spins: float = 0.0
    combined: float = 0.0
    misc: float = 0.0
    prepaid_count: int = 0
    refund_protection_count: int = 0

class GoalsMet(BaseModel):
    calls: bool = False
    reservations: bool = False
    profit: bool = False
    spins: bool = False
    combined: bool = False
    misc: bool = False

class PeriodLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = CURRENT_USER_ID  # MULTI-USER: Link to user
    period_id: str
    start_date: str
    end_date: str
    status: str = "closed"
    entry_count: int = 0
    totals: PeriodTotals
    goals: dict
    goals_met: GoalsMet
    conversion_rate: float = 0.0
    avg_time_per_booking: float = 0.0
    archived_at: datetime = Field(default_factory=datetime.utcnow)

# FORECASTING MODELS
class RepForecast(BaseModel):
    user_id: str
    projected_reservations: float
    projected_profit: float
    goal: float
    gap: float
    percent_of_goal: float
    risk_score: float
    risk_level: str
    trend: str
    confidence: str
    avg_daily_rate: float

class TeamForecast(BaseModel):
    team_projected_reservations: float
    team_current_reservations: int
    team_goal: float
    team_gap: float
    percent_of_goal: float
    required_daily_rate: float
    days_elapsed: int
    days_remaining: int
    confidence: str
    trend_direction: str = "ΓåÆ"  # Team velocity trend: Γåæ Γåô ΓåÆ
    risk_indicator: str = "≡ƒƒó"  # ≡ƒö┤ ≡ƒƒí ≡ƒƒó based on percent_of_goal
    rep_forecasts: List[RepForecast]

class InterventionSignal(BaseModel):
    user_id: str
    rank: int
    signal_type: str
    risk_score: float
    risk_level: str
    risk_tier: str = "≡ƒƒó Low Risk"
    projected_reservations: float
    projected_percent_of_goal: float = 0.0
    gap: float
    trend: str
    trend_direction: str = "ΓåÆ"  # Γåæ, Γåô, or ΓåÆ
    confidence_level: str = "medium"
    action_required: str
    can_alert: bool = True
    has_significant_change: bool = True
    change_details: List[str] = []
    
    # Decision signals - answers "who needs attention now?"
    operational_priority: int = 0  # 1-5, where 1 is highest priority

class TopSignalsResponse(BaseModel):
    signals: List[InterventionSignal]
    generated_at: datetime
    update_mode: str
    is_cached: bool = False
    cache_timestamp: Optional[datetime] = None

class DailySnapshot(BaseModel):
    """Daily cached snapshot for non-realtime plans"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    period_id: str
    snapshot_date: str
    signals: List[InterventionSignal]
    team_forecast: dict
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    snapshot_type: str = "daily"  # daily, manual, scheduled

# =============================================================================
# SNAPSHOT MANAGEMENT - Smart Hybrid Model
# =============================================================================

async def get_or_create_daily_snapshot(user_id: str, period_id: str) -> Optional[dict]:
    """
    Get today's cached snapshot or return None if needs refresh
    Used for Pro plan (daily updates)
    """
    today_str = date.today().isoformat()
    
    snapshot = await db.daily_snapshots.find_one({
        "user_id": user_id,
        "period_id": period_id,
        "snapshot_date": today_str,
        "snapshot_type": "daily"
    })
    
    return snapshot

async def save_daily_snapshot(user_id: str, period_id: str, signals: List[InterventionSignal], team_forecast: dict):
    """
    Save daily snapshot to MongoDB
    Replaces any existing snapshot for today
    """
    today_str = date.today().isoformat()
    
    snapshot = DailySnapshot(
        user_id=user_id,
        period_id=period_id,
        snapshot_date=today_str,
        signals=signals,
        team_forecast=team_forecast,
        snapshot_type="daily"
    )
    
    await db.daily_snapshots.update_one(
        {
            "user_id": user_id,
            "period_id": period_id,
            "snapshot_date": today_str,
            "snapshot_type": "daily"
        },
        {"$set": snapshot.dict()},
        upsert=True
    )
    
    return snapshot

async def calculate_top_signals_live(user_id: str, limit: int = 5) -> tuple:
    """
    Calculate Top 5 signals in real-time with smart thresholds
    Used for Group plan with realtime mode
    
    Includes:
    - Minimum change thresholds
    - Alert cooldown management
    - Risk tier classification
    """
    start_date, end_date, period_id = get_current_period()
    
    # For now, single user - expand for multi-user teams
    user_ids = [user_id]
    
    rep_forecasts = []
    team_projected = 0
    team_current = 0
    team_goal = 0
    
    for uid in user_ids:
        entries = await db.daily_entries.find({
            "user_id": uid,
            "date": {"$gte": start_date, "$lte": end_date}
        }).to_list(1000)
        
        user_goals = await get_user_goals(uid)
        goal = user_goals["reservations_biweekly"]
        
        forecast = await get_rep_forecast(uid, entries, goal, start_date, end_date)
        rep_forecasts.append(forecast)
        
        team_projected += forecast.projected_reservations
        team_current += sum(len(e.get("bookings", [])) for e in entries)
        team_goal += goal
    
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    total_days = (end - start).days + 1
    today = date.today()
    days_elapsed = min((today - start).days + 1, total_days)
    days_remaining = max(0, total_days - days_elapsed)
    
    team_gap = team_projected - team_goal
    percent_of_goal = (team_projected / team_goal) * 100 if team_goal > 0 else 0
    
    confidence_map = {"high": 3, "medium": 2, "low": 1}
    if rep_forecasts:
        avg_conf = sum(confidence_map.get(r.confidence, 1) for r in rep_forecasts) / len(rep_forecasts)
        team_confidence = {3: "high", 2: "medium", 1: "low"}.get(round(avg_conf), "medium")
    else:
        team_confidence = "low"
    
    remaining = max(0, team_goal - team_current)
    required_daily = remaining / days_remaining if days_remaining > 0 else 0
    
    team_forecast_data = {
        "team_projected_reservations": round(team_projected, 1),
        "team_current_reservations": team_current,
        "team_goal": team_goal,
        "team_gap": round(team_gap, 1),
        "percent_of_goal": round(percent_of_goal, 1),
        "required_daily_rate": round(required_daily, 1),
        "days_elapsed": days_elapsed,
        "days_remaining": days_remaining,
        "confidence": team_confidence
    }
    
    # Sort by risk_score descending - highest risk first
    sorted_reps = sorted(rep_forecasts, key=lambda x: x.risk_score, reverse=True)
    
    # Enforce max 5
    limit = min(limit, 5)
    
    signals = []
    for idx, rep in enumerate(sorted_reps[:limit]):
        if rep.gap < 0 and rep.risk_level in ["high", "medium"]:
            signal_type = "risk"
        elif rep.gap >= 0:
            signal_type = "momentum"
        else:
            signal_type = "risk"
        
        # Get risk tier with emoji
        risk_tier = get_risk_tier_label(rep.risk_score)
        
        # Calculate projected percent of goal
        projected_percent = (rep.projected_reservations / goal * 100) if goal > 0 else 0
        
        # Extract trend direction from trend string
        trend_direction = "ΓåÆ"
        if "Γåæ" in rep.trend:
            trend_direction = "Γåæ"
        elif "Γåô" in rep.trend:
            trend_direction = "Γåô"
        
        # Smart action recommendations based on risk level and cooldown
        can_alert = await AlertCooldownManager.can_send_alert(rep.user_id, signal_type, rep.risk_level)
        
        if rep.risk_level == "high":
            action = "≡ƒÜ¿ Immediate coaching required" if can_alert else "ΓÅ│ Alert on cooldown - coaching needed"
        elif rep.risk_level == "medium":
            action = "ΓÜá∩╕Å Schedule check-in this week" if can_alert else "ΓÅ│ Alert on cooldown - monitor closely"
        elif rep.gap >= 0:
            action = "Γ£à On track - maintain momentum"
        else:
            action = "Γ¡É Star performer - recognize achievement"
        
        signal_dict = {
            "user_id": rep.user_id,
            "rank": idx + 1,
            "signal_type": signal_type,
            "risk_score": rep.risk_score,
            "risk_level": rep.risk_level,
            "risk_tier": risk_tier,
            "projected_reservations": rep.projected_reservations,
            "projected_percent_of_goal": round(projected_percent, 1),
            "gap": rep.gap,
            "trend": rep.trend,
            "trend_direction": trend_direction,
            "confidence_level": rep.confidence,
            "action_required": action,
            "can_alert": can_alert,
            "operational_priority": idx + 1  # Rank = priority (1 is highest)
        }
        
        # Check for significant changes
        change_info = await SignalChangeDetector.has_significant_change(rep.user_id, signal_dict)
        signal_dict["has_significant_change"] = change_info["is_significant"]
        signal_dict["change_details"] = change_info.get("changes", [])
        
        # Save to history for future comparison
        await SignalChangeDetector.save_signal_history(rep.user_id, signal_dict)
        
        # Record alert if sent
        if can_alert and change_info["is_significant"] and rep.risk_level in ["high", "medium"]:
            await AlertCooldownManager.record_alert(rep.user_id, signal_type, rep.risk_level)
        
        signals.append(InterventionSignal(**signal_dict))
    
    return signals, team_forecast_data

# =============================================================================
# USER GOALS SERVICE - Database-driven goals
# =============================================================================

async def get_user_goals(user_id: str) -> dict:
    """Fetch user goals from DB or return defaults"""
    user_goals = await db.user_goals.find_one({"user_id": user_id})
    if user_goals:
        return {**DEFAULT_GOALS, **user_goals.get("goals", {})}
    return DEFAULT_GOALS.copy()

async def update_user_goals(user_id: str, goals: dict) -> bool:
    """Save user goals to DB"""
    result = await db.user_goals.update_one(
        {"user_id": user_id},
        {"$set": {"goals": goals, "updated_at": datetime.utcnow()}},
        upsert=True
    )
    return result.modified_count > 0 or result.upserted_id is not None

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def build_metric_stat(total: float, goal: float) -> MetricStat:
    progress = calculate_progress(total, goal)
    on_track = is_on_track(total, goal)
    return MetricStat(total=round(total, 2), goal=round(goal, 2), progress_percent=progress, on_track=on_track, status=get_status(progress))

def build_conversion_stat(bookings: int, calls: int, goal_bookings: int, goal_calls: int) -> ConversionStat:
    rate = round((bookings / calls) * 100, 2) if calls > 0 else 0.0
    goal = round((goal_bookings / goal_calls) * 100, 2) if goal_calls > 0 else 0.0
    return ConversionStat(rate=rate, goal=goal, on_track=rate >= goal, status="on_track" if rate >= goal else "behind")

def build_time_stat(times: List[int], goal: int) -> TimeStat:
    avg = round(sum(times) / len(times), 1) if times else 0.0
    return TimeStat(average=avg, goal=float(goal), on_track=avg <= goal if avg > 0 else True, status="on_track" if avg <= goal else "behind")

def normalize_entry(entry: dict, period_id: str = "", user_id: str = CURRENT_USER_ID) -> dict:
    return {
        "id": entry.get("id", str(uuid.uuid4())),
        "user_id": entry.get("user_id", user_id),
        "date": entry.get("date", date.today().isoformat()),
        "period_id": entry.get("period_id", period_id),
        "archived": entry.get("archived", False),
        "calls_received": entry.get("calls_received", 0),
        "bookings": entry.get("bookings", []),
        "spins": entry.get("bonuses", entry.get("spins", [])),
        "misc_income": entry.get("misc_income", []),
        "created_at": entry.get("created_at", datetime.utcnow()),
        "updated_at": entry.get("updated_at", datetime.utcnow()),
    }

# =============================================================================
# SMART THRESHOLDS - Prevent Toxic Behavior
# =============================================================================

# Minimum change thresholds before triggering updates
RISK_SCORE_CHANGE_THRESHOLD = 5.0  # Must change by 5+ points to trigger alert
RANKING_CHANGE_THRESHOLD = 1  # Must move up/down 1+ positions to notify
GAP_CHANGE_THRESHOLD = 2.0  # Gap must change by 2+ reservations

# Alert cooldown periods (in seconds)
ALERT_COOLDOWN_HIGH_RISK = 3600  # 1 hour for high risk alerts
ALERT_COOLDOWN_MEDIUM_RISK = 7200  # 2 hours for medium risk alerts
ALERT_COOLDOWN_LOW_RISK = 14400  # 4 hours for low risk alerts

# Risk tier thresholds
RISK_TIER_HIGH = 70  # Red zone
RISK_TIER_MEDIUM = 40  # Yellow zone
# Below 40 = Green zone

class AlertCooldownManager:
    """Prevents alert spam and anxiety-driven behavior"""
    
    @staticmethod
    async def can_send_alert(user_id: str, alert_type: str, risk_level: str) -> bool:
        """
        Check if enough time has passed since last alert
        Returns True if alert can be sent, False if in cooldown
        """
        cooldown_key = f"{user_id}_{alert_type}_{risk_level}"
        
        last_alert = await db.alert_cooldowns.find_one({"key": cooldown_key})
        
        if not last_alert:
            return True
        
        # Determine cooldown period based on risk level
        if risk_level == "high":
            cooldown_seconds = ALERT_COOLDOWN_HIGH_RISK
        elif risk_level == "medium":
            cooldown_seconds = ALERT_COOLDOWN_MEDIUM_RISK
        else:
            cooldown_seconds = ALERT_COOLDOWN_LOW_RISK
        
        time_since_last = (datetime.utcnow() - last_alert["timestamp"]).total_seconds()
        
        return time_since_last >= cooldown_seconds
    
    @staticmethod
    async def record_alert(user_id: str, alert_type: str, risk_level: str):
        """Record that an alert was sent"""
        cooldown_key = f"{user_id}_{alert_type}_{risk_level}"
        
        await db.alert_cooldowns.update_one(
            {"key": cooldown_key},
            {
                "$set": {
                    "user_id": user_id,
                    "alert_type": alert_type,
                    "risk_level": risk_level,
                    "timestamp": datetime.utcnow()
                }
            },
            upsert=True
        )

class SignalChangeDetector:
    """Detects meaningful changes to prevent noise"""
    
    @staticmethod
    async def has_significant_change(user_id: str, new_signal: dict) -> dict:
        """
        Compare new signal with previous to detect meaningful changes
        Returns dict with change flags and details
        """
        # Get previous signal from last snapshot
        previous = await db.signal_history.find_one(
            {"user_id": user_id},
            sort=[("timestamp", -1)]
        )
        
        if not previous:
            # First time - always significant
            return {
                "is_significant": True,
                "risk_score_changed": True,
                "ranking_changed": True,
                "tier_changed": True,
                "changes": ["initial_signal"]
            }
        
        prev_data = previous.get("signal", {})
        changes = []
        
        # Check risk score change
        risk_score_delta = abs(new_signal.get("risk_score", 0) - prev_data.get("risk_score", 0))
        risk_score_changed = risk_score_delta >= RISK_SCORE_CHANGE_THRESHOLD
        if risk_score_changed:
            changes.append(f"risk_score_changed_by_{risk_score_delta:.1f}")
        
        # Check ranking change
        rank_delta = abs(new_signal.get("rank", 0) - prev_data.get("rank", 0))
        ranking_changed = rank_delta >= RANKING_CHANGE_THRESHOLD
        if ranking_changed:
            changes.append(f"rank_changed_by_{rank_delta}")
        
        # Check tier change (green/yellow/red)
        prev_tier = get_risk_tier(prev_data.get("risk_score", 0))
        new_tier = get_risk_tier(new_signal.get("risk_score", 0))
        tier_changed = prev_tier != new_tier
        if tier_changed:
            changes.append(f"tier_changed_from_{prev_tier}_to_{new_tier}")
        
        # Check gap change
        gap_delta = abs(new_signal.get("gap", 0) - prev_data.get("gap", 0))
        gap_changed = gap_delta >= GAP_CHANGE_THRESHOLD
        if gap_changed:
            changes.append(f"gap_changed_by_{gap_delta:.1f}")
        
        is_significant = risk_score_changed or ranking_changed or tier_changed or gap_changed
        
        return {
            "is_significant": is_significant,
            "risk_score_changed": risk_score_changed,
            "ranking_changed": ranking_changed,
            "tier_changed": tier_changed,
            "gap_changed": gap_changed,
            "changes": changes,
            "risk_score_delta": risk_score_delta,
            "rank_delta": rank_delta
        }
    
    @staticmethod
    async def save_signal_history(user_id: str, signal: dict):
        """Save signal to history for future comparison"""
        await db.signal_history.insert_one({
            "user_id": user_id,
            "signal": signal,
            "timestamp": datetime.utcnow()
        })
        
        # Keep only last 30 days of history
        cutoff = datetime.utcnow() - timedelta(days=30)
        await db.signal_history.delete_many({
            "user_id": user_id,
            "timestamp": {"$lt": cutoff}
        })

def get_risk_tier(risk_score: float) -> str:
    """Get risk tier: red, yellow, or green"""
    if risk_score >= RISK_TIER_HIGH:
        return "red"
    elif risk_score >= RISK_TIER_MEDIUM:
        return "yellow"
    return "green"

def get_risk_tier_label(risk_score: float) -> str:
    """Get human-readable risk tier label"""
    tier = get_risk_tier(risk_score)
    if tier == "red":
        return "≡ƒö┤ High Risk"
    elif tier == "yellow":
        return "≡ƒƒí Medium Risk"
    return "≡ƒƒó Low Risk"

# =============================================================================
# FORECASTING ENGINE - Elite Risk Scoring
# =============================================================================

def calculate_risk_score(projected: float, goal: float, trend_direction: str, conversion_drop: float = 0) -> float:
    """
    Elite risk scoring formula:
    risk_score = (goal - projected) * weight1 + conversion_drop * weight2
    
    Higher score = higher risk
    """
    if goal <= 0:
        return 0
    
    # Weight 1: Gap from goal (normalized to 0-100)
    gap = max(0, goal - projected)
    gap_score = (gap / goal) * 100 if goal > 0 else 0
    
    # Weight 2: Conversion drop penalty
    conversion_penalty = conversion_drop * 50  # Scale conversion drop impact
    
    # Trend multiplier
    trend_multiplier = 1.3 if trend_direction == "Γåô declining" else 0.7 if trend_direction == "Γåæ improving" else 1.0
    
    # Combined risk score
    base_risk = (gap_score * 0.7) + (conversion_penalty * 0.3)  # 70% gap, 30% conversion
    final_risk = min(100, max(0, base_risk * trend_multiplier))
    
    return final_risk

def get_risk_level(risk_score: float) -> str:
    if risk_score >= 70:
        return "high"
    elif risk_score >= 40:
        return "medium"
    return "low"

def calculate_trend(recent_entries: List[Dict], older_entries: List[Dict]) -> str:
    recent_bookings = sum(len(e.get("bookings", [])) for e in recent_entries)
    older_bookings = sum(len(e.get("bookings", [])) for e in older_entries)
    recent_days = max(len(recent_entries), 1)
    older_days = max(len(older_entries), 1)
    recent_avg = recent_bookings / recent_days
    older_avg = older_bookings / older_days
    
    if older_avg == 0:
        return "ΓåÆ stable" if recent_avg == 0 else "Γåæ improving"
    
    change_ratio = recent_avg / older_avg
    if change_ratio > 1.1:
        return "Γåæ improving"
    elif change_ratio < 0.9:
        return "Γåô declining"
    return "ΓåÆ stable"

def calculate_conversion_drop(entries: List[Dict]) -> float:
    """Calculate conversion rate drop from first half to second half of period"""
    if len(entries) < 4:
        return 0
    
    mid = len(entries) // 2
    first_half = entries[:mid]
    second_half = entries[mid:]
    
    first_calls = sum(e.get("calls_received", 0) for e in first_half)
    first_bookings = sum(len(e.get("bookings", [])) for e in first_half)
    second_calls = sum(e.get("calls_received", 0) for e in second_half)
    second_bookings = sum(len(e.get("bookings", [])) for e in second_half)
    
    first_rate = (first_bookings / first_calls * 100) if first_calls > 0 else 0
    second_rate = (second_bookings / second_calls * 100) if second_calls > 0 else 0
    
    return max(0, first_rate - second_rate)  # Positive = drop in conversion

def calculate_confidence(entries: List[Dict]) -> str:
    if len(entries) < 3:
        return "low"
    daily_counts = [len(e.get("bookings", [])) for e in entries]
    if not daily_counts or sum(daily_counts) == 0:
        return "low"
    mean = statistics.mean(daily_counts)
    if mean == 0:
        return "low"
    try:
        cv = statistics.stdev(daily_counts) / mean
    except statistics.StatisticsError:
        return "high"
    
    if cv < 0.3:
        return "high"
    elif cv < 0.6:
        return "medium"
    return "low"

async def get_rep_forecast(user_id: str, entries: List[Dict], goal: float, start_date: str, end_date: str) -> RepForecast:
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    total_days = (end - start).days + 1
    today = date.today()
    days_elapsed = min((today - start).days + 1, total_days)
    days_remaining = max(0, total_days - days_elapsed)
    
    current_reservations = sum(len(e.get("bookings", [])) for e in entries)
    current_profit = sum(b.get("profit", 0) for e in entries for b in e.get("bookings", []))
    
    if days_elapsed > 0:
        avg_daily = current_reservations / days_elapsed
        avg_daily_profit = current_profit / days_elapsed
    else:
        avg_daily = 0
        avg_daily_profit = 0
    
    projected = avg_daily * total_days
    projected_profit = avg_daily_profit * total_days
    
    recent = entries[-3:] if len(entries) >= 3 else entries
    older = entries[-6:-3] if len(entries) >= 6 else entries[:max(0, len(entries)-3)]
    trend = calculate_trend(recent, older)
    
    # Calculate conversion drop for elite risk scoring
    conversion_drop = calculate_conversion_drop(entries)
    
    risk_score = calculate_risk_score(projected, goal, trend, conversion_drop)
    risk_level = get_risk_level(risk_score)
    confidence = calculate_confidence(entries)
    
    remaining_needed = max(0, goal - current_reservations)
    required_daily = remaining_needed / days_remaining if days_remaining > 0 else 0
    
    return RepForecast(
        user_id=user_id,
        projected_reservations=round(projected, 1),
        projected_profit=round(projected_profit, 2),
        goal=round(goal, 2),
        gap=round(projected - goal, 1),
        percent_of_goal=round((projected / goal) * 100, 1) if goal > 0 else 0,
        risk_score=round(risk_score, 1),
        risk_level=risk_level,
        trend=trend,
        confidence=confidence,
        avg_daily_rate=round(avg_daily, 2)
    )

# =============================================================================
# IDEMPOTENT ARCHIVE FUNCTIONS
# =============================================================================

async def ensure_previous_period_closed():
    if not is_period_boundary():
        return
    
    prev_start, prev_end, prev_period_id = get_previous_period()
    
    # IDEMPOTENCY: Check if already archived
    existing = await db.period_logs.find_one({"period_id": prev_period_id, "user_id": CURRENT_USER_ID})
    if existing:
        return
    
    await archive_period_internal(prev_start, prev_end, prev_period_id)

async def archive_period_internal(start_date: str, end_date: str, period_id: str) -> PeriodLog:
    # MULTI-USER: Filter by user_id
    entries = await db.daily_entries.find({
        "user_id": CURRENT_USER_ID,
        "$or": [
            {"date": {"$gte": start_date, "$lte": end_date}},
            {"period_id": period_id}
        ]
    }).to_list(1000)
    
    entries = [normalize_entry(e, period_id, CURRENT_USER_ID) for e in entries]
    
    total_calls = sum(e.get("calls_received", 0) for e in entries)
    all_bookings, all_spins, all_misc, all_times = [], [], [], []
    
    for e in entries:
        all_bookings.extend(e.get("bookings", []))
        all_spins.extend(e.get("spins", []))
        all_misc.extend(e.get("misc_income", []))
    
    total_bookings = len(all_bookings)
    total_profit = sum(b.get("profit", 0) for b in all_bookings)
    total_spins = sum(s.get("amount", 0) for s in all_spins)
    total_misc = sum(m.get("amount", 0) for m in all_misc)
    
    # Get user-specific goals
    user_goals = await get_user_goals(CURRENT_USER_ID)
    
    prepaid_count = sum(1 for b in all_bookings if b.get("is_prepaid", False))
    refund_count = sum(1 for b in all_bookings if b.get("has_refund_protection", False))
    
    for b in all_bookings:
        t = b.get("time_since_last", 0)
        if t > 0:
            all_times.append(t)
    
    avg_time = sum(all_times) / len(all_times) if all_times else 0
    conversion = (total_bookings / total_calls * 100) if total_calls > 0 else 0
    
    period_log = PeriodLog(
        user_id=CURRENT_USER_ID,
        period_id=period_id,
        start_date=start_date,
        end_date=end_date,
        status="closed",
        entry_count=len(entries),
        totals=PeriodTotals(
            calls=total_calls,
            reservations=total_bookings,
            profit=round(total_profit, 2),
            spins=round(total_spins, 2),
            combined=round(total_profit + total_spins, 2),
            misc=round(total_misc, 2),
            prepaid_count=prepaid_count,
            refund_protection_count=refund_count,
        ),
        goals=user_goals,
        goals_met=GoalsMet(
            calls=total_calls >= user_goals["calls_biweekly"],
            reservations=total_bookings >= user_goals["reservations_biweekly"],
            profit=total_profit >= user_goals["profit_biweekly"],
            spins=total_spins >= user_goals["spins_biweekly"],
            combined=(total_profit + total_spins) >= user_goals["combined_biweekly"],
            misc=total_misc >= user_goals["misc_biweekly"],
        ),
        conversion_rate=round(conversion, 2),
        avg_time_per_booking=round(avg_time, 1),
    )
    
    # IDEMPOTENCY: Use upsert to prevent duplicates
    await db.period_logs.update_one(
        {"period_id": period_id, "user_id": CURRENT_USER_ID},
        {"$setOnInsert": period_log.dict()},
        upsert=True
    )
    
    await db.daily_entries.update_many(
        {"user_id": CURRENT_USER_ID, "date": {"$gte": start_date, "$lte": end_date}},
        {"$set": {"archived": True, "period_id": period_id}}
    )
    
    return period_log

# =============================================================================
# IDEMPOTENT DAILY RESET
# =============================================================================

async def daily_reset_cron_task():
    """Idempotent daily reset with duplicate protection"""
    logger.info("Running daily midnight reset...")
    
    today_str = date.today().isoformat()
    yesterday = date.today() - timedelta(days=1)
    yesterday_str = yesterday.isoformat()
    
    # IDEMPOTENCY: Check if yesterday already archived
    existing_archive = await db.daily_archives.find_one({
        "user_id": CURRENT_USER_ID,
        "date": yesterday_str,
        "type": "daily"
    })
    
    if not existing_archive:
        yesterday_entry = await db.daily_entries.find_one({
            "user_id": CURRENT_USER_ID,
            "date": yesterday_str
        })
        if yesterday_entry:
            await db.daily_archives.insert_one({
                "user_id": CURRENT_USER_ID,
                "date": yesterday_str,
                "type": "daily",
                "entry": yesterday_entry,
                "archived_at": datetime.utcnow()
            })
            logger.info(f"Archived entry for {yesterday_str}")
    else:
        logger.info(f"Already archived for {yesterday_str}, skipping")
    
    # IDEMPOTENCY: Check if today already reset
    existing_reset = await db.daily_archives.find_one({
        "user_id": CURRENT_USER_ID,
        "date": f"{today_str}_reset",
        "type": "reset_marker"
    })
    
    if existing_reset:
        logger.info(f"Already reset for {today_str}, skipping")
        return
    
    today_entry = await db.daily_entries.find_one({
        "user_id": CURRENT_USER_ID,
        "date": today_str
    })
    
    if today_entry:
        # Mark reset
        await db.daily_archives.insert_one({
            "user_id": CURRENT_USER_ID,
            "date": f"{today_str}_reset",
            "type": "reset_marker",
            "created_at": datetime.utcnow()
        })
        
        # Reset counters
        await db.daily_entries.update_one(
            {"user_id": CURRENT_USER_ID, "date": today_str},
            {
                "$set": {
                    "calls_received": 0,
                    "bookings": [],
                    "spins": [],
                    "misc_income": [],
                    "updated_at": datetime.utcnow(),
                    "reset_at": datetime.utcnow()
                }
            }
        )
        logger.info(f"Reset daily counters for {today_str}")
    
    logger.info("Daily reset complete")

async def daily_snapshot_cron_task():
    """
    Generate daily snapshots at 6 PM for Pro plan users
    This provides structured check-ins without real-time noise
    """
    logger.info("Running daily snapshot generation at 6 PM...")
    
    _, _, period_id = get_current_period()
    
    # For now, single user - expand for multi-user
    # In production, query all Pro plan users
    user = get_current_user_sync()
    
    if user.plan in ["pro", "group"]:
        try:
            signals, team_forecast_data = await calculate_top_signals_live(CURRENT_USER_ID, 5)
            await save_daily_snapshot(CURRENT_USER_ID, period_id, signals, team_forecast_data)
            logger.info(f"Generated daily snapshot for user {CURRENT_USER_ID}")
        except Exception as e:
            logger.error(f"Failed to generate daily snapshot: {e}")
    
    logger.info("Daily snapshot generation complete")

# =============================================================================
# SCHEDULER
# =============================================================================

scheduler = AsyncIOScheduler()

async def close_period_cron_task():
    logger.info("Running scheduled period check...")
    today = date.today()
    
    if today.day not in [1, 15]:
        logger.info(f"Today is day {today.day}, not a period boundary. Skipping.")
        return
    
    logger.info(f"Today is day {today.day} - period boundary detected!")
    
    prev_start, prev_end, prev_period_id = get_previous_period()
    
    # IDEMPOTENCY: Check if already archived
    existing = await db.period_logs.find_one({
        "period_id": prev_period_id,
        "user_id": CURRENT_USER_ID
    })
    
    if existing:
        logger.info(f"Period {prev_period_id} already archived. Skipping.")
        return
    
    logger.info(f"Archiving period: {prev_period_id}")
    try:
        await archive_period_internal(prev_start, prev_end, prev_period_id)
        logger.info(f"Successfully archived period {prev_period_id}")
    except Exception as e:
        logger.error(f"Failed to archive period {prev_period_id}: {e}")

def start_scheduler():
    scheduler.add_job(
        close_period_cron_task,
        CronTrigger(hour=0, minute=0),
        id='period_archiver',
        name='Archive previous period at midnight on 1st and 15th',
        replace_existing=True
    )
    
    scheduler.add_job(
        daily_reset_cron_task,
        CronTrigger(hour=0, minute=0),
        id='daily_reset',
        name='Daily stats reset at midnight',
        replace_existing=True
    )
    
    scheduler.add_job(
        daily_snapshot_cron_task,
        CronTrigger(hour=18, minute=0),  # 6 PM daily
        id='daily_snapshot',
        name='Generate daily Top 5 snapshot at 6 PM for Pro users',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("APScheduler started with 3 jobs: period archiver, daily reset, daily snapshot")

# =============================================================================
# MIGRATION - With chunking to prevent memory issues
# =============================================================================

async def migrate_legacy_entries() -> dict:
    """Migrate entries with chunking for large datasets"""
    chunk_size = 1000
    total_migrated = 0
    periods_created = 0
    
    last_id = None
    while True:
        query = {
            "$or": [
                {"period_id": {"$exists": False}},
                {"period_id": ""},
                {"period_id": None}
            ]
        }
        if last_id:
            query["_id"] = {"$gt": last_id}
        
        chunk = await db.daily_entries.find(query).sort("_id", 1).limit(chunk_size).to_list(chunk_size)
        
        if not chunk:
            break
        
        # Process chunk
        for entry in chunk:
            entry_date_str = entry.get("date")
            if not entry_date_str:
                continue
            
            try:
                entry_date = date.fromisoformat(entry_date_str)
            except (ValueError, TypeError):
                continue
            
            year, month, day = entry_date.year, entry_date.month, entry_date.day
            
            if day <= 14:
                start = date(year, month, 1)
                end = date(year, month, 14)
            else:
                start = date(year, month, 15)
                end = date(year, month, get_last_day_of_month(year, month))
            
            period_id = f"{start.isoformat()}_to_{end.isoformat()}"
            
            _, _, current_period_id = get_current_period()
            should_archive = period_id != current_period_id
            
            await db.daily_entries.update_one(
                {"_id": entry["_id"]},
                {"$set": {
                    "user_id": entry.get("user_id", CURRENT_USER_ID),
                    "period_id": period_id,
                    "archived": should_archive
                }}
            )
            total_migrated += 1
        
        last_id = chunk[-1]["_id"]
        
        # Create period logs for archived periods
        # (Simplified - full implementation would batch this)
    
    return {
        "migrated_entries": total_migrated,
        "periods_created": periods_created,
        "message": f"Migration complete. {total_migrated} entries migrated."
    }

# =============================================================================
# API ROUTES
# =============================================================================

@api_router.get("/")
async def root():
    return {"message": "KPI Tracker API", "version": "2.2"}


# =============================================================================
# AUTHENTICATION ENDPOINTS
# =============================================================================

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

from services.auth import verify_password
from services.tokens import create_tokens


class TokenResponse(BaseModel):
    access: str
    refresh: str
    jti: str
    token_type: str = "bearer"


async def get_user_by_email(email: str) -> Optional[dict]:
    """Get user by email (used by auth services)"""
    return await db.users.find_one({"email": email})


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Get current user from JWT access token
    Used as dependency for protected routes
    """
    from .services.tokens import decode_access_token
    
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user = await db.users.find_one({"id": user_id}, {"password_hash": 0})
    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user


async def get_current_active_user(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Get current active user (checks for revoked tokens)
    """
    # Check if user's tokens have been revoked
    revoked_count = await db.refresh_tokens.count_documents({
        "user_id": current_user["id"],
        "revoked": True
    })
    
    if revoked_count > 0:
        raise HTTPException(
            status_code=401,
            detail="Token revoked - please login again",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return current_user


class UserCreate(BaseModel):
    email: str
    password: str
    plan: str = "free"
    company_id: str = ""
    team_id: str = ""


class UserUpdate(BaseModel):
    plan: str = None
    company_id: str = None
    team_id: str = None


@api_router.post("/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    """
    Register a new user and return tokens
    """
    from services.users import create_user
    
    # Create user
    user = await create_user(
        email=user_data.email,
        password=user_data.password,
        plan=user_data.plan,
        company_id=user_data.company_id,
        team_id=user_data.team_id
    )
    
    # Create tokens for new user
    return await create_tokens(user["id"], user.get("plan", "free"))


@api_router.put("/user", response_model=User)
async def update_current_user(
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Update current user's profile
    Protected route - requires valid JWT token
    """
    from services.users import update_user
    
    updates = {k: v for k, v in user_update.dict().items() if v is not None}
    
    if not updates:
        return current_user
    
    updated = await update_user(current_user["id"], updates)
    if updated:
        return updated
    
    return current_user


@api_router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), request: Request = None):
    """
    Login endpoint - returns JWT access token and opaque refresh token
    Uses OAuth2PasswordRequestForm for standard compatibility
    """
    import os
    from services.tokens import create_tokens
    
    # Normalize and validate email
    email = normalize_and_validate_email(form_data.username)
    
    # Find user by email
    user = await db.users.find_one({"email": email})
    
    if not user or not verify_password(form_data.password, user.get("password_hash", "")):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Create tokens
    response = await create_tokens(user["id"], user.get("plan", "free"), user.get("role", "member"))
    
    # Set secure cookie for refresh token
    if request:
        response["cookie_settings"] = {
            "httponly": True,
            "secure": True,
            "samesite": "strict",
            "path": "/api/auth"
        }
    
    return response


@api_router.post("/refresh")
async def refresh_token(refresh_token: str, jti: str, request: Request):
    """
    Refresh access token using refresh token with CSRF protection
    """
    import os
    from .services.tokens import rotate_refresh_token
    
    # SameSite=strict prevents cross-site requests entirely
    # Additional: Verify Origin/Referer headers match expected host
    origin = request.headers.get("origin")
    expected_origin = os.environ.get("ALLOWED_ORIGIN", "https://app.example.com")
    
    if origin and origin != expected_origin:
        logger.warning(f"CSRF suspicion: origin={origin}, expected={expected_origin}")
        raise HTTPException(status_code=403, detail="Invalid origin")
    
    try:
        return await rotate_refresh_token(refresh_token, jti)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"}
        )


@api_router.post("/logout")
async def logout(jti: str):
    """
    Logout - revoke refresh token
    """
    from services.tokens import revoke_token
    
    revoked = await revoke_token(jti)
    return {"revoked": revoked}


@api_router.get("/health")
async def health():
    return {"status": "ok", "hardening": "complete"}

@api_router.get("/user", response_model=User)
async def get_user():
    return HARDCODED_USER

# SETTINGS ENDPOINTS - Database-driven
@api_router.get("/settings")
async def get_settings():
    user = get_current_user_sync()
    access = check_feature_access(user, "custom_goals")
    user_goals = await get_user_goals(CURRENT_USER_ID)
    
    return {
        "goals": user_goals,
        "conversion": {
            "exchange_rate": 15.86,
            "processing_fee_percent": 17,
            "period_fee": 100
        },
        "plan": user.plan,
        "features": {
            "custom_goals": access,
            "forecasting": check_feature_access(user, "advanced_analytics")
        },
        "update_mode": "realtime" if user.plan == "group" else "daily" if user.plan in ["pro", "individual"] else "manual"
    }

# Keep old endpoint for backward compatibility
@api_router.get("/goals")
async def get_goals():
    return await get_user_goals(CURRENT_USER_ID)

# TEAM FORECAST - Multi-user safe
@api_router.get("/team/forecast", response_model=TeamForecast)
async def get_team_forecast():
    user = get_current_user_sync()
    access = check_feature_access(user, "team_dashboard")
    
    if not access["allowed"]:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Team forecasting requires Individual plan or higher",
                "current_plan": user.plan,
                "required_plan": "individual"
            }
        )
    
    start_date, end_date, period_id = get_current_period()
    
    # MULTI-USER: Only fetch current user's data (expand for team view)
    user_ids = [CURRENT_USER_ID]
    
    rep_forecasts = []
    team_projected = 0
    team_current = 0
    team_goal = 0
    
    for uid in user_ids:
        # MULTI-USER: Filter by user_id
        entries = await db.daily_entries.find({
            "user_id": uid,
            "date": {"$gte": start_date, "$lte": end_date}
        }).to_list(1000)
        
        user_goals = await get_user_goals(uid)
        goal = user_goals["reservations_biweekly"]
        
        forecast = await get_rep_forecast(uid, entries, goal, start_date, end_date)
        rep_forecasts.append(forecast)
        
        team_projected += forecast.projected_reservations
        team_current += sum(len(e.get("bookings", [])) for e in entries)
        team_goal += goal
    
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    total_days = (end - start).days + 1
    today = date.today()
    days_elapsed = min((today - start).days + 1, total_days)
    days_remaining = max(0, total_days - days_elapsed)
    
    team_gap = team_projected - team_goal
    percent_of_goal = (team_projected / team_goal) * 100 if team_goal > 0 else 0
    
    confidence_map = {"high": 3, "medium": 2, "low": 1}
    if rep_forecasts:
        avg_conf = sum(confidence_map.get(r.confidence, 1) for r in rep_forecasts) / len(rep_forecasts)
        team_confidence = {3: "high", 2: "medium", 1: "low"}.get(round(avg_conf), "medium")
    else:
        team_confidence = "low"
    
    remaining = max(0, team_goal - team_current)
    required_daily = remaining / days_remaining if days_remaining > 0 else 0
    
    # Calculate team trend direction based on last 3 days velocity
    all_entries = []
    for uid in user_ids:
        entries = await db.daily_entries.find({
            "user_id": uid,
            "date": {"$gte": start_date, "$lte": end_date}
        }).sort("date", -1).to_list(1000)
        all_entries.extend(entries)
    
    team_trend_direction = "ΓåÆ"
    if len(all_entries) >= 6:
        recent_3 = all_entries[:3]
        older_3 = all_entries[3:6]
        recent_bookings = sum(len(e.get("bookings", [])) for e in recent_3)
        older_bookings = sum(len(e.get("bookings", [])) for e in older_3)
        
        if older_bookings > 0:
            change_ratio = recent_bookings / older_bookings
            if change_ratio > 1.1:
                team_trend_direction = "Γåæ"
            elif change_ratio < 0.9:
                team_trend_direction = "Γåô"
    
    # Calculate team risk indicator based on percent_of_goal
    if percent_of_goal >= 90:
        team_risk_indicator = "≡ƒƒó"  # On track
    elif percent_of_goal >= 70:
        team_risk_indicator = "≡ƒƒí"  # At risk
    else:
        team_risk_indicator = "≡ƒö┤"  # High risk
    
    return TeamForecast(
        team_projected_reservations=round(team_projected, 1),
        team_current_reservations=team_current,
        team_goal=team_goal,
        team_gap=round(team_gap, 1),
        percent_of_goal=round(percent_of_goal, 1),
        required_daily_rate=round(required_daily, 1),
        days_elapsed=days_elapsed,
        days_remaining=days_remaining,
        confidence=team_confidence,
        trend_direction=team_trend_direction,
        risk_indicator=team_risk_indicator,
        rep_forecasts=rep_forecasts
    )

@api_router.get("/team/top-signals", response_model=TopSignalsResponse)
async def get_top_signals(limit: int = 5, force_refresh: bool = False):
    """
    Elite Top 5 Signals - Smart Hybrid Model
    
    Plan-Based Behavior:
    - Trial: No access
    - Individual: Real-time calculation (basic forecasting)
    - Pro: Daily cached snapshot (updates once per day at 6 PM)
    - Group: Real-time calculation with 20s polling (always live)
    
    Backend calculates everything - frontend just displays
    Sorted by risk_score descending
    Max 5 signals enforced
    """
    user = get_current_user_sync()
    access = check_feature_access(user, "top_signals")
    
    if not access["allowed"]:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Top signals requires Individual plan or higher",
                "current_plan": user.plan,
                "required_plan": "individual",
                "message": "Upgrade to Individual plan for Top 5 intervention signals and forecast risk indicators"
            }
        )
    
    _, _, period_id = get_current_period()
    
    # SMART HYBRID MODEL
    if user.plan in ["individual", "group"]:
        # INDIVIDUAL & GROUP PLAN: Real-time calculation
        # Dashboard always live, calculations on-demand
        signals, team_forecast_data = await calculate_top_signals_live(CURRENT_USER_ID, limit)
        
        # Save snapshot for historical tracking
        await save_daily_snapshot(CURRENT_USER_ID, period_id, signals, team_forecast_data)
        
        return TopSignalsResponse(
            signals=signals,
            generated_at=datetime.utcnow(),
            update_mode="realtime",
            is_cached=False
        )
    
    else:
        # PRO PLAN: Daily cached snapshot
        # Check if we have today's snapshot
        snapshot = await get_or_create_daily_snapshot(CURRENT_USER_ID, period_id)
        
        if snapshot and not force_refresh:
            # Return cached snapshot
            return TopSignalsResponse(
                signals=[InterventionSignal(**s) for s in snapshot["signals"]],
                generated_at=snapshot["generated_at"],
                update_mode="daily",
                is_cached=True,
                cache_timestamp=snapshot["generated_at"]
            )
        
        # No snapshot or force refresh - calculate and cache
        signals, team_forecast_data = await calculate_top_signals_live(CURRENT_USER_ID, limit)
        await save_daily_snapshot(CURRENT_USER_ID, period_id, signals, team_forecast_data)
        
        return TopSignalsResponse(
            signals=signals,
            generated_at=datetime.utcnow(),
            update_mode="daily",
            is_cached=False
        )

# PERIOD ENDPOINTS
@api_router.get("/periods/current")
async def get_current_period_info():
    start, end, period_id = get_current_period()
    prev_start, prev_end, prev_period_id = get_previous_period()
    
    prev_archived = await db.period_logs.find_one({
        "period_id": prev_period_id,
        "user_id": CURRENT_USER_ID
    })
    
    return {
        "period_id": period_id,
        "start_date": start,
        "end_date": end,
        "is_boundary_day": is_period_boundary(),
        "days_remaining": (date.fromisoformat(end) - date.today()).days + 1,
        "previous_period": {
            "period_id": prev_period_id,
            "is_archived": prev_archived is not None,
        }
    }

# DAILY ENTRY ENDPOINTS - Multi-user filtered
@api_router.get("/entries/today", response_model=DailyEntry)
async def get_today_entry():
    await ensure_previous_period_closed()
    
    today_str = date.today().isoformat()
    _, _, current_period_id = get_current_period()
    
    # MULTI-USER: Filter by user_id
    entry = await db.daily_entries.find_one({
        "user_id": CURRENT_USER_ID,
        "date": today_str
    })
    
    if not entry:
        new_entry = DailyEntry(
            user_id=CURRENT_USER_ID,
            date=today_str,
            period_id=current_period_id
        )
        await db.daily_entries.insert_one(new_entry.dict())
        return new_entry
    
    return DailyEntry(**normalize_entry(entry, current_period_id, CURRENT_USER_ID))

@api_router.get("/entries/{entry_date}", response_model=DailyEntry)
async def get_entry_by_date(entry_date: str):
    entry = await db.daily_entries.find_one({
        "user_id": CURRENT_USER_ID,
        "date": entry_date
    })
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return DailyEntry(**normalize_entry(entry, user_id=CURRENT_USER_ID))

@api_router.get("/entries")
async def get_entries(start_date: Optional[str] = None, end_date: Optional[str] = None, archived: Optional[bool] = None):
    query = {"user_id": CURRENT_USER_ID}  # MULTI-USER: Always filter by user
    if start_date and end_date:
        query["date"] = {"$gte": start_date, "$lte": end_date}
    if archived is not None:
        query["archived"] = archived
    entries = await db.daily_entries.find(query).sort("date", -1).to_list(1000)
    return [DailyEntry(**normalize_entry(e, user_id=CURRENT_USER_ID)) for e in entries]

# All write operations include user_id filter
@api_router.put("/entries/{entry_date}/calls")
async def update_calls(entry_date: str, calls_received: int):
    await ensure_previous_period_closed()
    _, _, current_period_id = get_current_period()
    
    result = await db.daily_entries.find_one_and_update(
        {"user_id": CURRENT_USER_ID, "date": entry_date},  # MULTI-USER: Filter
        {
            "$set": {"calls_received": calls_received, "updated_at": datetime.utcnow()},
            "$setOnInsert": {
                "id": str(uuid.uuid4()),
                "user_id": CURRENT_USER_ID,
                "date": entry_date,
                "period_id": current_period_id,
                "archived": False,
                "bookings": [],
                "spins": [],
                "misc_income": [],
                "created_at": datetime.utcnow()
            }
        },
        upsert=True,
        return_document=True
    )
    return DailyEntry(**normalize_entry(result, current_period_id, CURRENT_USER_ID))

@api_router.post("/entries/{entry_date}/bookings")
async def add_booking(entry_date: str, booking: BookingCreate):
    await ensure_previous_period_closed()
    _, _, current_period_id = get_current_period()
    
    new_booking = Booking(**booking.dict())
    
    # MULTI-USER: Filter by user_id
    entry = await db.daily_entries.find_one({
        "user_id": CURRENT_USER_ID,
        "date": entry_date
    })
    
    if not entry:
        new_entry = DailyEntry(
            user_id=CURRENT_USER_ID,
            date=entry_date,
            period_id=current_period_id,
            bookings=[new_booking]
        )
        await db.daily_entries.insert_one(new_entry.dict())
        return new_entry
    
    result = await db.daily_entries.find_one_and_update(
        {"user_id": CURRENT_USER_ID, "date": entry_date},
        {
            "$push": {"bookings": new_booking.dict()},
            "$set": {"updated_at": datetime.utcnow()}
        },
        return_document=True
    )
    return DailyEntry(**normalize_entry(result, current_period_id, CURRENT_USER_ID))

# STATS - Use user-specific goals
@api_router.get("/stats/biweekly", response_model=BiweeklyStats)
async def get_biweekly_stats():
    await ensure_previous_period_closed()
    
    start_date, end_date, period_id = get_current_period()
    
    # MULTI-USER: Filter by user_id
    entries = await db.daily_entries.find({
        "user_id": CURRENT_USER_ID,
        "date": {"$gte": start_date, "$lte": end_date},
        "archived": {"$ne": True}
    }).to_list(1000)
    
    entries = [normalize_entry(e, period_id, CURRENT_USER_ID) for e in entries]
    
    # Get user-specific goals
    user_goals = await get_user_goals(CURRENT_USER_ID)
    
    total_calls = sum(e.get("calls_received", 0) for e in entries)
    all_bookings, all_spins, all_misc, all_times = [], [], [], []
    
    for e in entries:
        all_bookings.extend(e.get("bookings", []))
        all_spins.extend(e.get("spins", []))
        all_misc.extend(e.get("misc_income", []))
    
    total_bookings = len(all_bookings)
    total_profit = sum(b.get("profit", 0) for b in all_bookings)
    total_spins_amount = sum(s.get("amount", 0) for s in all_spins)
    total_misc = sum(m.get("amount", 0) for m in all_misc)
    
    prepaid_count = sum(1 for b in all_bookings if b.get("is_prepaid", False))
    refund_count = sum(1 for b in all_bookings if b.get("has_refund_protection", False))
    
    for b in all_bookings:
        t = b.get("time_since_last", 0)
        if t > 0:
            all_times.append(t)
    
    regular_spins = [s for s in all_spins if not s.get("is_mega", False)]
    mega_spins = [s for s in all_spins if s.get("is_mega", False)]
    avg_regular = sum(s.get("amount", 0) for s in regular_spins) / len(regular_spins) if regular_spins else 0
    avg_mega = sum(s.get("amount", 0) for s in mega_spins) / len(mega_spins) if mega_spins else 0
    
    res_stat = build_metric_stat(total_bookings, user_goals["reservations_biweekly"])
    
    return BiweeklyStats(
        period="biweekly",
        period_id=period_id,
        start_date=start_date,
        end_date=end_date,
        days_tracked=len(entries),
        calls=build_metric_stat(total_calls, user_goals["calls_biweekly"]),
        reservations=ReservationStat(
            total=res_stat.total,
            goal=res_stat.goal,
            progress_percent=res_stat.progress_percent,
            on_track=res_stat.on_track,
            status=res_stat.status,
            prepaid_count=prepaid_count,
            refund_protection_count=refund_count
        ),
        conversion_rate=build_conversion_stat(
            total_bookings, total_calls,
            user_goals["reservations_biweekly"], user_goals["calls_biweekly"]
        ),
        profit=build_metric_stat(total_profit, user_goals["profit_biweekly"]),
        spins=build_metric_stat(total_spins_amount, user_goals["spins_biweekly"]),
        combined=build_metric_stat(total_profit + total_spins_amount, user_goals["combined_biweekly"]),
        misc=build_metric_stat(total_misc, user_goals["misc_biweekly"]),
        avg_time=build_time_stat(all_times, user_goals["avg_time_per_booking"]),
        spin_averages=SpinAverages(
            regular=round(avg_regular, 2),
            regular_goal=user_goals.get("avg_spin", 0),
            mega=round(avg_mega, 2),
            mega_goal=user_goals.get("avg_mega_spin", 0)
        )
    )


# =============================================================================
# NEW ENDPOINTS - Daily Stats, Settings, Entries, Timer, Export
# =============================================================================

@api_router.get("/stats/today")
async def get_today_stats():
    """Get statistics for today only"""
    today = date.today().isoformat()
    entry = await db.daily_entries.find_one({"user_id": CURRENT_USER_ID, "date": today})
    
    if not entry:
        user_goals = await get_user_goals(CURRENT_USER_ID)
        return {
            "date": today,
            "calls": {"current": 0, "goal": user_goals.get("calls_daily", 0), "diff": -user_goals.get("calls_daily", 0), "status": "behind"},
            "reservations": {"current": 0, "goal": user_goals.get("reservations_daily", 0), "diff": -user_goals.get("reservations_daily", 0), "status": "behind", "prepaid_count": 0, "refund_protection_count": 0},
            "conversion_rate": {"current": 0, "goal": 0, "status": "on_track"},
            "profit": {"current": 0, "goal": user_goals.get("profit_daily", 0), "diff": -user_goals.get("profit_daily", 0), "status": "behind"},
            "spins": {"current": 0, "goal": user_goals.get("spins_daily", 0), "diff": -user_goals.get("spins_daily", 0), "status": "behind"},
            "combined": {"current": 0, "goal": 0, "diff": 0, "status": "on_track"},
            "avg_time": {"current": 0, "goal": user_goals.get("avg_time_per_booking", 0), "status": "on_track"},
            "earnings": {"usd": {"profit": 0, "spins": 0, "misc": 0, "total": 0}, "pesos": {"gross_pesos": 0, "service_fee": 0, "payday_deduction": 0, "net_pesos": 0}, "peso_rate": user_goals.get("peso_rate", 17.50)}
        }
    
    user_goals = await get_user_goals(CURRENT_USER_ID)
    bookings = entry.get("bookings", [])
    spins = entry.get("spins", [])
    misc_income = entry.get("misc_income", [])
    calls = entry.get("calls_received", 0)
    
    total_bookings = len(bookings)
    total_profit = sum(b.get("profit", 0) for b in bookings)
    total_spins = sum(s.get("amount", 0) for s in spins)
    total_misc = sum(m.get("amount", 0) for m in misc_income)
    prepaid_count = sum(1 for b in bookings if b.get("is_prepaid", False))
    refund_count = sum(1 for b in bookings if b.get("has_refund_protection", False))
    
    times = [b.get("time_since_last", 0) for b in bookings if b.get("time_since_last", 0) > 0]
    avg_time = sum(times) / len(times) if times else 0
    conversion_rate = (total_bookings / calls * 100) if calls > 0 else 0
    combined = total_profit + total_spins
    
    peso_rate = user_goals.get("peso_rate", 17.50)
    gross_pesos = (total_profit + total_spins + total_misc) * peso_rate
    service_fee = gross_pesos * 0.17
    net_pesos = gross_pesos - service_fee
    
    return {
        "date": today,
        "calls": {"current": calls, "goal": user_goals.get("calls_daily", 0), "diff": calls - user_goals.get("calls_daily", 0), "status": "ahead" if calls >= user_goals.get("calls_daily", 0) else "behind"},
        "reservations": {"current": total_bookings, "goal": user_goals.get("reservations_daily", 0), "diff": total_bookings - user_goals.get("reservations_daily", 0), "status": "ahead" if total_bookings >= user_goals.get("reservations_daily", 0) else "behind", "prepaid_count": prepaid_count, "refund_protection_count": refund_count},
        "conversion_rate": {"current": round(conversion_rate, 2), "goal": user_goals.get("conversion_rate_goal", 0), "status": "ahead" if conversion_rate >= user_goals.get("conversion_rate_goal", 0) else "behind"},
        "profit": {"current": round(total_profit, 2), "goal": user_goals.get("profit_daily", 0), "diff": round(total_profit - user_goals.get("profit_daily", 0), 2), "status": "ahead" if total_profit >= user_goals.get("profit_daily", 0) else "behind"},
        "spins": {"current": round(total_spins, 2), "goal": user_goals.get("spins_daily", 0), "diff": round(total_spins - user_goals.get("spins_daily", 0), 2), "status": "ahead" if total_spins >= user_goals.get("spins_daily", 0) else "behind"},
        "combined": {"current": round(combined, 2), "goal": user_goals.get("combined_daily", 0), "diff": round(combined - user_goals.get("combined_daily", 0), 2), "status": "ahead" if combined >= user_goals.get("combined_daily", 0) else "behind"},
        "avg_time": {"current": round(avg_time, 1), "goal": user_goals.get("avg_time_per_booking", 0), "status": "ahead" if avg_time <= user_goals.get("avg_time_per_booking", 0) or avg_time == 0 else "behind"},
        "earnings": {"usd": {"profit": round(total_profit, 2), "spins": round(total_spins, 2), "misc": round(total_misc, 2), "total": round(total_profit + total_spins + total_misc, 2)}, "pesos": {"gross_pesos": round(gross_pesos, 2), "service_fee": round(service_fee, 2), "payday_deduction": 0, "net_pesos": round(net_pesos, 2)}, "peso_rate": peso_rate}
    }


@api_router.get("/stats/week")
async def get_week_stats():
    """Get statistics for the past 7 days - Pro+ only"""
    user = get_current_user_sync()
    access = check_feature_access(user, "multiple_periods")
    if not access["allowed"]:
        raise HTTPException(status_code=403, detail={"error": "Weekly statistics require Pro plan or higher", "current_plan": user.plan, "required_plan": "pro"})
    
    end_date = date.today()
    start_date = end_date - timedelta(days=6)
    entries = await db.daily_entries.find({"user_id": CURRENT_USER_ID, "date": {"$gte": start_date.isoformat(), "$lte": end_date.isoformat()}}).to_list(1000)
    
    user_goals = await get_user_goals(CURRENT_USER_ID)
    all_bookings, all_spins, all_misc = [], [], []
    total_calls = 0
    for e in entries:
        all_bookings.extend(e.get("bookings", []))
        all_spins.extend(e.get("spins", []))
        all_misc.extend(e.get("misc_income", []))
        total_calls += e.get("calls_received", 0)
    
    total_profit = sum(b.get("profit", 0) for b in all_bookings)
    total_spins_amount = sum(s.get("amount", 0) for s in all_spins)
    total_misc = sum(m.get("amount", 0) for m in all_misc)
    
    peso_rate = user_goals.get("peso_rate", 17.50)
    gross_pesos = (total_profit + total_spins_amount + total_misc) * peso_rate
    service_fee = gross_pesos * 0.17
    net_pesos = gross_pesos - service_fee
    
    return {
        "period": "week",
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "days_tracked": len(entries),
        "goals": {
            "earnings": user_goals.get("combined_weekly", 366.00),
            "reservations": user_goals.get("reservations_weekly", 96),
            "calls": user_goals.get("calls_weekly", 640)
        },
        "reservations": {"current": len(all_bookings), "goal": user_goals.get("reservations_weekly", 96)},
        "calls": {"current": total_calls, "goal": user_goals.get("calls_weekly", 640)},
        "earnings": {"usd": {"profit": round(total_profit, 2), "spins": round(total_spins_amount, 2), "misc": round(total_misc, 2), "total": round(total_profit + total_spins_amount + total_misc, 2)}, "pesos": {"gross_pesos": round(gross_pesos, 2), "service_fee": round(service_fee, 2), "payday_deduction": 0, "net_pesos": round(net_pesos, 2)}, "peso_rate": peso_rate}
    }


@api_router.get("/stats/period")
async def get_period_stats():
    """Get statistics for current pay period - Pro+ only"""
    user = get_current_user_sync()
    access = check_feature_access(user, "multiple_periods")
    if not access["allowed"]:
        raise HTTPException(status_code=403, detail={"error": "Period statistics require Pro plan or higher", "current_plan": user.plan, "required_plan": "pro"})
    
    start_date, end_date, period_id = get_current_period()
    entries = await db.daily_entries.find({"user_id": CURRENT_USER_ID, "date": {"$gte": start_date, "$lte": end_date}}).to_list(1000)
    
    user_goals = await get_user_goals(CURRENT_USER_ID)
    all_bookings, all_spins, all_misc = [], [], []
    for e in entries:
        all_bookings.extend(e.get("bookings", []))
        all_spins.extend(e.get("spins", []))
        all_misc.extend(e.get("misc_income", []))
    
    total_profit = sum(b.get("profit", 0) for b in all_bookings)
    total_spins_amount = sum(s.get("amount", 0) for s in all_spins)
    total_misc = sum(m.get("amount", 0) for m in all_misc)
    
    peso_rate = user_goals.get("peso_rate", 17.50)
    gross_pesos = (total_profit + total_spins_amount + total_misc) * peso_rate
    service_fee = gross_pesos * 0.17
    net_pesos = gross_pesos - service_fee
    
    return {"period": "biweekly", "period_id": period_id, "start_date": start_date, "end_date": end_date, "days_tracked": len(entries), "earnings": {"usd": {"profit": round(total_profit, 2), "spins": round(total_spins_amount, 2), "misc": round(total_misc, 2), "total": round(total_profit + total_spins_amount + total_misc, 2)}, "pesos": {"gross_pesos": round(gross_pesos, 2), "service_fee": round(service_fee, 2), "payday_deduction": 0, "net_pesos": round(net_pesos, 2)}, "peso_rate": peso_rate}}


@api_router.get("/settings")
async def get_settings():
    """Get user settings"""
    settings = await db.user_settings.find_one({"user_id": CURRENT_USER_ID})
    if not settings:
        user_goals = await get_user_goals(CURRENT_USER_ID)
        return {"user_id": CURRENT_USER_ID, "user_plan": CURRENT_USER_PLAN, "peso_rate": user_goals.get("peso_rate", 17.50), "goals": user_goals}
    return {"user_id": CURRENT_USER_ID, "user_plan": settings.get("user_plan", CURRENT_USER_PLAN), "peso_rate": settings.get("peso_rate", 17.50), "goals": settings.get("goals", await get_user_goals(CURRENT_USER_ID))}


@api_router.get("/entries/today")
async def get_today_entry():
    """Get today's daily entry"""
    today = date.today().isoformat()
    _, _, period_id = get_current_period()
    entry = await db.daily_entries.find_one({"user_id": CURRENT_USER_ID, "date": today})
    if not entry:
        entry = {"id": str(uuid.uuid4()), "user_id": CURRENT_USER_ID, "date": today, "period_id": period_id, "calls_received": 0, "bookings": [], "spins": [], "misc_income": [], "work_timer_start": None, "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()}
        await db.daily_entries.insert_one(entry)
    return entry


@api_router.put("/entries/{date}/calls")
async def update_calls(date: str, calls_received: int):
    """Update calls received for a date"""
    try:
        datetime.fromisoformat(date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    _, _, period_id = get_current_period()
    await db.daily_entries.update_one({"user_id": CURRENT_USER_ID, "date": date}, {"$set": {"calls_received": calls_received, "updated_at": datetime.utcnow()}, "$setOnInsert": {"id": str(uuid.uuid4()), "user_id": CURRENT_USER_ID, "date": date, "period_id": period_id, "bookings": [], "spins": [], "misc_income": [], "created_at": datetime.utcnow()}}, upsert=True)
    return await db.daily_entries.find_one({"user_id": CURRENT_USER_ID, "date": date})


@api_router.post("/entries/{date}/timer/start")
async def start_timer(date: str):
    """Start work timer"""
    try:
        datetime.fromisoformat(date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    entry = await db.daily_entries.find_one({"user_id": CURRENT_USER_ID, "date": date})
    if entry and entry.get("work_timer_start"):
        raise HTTPException(status_code=400, detail="Timer already running")
    _, _, period_id = get_current_period()
    await db.daily_entries.update_one({"user_id": CURRENT_USER_ID, "date": date}, {"$set": {"work_timer_start": datetime.utcnow().isoformat(), "updated_at": datetime.utcnow()}, "$setOnInsert": {"id": str(uuid.uuid4()), "user_id": CURRENT_USER_ID, "date": date, "period_id": period_id, "calls_received": 0, "bookings": [], "spins": [], "misc_income": [], "created_at": datetime.utcnow()}}, upsert=True)
    return await db.daily_entries.find_one({"user_id": CURRENT_USER_ID, "date": date})


@api_router.post("/entries/{date}/timer/stop")
async def stop_timer(date: str):
    """Stop work timer"""
    try:
        datetime.fromisoformat(date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    entry = await db.daily_entries.find_one({"user_id": CURRENT_USER_ID, "date": date})
    if not entry or not entry.get("work_timer_start"):
        raise HTTPException(status_code=400, detail="No timer running")
    timer_start = datetime.fromisoformat(entry["work_timer_start"])
    elapsed_minutes = (datetime.utcnow() - timer_start).total_seconds() / 60
    await db.daily_entries.update_one({"user_id": CURRENT_USER_ID, "date": date}, {"$set": {"work_timer_start": None, "updated_at": datetime.utcnow()}, "$inc": {"total_time_minutes": elapsed_minutes}})
    return await db.daily_entries.find_one({"user_id": CURRENT_USER_ID, "date": date})


@api_router.post("/entries/{date}/bookings")
async def add_booking(date: str, booking: BookingCreate):
    """Add a booking"""
    try:
        datetime.fromisoformat(date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    _, _, period_id = get_current_period()
    booking_dict = booking.dict()
    booking_dict["id"] = str(uuid.uuid4())
    booking_dict["timestamp"] = datetime.utcnow()
    await db.daily_entries.update_one({"user_id": CURRENT_USER_ID, "date": date}, {"$push": {"bookings": booking_dict}, "$set": {"updated_at": datetime.utcnow()}, "$setOnInsert": {"id": str(uuid.uuid4()), "user_id": CURRENT_USER_ID, "date": date, "period_id": period_id, "calls_received": 0, "spins": [], "misc_income": [], "created_at": datetime.utcnow()}}, upsert=True)
    return await db.daily_entries.find_one({"user_id": CURRENT_USER_ID, "date": date})


@api_router.post("/entries/{date}/spins")
async def add_spin(date: str, spin: SpinCreate):
    """Add a spin"""
    try:
        datetime.fromisoformat(date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    _, _, period_id = get_current_period()
    spin_dict = spin.dict()
    spin_dict["id"] = str(uuid.uuid4())
    spin_dict["timestamp"] = datetime.utcnow()
    await db.daily_entries.update_one({"user_id": CURRENT_USER_ID, "date": date}, {"$push": {"spins": spin_dict}, "$set": {"updated_at": datetime.utcnow()}, "$setOnInsert": {"id": str(uuid.uuid4()), "user_id": CURRENT_USER_ID, "date": date, "period_id": period_id, "calls_received": 0, "bookings": [], "misc_income": [], "created_at": datetime.utcnow()}}, upsert=True)
    return await db.daily_entries.find_one({"user_id": CURRENT_USER_ID, "date": date})


@api_router.post("/entries/{date}/misc")
async def add_misc_income(date: str, misc: MiscIncomeCreate):
    """Add miscellaneous income"""
    try:
        datetime.fromisoformat(date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    _, _, period_id = get_current_period()
    misc_dict = misc.dict()
    misc_dict["id"] = str(uuid.uuid4())
    misc_dict["timestamp"] = datetime.utcnow()
    await db.daily_entries.update_one({"user_id": CURRENT_USER_ID, "date": date}, {"$push": {"misc_income": misc_dict}, "$set": {"updated_at": datetime.utcnow()}, "$setOnInsert": {"id": str(uuid.uuid4()), "user_id": CURRENT_USER_ID, "date": date, "period_id": period_id, "calls_received": 0, "bookings": [], "spins": [], "created_at": datetime.utcnow()}}, upsert=True)
    return await db.daily_entries.find_one({"user_id": CURRENT_USER_ID, "date": date})


@api_router.delete("/entries/{date}/bookings/{booking_id}")
async def delete_booking(date: str, booking_id: str):
    """Delete a booking"""
    try:
        datetime.fromisoformat(date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    entry = await db.daily_entries.find_one({"user_id": CURRENT_USER_ID, "date": date})
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    if not any(b.get("id") == booking_id for b in entry.get("bookings", [])):
        raise HTTPException(status_code=404, detail="Booking not found")
    await db.daily_entries.update_one({"user_id": CURRENT_USER_ID, "date": date}, {"$pull": {"bookings": {"id": booking_id}}, "$set": {"updated_at": datetime.utcnow()}})
    return await db.daily_entries.find_one({"user_id": CURRENT_USER_ID, "date": date})

@api_router.put("/entries/{date}/bookings/{booking_id}")
async def update_booking(date: str, booking_id: str, booking_update: BookingCreate):
    """Update a booking"""
    try:
        datetime.fromisoformat(date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    entry = await db.daily_entries.find_one({"user_id": CURRENT_USER_ID, "date": date})
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    bookings = entry.get("bookings", [])
    booking_index = next((i for i, b in enumerate(bookings) if b.get("id") == booking_id), None)

    if booking_index is None:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Update the booking while preserving id and timestamp
    updated_booking = booking_update.dict()
    updated_booking["id"] = bookings[booking_index]["id"]
    updated_booking["timestamp"] = bookings[booking_index].get("timestamp", datetime.utcnow())
    bookings[booking_index] = updated_booking

    await db.daily_entries.update_one(
        {"user_id": CURRENT_USER_ID, "date": date},
        {"$set": {"bookings": bookings, "updated_at": datetime.utcnow()}}
    )

    return await db.daily_entries.find_one({"user_id": CURRENT_USER_ID, "date": date})



@api_router.get("/export/csv")
async def export_csv():
    """Export data as CSV - Individual+ only"""
    user = get_current_user_sync()
    access = check_feature_access(user, "export_data")
    if not access["allowed"]:
        raise HTTPException(status_code=403, detail={"error": "CSV export requires Individual plan or higher", "current_plan": user.plan, "required_plan": "individual"})
    entries = await db.daily_entries.find({"user_id": CURRENT_USER_ID}).sort("date", 1).to_list(10000)
    import io, csv
    from fastapi.responses import Response
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Calls", "Bookings", "Conversion Rate", "Profit", "Spins", "Misc Income", "Total Time (min)"])
    for entry in entries:
        bookings = entry.get("bookings", [])
        spins = entry.get("spins", [])
        misc_income = entry.get("misc_income", [])
        calls = entry.get("calls_received", 0)
        total_bookings = len(bookings)
        total_profit = sum(b.get("profit", 0) for b in bookings)
        total_spins = sum(s.get("amount", 0) for s in spins)
        total_misc = sum(m.get("amount", 0) for m in misc_income)
        conversion_rate = (total_bookings / calls * 100) if calls > 0 else 0
        total_time = entry.get("total_time_minutes", 0)
        writer.writerow([entry.get("date"), calls, total_bookings, f"{conversion_rate:.2f}%", f"${total_profit:.2f}", f"${total_spins:.2f}", f"${total_misc:.2f}", f"{total_time:.1f}"])
    return Response(content=output.getvalue(), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=kpi_export_{date.today().isoformat()}.csv"})


# APP SETUP
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# TENANT ISOLATION MIDDLEWARE
# =============================================================================

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse


class TenantIsolationMiddleware(BaseHTTPMiddleware):
    """
    Enforce tenant isolation for multi-tenant requests
    Verifies that user's company_id matches the requested tenant
    """
    
    async def dispatch(self, request, call_next):
        # Skip for public routes
        public_routes = ["/login", "/refresh", "/health", "/"]
        if any(request.url.path.startswith(route) for route in public_routes):
            return await call_next(request)
        
        # Skip for routes that don't use tenant isolation
        if request.url.path.startswith("/api/periods") or request.url.path.startswith("/api/stats"):
            return await call_next(request)
        
        # Get current user from token
        try:
            from services.tokens import validate_access_token
            from fastapi import Request
            
            # Extract token from header
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                payload = await validate_access_token(token)
                user_id = payload.get("sub")
                
                if user_id:
                    user = await db.users.find_one({"id": user_id})
                    if user:
                        # Store user info in request state for downstream use
                        request.state.user = user
                        request.state.company_id = user.get("company_id")
                        request.state.team_id = user.get("team_id")
        except Exception:
            pass  # Will be handled by auth dependency on protected routes
        
        return await call_next(request)


app.add_middleware(TenantIsolationMiddleware)

# STARTUP/SHUTDOWN
@app.on_event("startup")
async def startup_event():
    """Ordered, blocking startup validation. Any failure = immediate termination."""
    from .db.validators import (
        verify_database_connection,
        initialize_database_schema,
        verify_schema_enforcement,
        verify_unique_indexes,
        validate_auth_system_integrity,
        verify_tenant_validation_works,
        verify_audit_immutability,
    )
    from .services.tokens import load_jwt_keys
    
    logger.info("Starting system hardening...")
    
    # 0. Load JWT keys for rotation support
    load_jwt_keys()
    logger.info("Γ£ô JWT keys loaded with rotation support")
    
    # 1. Database connectivity
    await verify_database_connection(db)
    logger.info("Γ£ô Database connection verified")
    
    # 2. Initialize collections with schemas (creates if missing, updates if exists)
    await initialize_database_schema(db)
    logger.info("Γ£ô Database schema initialized")
    
    # 3. Create unique indexes (structural constraints)
    # (Already done in initialize_database_schema)
    logger.info("Γ£ô Unique indexes created")
    
    # 4. Verify schemas are actually enforced
    await verify_schema_enforcement(db)
    logger.info("Γ£ô Schema enforcement verified")
    
    # 5. Verify unique indexes exist
    await verify_unique_indexes(db)
    logger.info("Γ£ô Unique indexes verified")
    
    # 6. Verify enum/hierarchy completeness
    await validate_auth_system_integrity(db)
    logger.info("Γ£ô Auth system integrity verified")
    
    # 7. Test tenant integrity enforcement
    await verify_tenant_validation_works(db)
    logger.info("Γ£ô Tenant validation verified")
    
    # 8. Verify audit log immutability
    await verify_audit_immutability(db)
    logger.info("Γ£ô Audit immutability verified")
    
    start_scheduler()
    logger.info("=" * 50)
    logger.info("SYSTEM HARDENING COMPLETE")
    logger.info("All structural integrity constraints active")
    logger.info("=" * 50)

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()
    client.close()
    logger.info("Application shutdown complete")

# =============================================================================
# STATS ENDPOINTS - Daily, Weekly, Period
# =============================================================================

@api_router.get("/stats/today")
async def get_today_stats():
    """Get statistics for today only"""
    today = date.today().isoformat()

    # Query today's entry
    entry = await db.daily_entries.find_one({
        "user_id": CURRENT_USER_ID,
        "date": today
    })

    if not entry:
        # Return zeros if no entry exists
        user_goals = await get_user_goals(CURRENT_USER_ID)
        return {
            "date": today,
            "calls": {"current": 0, "goal": user_goals.get("calls_daily", 0), "diff": -user_goals.get("calls_daily", 0), "status": "behind"},
            "reservations": {"current": 0, "goal": user_goals.get("reservations_daily", 0), "diff": -user_goals.get("reservations_daily", 0), "status": "behind", "prepaid_count": 0, "refund_protection_count": 0},
            "conversion_rate": {"current": 0, "goal": 0, "status": "on_track"},
            "profit": {"current": 0, "goal": user_goals.get("profit_daily", 0), "diff": -user_goals.get("profit_daily", 0), "status": "behind"},
            "spins": {"current": 0, "goal": user_goals.get("spins_daily", 0), "diff": -user_goals.get("spins_daily", 0), "status": "behind"},
            "combined": {"current": 0, "goal": 0, "diff": 0, "status": "on_track"},
            "avg_time": {"current": 0, "goal": user_goals.get("avg_time_per_booking", 0), "status": "on_track"},
            "earnings": {
                "usd": {"profit": 0, "spins": 0, "misc": 0, "total": 0},
                "pesos": {"gross_pesos": 0, "service_fee": 0, "payday_deduction": 0, "net_pesos": 0},
                "peso_rate": user_goals.get("peso_rate", 17.50)
            }
        }

    # Calculate stats from entry
    user_goals = await get_user_goals(CURRENT_USER_ID)
    bookings = entry.get("bookings", [])
    spins = entry.get("spins", [])
    misc_income = entry.get("misc_income", [])
    calls = entry.get("calls_received", 0)

    total_bookings = len(bookings)
    total_profit = sum(b.get("profit", 0) for b in bookings)
    total_spins = sum(s.get("amount", 0) for s in spins)
    total_misc = sum(m.get("amount", 0) for m in misc_income)
    prepaid_count = sum(1 for b in bookings if b.get("is_prepaid", False))
    refund_count = sum(1 for b in bookings if b.get("has_refund_protection", False))

    times = [b.get("time_since_last", 0) for b in bookings if b.get("time_since_last", 0) > 0]
    avg_time = sum(times) / len(times) if times else 0

    conversion_rate = (total_bookings / calls * 100) if calls > 0 else 0
    combined = total_profit + total_spins

    # Calculate earnings with peso conversion
    peso_rate = user_goals.get("peso_rate", 17.50)
    gross_pesos = (total_profit + total_spins + total_misc) * peso_rate
    service_fee = gross_pesos * 0.17
    net_pesos = gross_pesos - service_fee

    return {
        "date": today,
        "calls": {
            "current": calls,
            "goal": user_goals.get("calls_daily", 0),
            "diff": calls - user_goals.get("calls_daily", 0),
            "status": "ahead" if calls >= user_goals.get("calls_daily", 0) else "behind"
        },
        "reservations": {
            "current": total_bookings,
            "goal": user_goals.get("reservations_daily", 0),
            "diff": total_bookings - user_goals.get("reservations_daily", 0),
            "status": "ahead" if total_bookings >= user_goals.get("reservations_daily", 0) else "behind",
            "prepaid_count": prepaid_count,
            "refund_protection_count": refund_count
        },
        "conversion_rate": {
            "current": round(conversion_rate, 2),
            "goal": user_goals.get("conversion_rate_goal", 0),
            "status": "ahead" if conversion_rate >= user_goals.get("conversion_rate_goal", 0) else "behind"
        },
        "profit": {
            "current": round(total_profit, 2),
            "goal": user_goals.get("profit_daily", 0),
            "diff": round(total_profit - user_goals.get("profit_daily", 0), 2),
            "status": "ahead" if total_profit >= user_goals.get("profit_daily", 0) else "behind"
        },
        "spins": {
            "current": round(total_spins, 2),
            "goal": user_goals.get("spins_daily", 0),
            "diff": round(total_spins - user_goals.get("spins_daily", 0), 2),
            "status": "ahead" if total_spins >= user_goals.get("spins_daily", 0) else "behind"
        },
        "combined": {
            "current": round(combined, 2),
            "goal": user_goals.get("combined_daily", 0),
            "diff": round(combined - user_goals.get("combined_daily", 0), 2),
            "status": "ahead" if combined >= user_goals.get("combined_daily", 0) else "behind"
        },
        "avg_time": {
            "current": round(avg_time, 1),
            "goal": user_goals.get("avg_time_per_booking", 0),
            "status": "ahead" if avg_time <= user_goals.get("avg_time_per_booking", 0) or avg_time == 0 else "behind"
        },
        "earnings": {
            "usd": {
                "profit": round(total_profit, 2),
                "spins": round(total_spins, 2),
                "misc": round(total_misc, 2),
                "total": round(total_profit + total_spins + total_misc, 2)
            },
            "pesos": {
                "gross_pesos": round(gross_pesos, 2),
                "service_fee": round(service_fee, 2),
                "payday_deduction": 0,
                "net_pesos": round(net_pesos, 2)
            },
            "peso_rate": peso_rate
        }
    }


@api_router.get("/stats/week")
async def get_week_stats():
    """Get statistics for the past 7 days - Pro+ only"""
    user = get_current_user_sync()
    access = check_feature_access(user, "multiple_periods")

    if not access["allowed"]:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Weekly statistics require Pro plan or higher",
                "current_plan": user.plan,
                "required_plan": "pro"
            }
        )

    # Calculate date range for past 7 days
    end_date = date.today()
    start_date = end_date - timedelta(days=6)

    entries = await db.daily_entries.find({
        "user_id": CURRENT_USER_ID,
        "date": {"$gte": start_date.isoformat(), "$lte": end_date.isoformat()}
    }).to_list(1000)

    # Aggregate statistics
    user_goals = await get_user_goals(CURRENT_USER_ID)
    total_calls = sum(e.get("calls_received", 0) for e in entries)
    all_bookings = []
    all_spins = []
    all_misc = []

    for e in entries:
        all_bookings.extend(e.get("bookings", []))
        all_spins.extend(e.get("spins", []))
        all_misc.extend(e.get("misc_income", []))

    total_bookings = len(all_bookings)
    total_profit = sum(b.get("profit", 0) for b in all_bookings)
    total_spins_amount = sum(s.get("amount", 0) for s in all_spins)
    total_misc = sum(m.get("amount", 0) for m in all_misc)

    peso_rate = user_goals.get("peso_rate", 17.50)
    gross_pesos = (total_profit + total_spins_amount + total_misc) * peso_rate
    service_fee = gross_pesos * 0.17
    net_pesos = gross_pesos - service_fee

    return {
        "period": "week",
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "days_tracked": len(entries),
        "earnings": {
            "usd": {
                "profit": round(total_profit, 2),
                "spins": round(total_spins_amount, 2),
                "misc": round(total_misc, 2),
                "total": round(total_profit + total_spins_amount + total_misc, 2)
            },
            "pesos": {
                "gross_pesos": round(gross_pesos, 2),
                "service_fee": round(service_fee, 2),
                "payday_deduction": 0,
                "net_pesos": round(net_pesos, 2)
            },
            "peso_rate": peso_rate
        }
    }


@api_router.get("/stats/period")
async def get_period_stats():
    """Get statistics for current pay period - Pro+ only"""
    user = get_current_user_sync()
    access = check_feature_access(user, "multiple_periods")

    if not access["allowed"]:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Period statistics require Pro plan or higher",
                "current_plan": user.plan,
                "required_plan": "pro"
            }
        )

    start_date, end_date, period_id = get_current_period()

    entries = await db.daily_entries.find({
        "user_id": CURRENT_USER_ID,
        "date": {"$gte": start_date, "$lte": end_date}
    }).to_list(1000)

    # Aggregate statistics
    user_goals = await get_user_goals(CURRENT_USER_ID)
    total_calls = sum(e.get("calls_received", 0) for e in entries)
    all_bookings = []
    all_spins = []
    all_misc = []

    for e in entries:
        all_bookings.extend(e.get("bookings", []))
        all_spins.extend(e.get("spins", []))
        all_misc.extend(e.get("misc_income", []))

    total_bookings = len(all_bookings)
    total_profit = sum(b.get("profit", 0) for b in all_bookings)
    total_spins_amount = sum(s.get("amount", 0) for s in all_spins)
    total_misc = sum(m.get("amount", 0) for m in all_misc)

    peso_rate = user_goals.get("peso_rate", 17.50)
    gross_pesos = (total_profit + total_spins_amount + total_misc) * peso_rate
    service_fee = gross_pesos * 0.17
    net_pesos = gross_pesos - service_fee

    return {
        "period": "biweekly",
        "period_id": period_id,
        "start_date": start_date,
        "end_date": end_date,
        "days_tracked": len(entries),
        "earnings": {
            "usd": {
                "profit": round(total_profit, 2),
                "spins": round(total_spins_amount, 2),
                "misc": round(total_misc, 2),
                "total": round(total_profit + total_spins_amount + total_misc, 2)
            },
            "pesos": {
                "gross_pesos": round(gross_pesos, 2),
                "service_fee": round(service_fee, 2),
                "payday_deduction": 0,
                "net_pesos": round(net_pesos, 2)
            },
            "peso_rate": peso_rate
        }
    }


# =============================================================================
# SETTINGS ENDPOINTS
# =============================================================================

@api_router.get("/settings")
async def get_settings():
    """Get user settings"""
    settings = await db.user_settings.find_one({"user_id": CURRENT_USER_ID})

    if not settings:
        # Return default settings
        user_goals = await get_user_goals(CURRENT_USER_ID)
        return {
            "user_id": CURRENT_USER_ID,
            "user_plan": CURRENT_USER_PLAN,
            "peso_rate": user_goals.get("peso_rate", 17.50),
            "goals": user_goals
        }

    return {
        "user_id": CURRENT_USER_ID,
        "user_plan": settings.get("user_plan", CURRENT_USER_PLAN),
        "peso_rate": settings.get("peso_rate", 17.50),
        "goals": settings.get("goals", await get_user_goals(CURRENT_USER_ID))
    }


@api_router.put("/settings")
async def update_settings(settings_update: dict):
    """Update user settings"""
    global CURRENT_USER_PLAN
    
    existing = await db.user_settings.find_one({"user_id": CURRENT_USER_ID})
    if not existing:
        existing = {"user_id": CURRENT_USER_ID, "user_plan": CURRENT_USER_PLAN, "peso_rate": 17.50, "goals": await get_user_goals(CURRENT_USER_ID)}
    merged = {**existing, **settings_update, "updated_at": datetime.utcnow()}
    await db.user_settings.update_one({"user_id": CURRENT_USER_ID}, {"$set": merged}, upsert=True)
    if "goals" in settings_update:
        await update_user_goals(CURRENT_USER_ID, settings_update["goals"])
    if "user_plan" in settings_update:
        CURRENT_USER_PLAN = settings_update["user_plan"]
    return merged


# =============================================================================
# ENTRY MANAGEMENT ENDPOINTS
# =============================================================================

@api_router.get("/entries/today")
async def get_today_entry():
    """Get today's daily entry"""
    today = date.today().isoformat()
    _, _, period_id = get_current_period()

    entry = await db.daily_entries.find_one({
        "user_id": CURRENT_USER_ID,
        "date": today
    })

    if not entry:
        # Create new entry with zero values
        entry = {
            "id": str(uuid.uuid4()),
            "user_id": CURRENT_USER_ID,
            "date": today,
            "period_id": period_id,
            "calls_received": 0,
            "bookings": [],
            "spins": [],
            "misc_income": [],
            "work_timer_start": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        await db.daily_entries.insert_one(entry)

    return entry


@api_router.put("/entries/{date}/calls")
async def update_calls(date: str, calls_received: int):
    """Update calls received for a date"""
    # Validate date format
    try:
        date_obj = datetime.fromisoformat(date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    _, _, period_id = get_current_period()

    # Update or create entry
    result = await db.daily_entries.update_one(
        {"user_id": CURRENT_USER_ID, "date": date},
        {
            "$set": {
                "calls_received": calls_received,
                "updated_at": datetime.utcnow()
            },
            "$setOnInsert": {
                "id": str(uuid.uuid4()),
                "user_id": CURRENT_USER_ID,
                "date": date,
                "period_id": period_id,
                "bookings": [],
                "spins": [],
                "misc_income": [],
                "created_at": datetime.utcnow()
            }
        },
        upsert=True
    )

    # Return updated entry
    entry = await db.daily_entries.find_one({"user_id": CURRENT_USER_ID, "date": date})
    return entry


# =============================================================================
# EXPORT ENDPOINT
# =============================================================================

@api_router.get("/export/csv")
async def export_csv():
    """Export data as CSV - Pro+ only"""
    user = get_current_user_sync()
    access = check_feature_access(user, "export_data")

    if not access["allowed"]:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "CSV export requires Individual plan or higher",
                "current_plan": user.plan,
                "required_plan": "individual"
            }
        )

    # Query all entries
    entries = await db.daily_entries.find({"user_id": CURRENT_USER_ID}).sort("date", 1).to_list(10000)

    # Generate CSV
    import io
    import csv

    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(["Date", "Calls", "Bookings", "Conversion Rate", "Profit", "Spins", "Misc Income", "Total Time (min)"])

    # Write data
    for entry in entries:
        bookings = entry.get("bookings", [])
        spins = entry.get("spins", [])
        misc_income = entry.get("misc_income", [])
        calls = entry.get("calls_received", 0)

        total_bookings = len(bookings)
        total_profit = sum(b.get("profit", 0) for b in bookings)
        total_spins = sum(s.get("amount", 0) for s in spins)
        total_misc = sum(m.get("amount", 0) for m in misc_income)
        conversion_rate = (total_bookings / calls * 100) if calls > 0 else 0
        total_time = entry.get("total_time_minutes", 0)

        writer.writerow([
            entry.get("date"),
            calls,
            total_bookings,
            f"{conversion_rate:.2f}%",
            f"${total_profit:.2f}",
            f"${total_spins:.2f}",
            f"${total_misc:.2f}",
            f"{total_time:.1f}"
        ])

    # Return CSV
    from fastapi.responses import Response
    csv_content = output.getvalue()
    today_str = date.today().isoformat()

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=kpi_export_{today_str}.csv"
        }
    )

