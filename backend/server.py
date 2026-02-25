from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks, Depends
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, date, timedelta
import calendar
import asyncio
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import statistics

from backend.constants import SPIN_RULES, calculate_progress, is_on_track, get_status


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
CURRENT_USER_PLAN = "group"

# =============================================================================
# FEATURE REGISTRY
# =============================================================================

FEATURES = {
    "export_data": {"label": "Export Data", "description": "Download CSV and PDF reports", "required_plan": "pro"},
    "custom_goals": {"label": "Custom Goals", "description": "Set personalized KPI targets", "required_plan": "pro"},
    "historical_reports": {"label": "Historical Reports", "description": "Access reports beyond 14 days", "required_plan": "pro"},
    "multiple_periods": {"label": "Multiple Periods", "description": "Compare across custom date ranges", "required_plan": "pro"},
    "team_dashboard": {"label": "Team Dashboard", "description": "View team-wide KPI stats", "required_plan": "group"},
    "advanced_analytics": {"label": "Advanced Analytics", "description": "Detailed performance insights and trends", "required_plan": "group"},
    "priority_support": {"label": "Priority Support", "description": "24/7 priority customer support", "required_plan": "group"},
}

PLAN_HIERARCHY = {"free": 0, "pro": 1, "group": 2}

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

# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class User(BaseModel):
    id: str
    email: str
    plan: str = "free"
    created_at: datetime = Field(default_factory=datetime.utcnow)

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
    rep_forecasts: List[RepForecast]

class InterventionSignal(BaseModel):
    user_id: str
    rank: int
    signal_type: str
    risk_score: float
    risk_level: str
    projected_reservations: float
    gap: float
    trend: str
    action_required: str

class TopSignalsResponse(BaseModel):
    signals: List[InterventionSignal]
    generated_at: datetime
    update_mode: str

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
# FORECASTING ENGINE
# =============================================================================

def calculate_risk_score(projected: float, goal: float, trend_direction: str) -> float:
    if goal <= 0:
        return 0
    percent_of_goal = (projected / goal) * 100
    base_risk = max(0, 100 - percent_of_goal)
    trend_multiplier = 1.3 if trend_direction == "↓ declining" else 0.7 if trend_direction == "↑ improving" else 1.0
    return min(100, max(0, base_risk * trend_multiplier))

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
        return "→ stable" if recent_avg == 0 else "↑ improving"
    
    change_ratio = recent_avg / older_avg
    if change_ratio > 1.1:
        return "↑ improving"
    elif change_ratio < 0.9:
        return "↓ declining"
    return "→ stable"

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
    
    risk_score = calculate_risk_score(projected, goal, trend)
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
    
    scheduler.start()
    logger.info("APScheduler started")

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

@api_router.get("/health")
async def health():
    start, end, period_id = get_current_period()
    return {
        "status": "healthy",
        "env": os.environ.get("ENV", "development"),
        "plan_mode": CURRENT_USER_PLAN,
        "current_period": period_id,
    }

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
        "update_mode": "realtime" if user.plan == "group" else "daily"
    }

@api_router.put("/settings")
async def update_settings(settings_update: Dict[str, Any]):
    user = get_current_user_sync()
    access = check_feature_access(user, "custom_goals")
    
    if not access["allowed"]:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Custom goals require Pro or Group plan",
                "current_plan": user.plan,
                "required_plan": access["required_plan"]
            }
        )
    
    updated_goals = settings_update.get("goals", {})
    success = await update_user_goals(CURRENT_USER_ID, updated_goals)
    
    return {
        "success": success,
        "message": "Settings updated" if success else "No changes",
        "goals": {**DEFAULT_GOALS, **updated_goals},
        "updated_at": datetime.utcnow().isoformat()
    }

# Keep old endpoint for backward compatibility
@api_router.get("/goals")
async def get_goals():
    return await get_user_goals(CURRENT_USER_ID)

# TEAM FORECAST - Multi-user safe
@api_router.get("/team/forecast", response_model=TeamForecast)
async def get_team_forecast():
    user = get_current_user_sync()
    access = check_feature_access(user, "advanced_analytics")
    
    if not access["allowed"]:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Team forecasting requires Group plan",
                "current_plan": user.plan,
                "required_plan": "group"
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
        rep_forecasts=rep_forecasts
    )

@api_router.get("/team/top-signals", response_model=TopSignalsResponse)
async def get_top_signals(limit: int = 5):
    user = get_current_user_sync()
    access = check_feature_access(user, "advanced_analytics")
    
    if not access["allowed"]:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Top signals requires Group plan",
                "current_plan": user.plan,
                "required_plan": "group"
            }
        )
    
    forecast_data = await get_team_forecast()
    rep_forecasts = forecast_data.rep_forecasts
    
    sorted_reps = sorted(rep_forecasts, key=lambda x: x.risk_score, reverse=True)
    
    signals = []
    for idx, rep in enumerate(sorted_reps[:limit]):
        signal_type = "risk" if rep.risk_level in ["high", "medium"] else "momentum"
        
        if rep.risk_level == "high":
            action = "Immediate coaching required"
        elif rep.risk_level == "medium":
            action = "Schedule check-in this week"
        elif rep.gap >= 0:
            action = "On track - maintain momentum"
        else:
            action = "Star performer - recognize"
        
        signals.append(InterventionSignal(
            user_id=rep.user_id,
            rank=idx + 1,
            signal_type=signal_type,
            risk_score=rep.risk_score,
            risk_level=rep.risk_level,
            projected_reservations=rep.projected_reservations,
            gap=rep.gap,
            trend=rep.trend,
            action_required=action
        ))
    
    return TopSignalsResponse(
        signals=signals,
        generated_at=datetime.utcnow(),
        update_mode="realtime" if user.plan == "group" else "daily"
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

# APP SETUP
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# STARTUP/SHUTDOWN
@app.on_event("startup")
async def startup_event():
    # Ensure indexes for multi-user queries
    await db.daily_entries.create_index([("user_id", 1), ("date", 1)])
    await db.period_logs.create_index([("user_id", 1), ("period_id", 1)])
    await db.user_goals.create_index("user_id", unique=True)
    await db.daily_archives.create_index([("user_id", 1), ("date", 1), ("type", 1)])
    
    start_scheduler()
    logger.info("Application startup complete with multi-user support")

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()
    client.close()
    logger.info("Application shutdown complete")