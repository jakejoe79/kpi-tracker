"""
Statistics endpoints for KPI Tracker API
"""
from fastapi import APIRouter, HTTPException
from datetime import date, timedelta, datetime
from backend.constants import CURRENT_USER_ID, CURRENT_USER_PLAN

# This will be imported from server.py
# from server import db, get_user_goals, check_feature_access, get_current_user_sync, get_current_period

router = APIRouter()


@router.get("/stats/today")
async def get_today_stats(db, get_user_goals):
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
