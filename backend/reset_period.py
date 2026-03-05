#!/usr/bin/env python3
"""
Reset Current Period Earnings to 0s
"""
import asyncio
from datetime import date, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def reset_current_period():
    mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017/kpi_tracker')
    client = AsyncIOMotorClient(mongo_url)
    db_name = os.getenv('DB_NAME', 'kpi_tracker')
    db = client[db_name]

    try:
        # Get current period - biweekly periods
        today = date.today()
        # Find the start of the current biweekly period
        # Assuming periods start on the 1st and 15th of each month

        if today.day <= 15:
            period_start = today.replace(day=1)
        else:
            period_start = today.replace(day=16)

        period_end = period_start + timedelta(days=13)  # 14 days total

        print(f'Current period: {period_start} to {period_end}')

        # Get all entries for current period
        entries = await db.daily_entries.find({
            'user_id': 'user_001',
            'date': {
                '$gte': period_start.isoformat(),
                '$lte': period_end.isoformat()
            }
        }).to_list(None)

        print(f'Found {len(entries)} entries in current period')

        # Reset each entry
        reset_count = 0
        for entry in entries:
            date_str = entry['date']

            # Reset all earnings data
            await db.daily_entries.update_one(
                {'user_id': 'user_001', 'date': date_str},
                {
                    '$set': {
                        'calls_received': 0,
                        'bookings': [],
                        'spins': [],
                        'misc_income': [],
                        'total_time_minutes': 0.0,
                        'work_timer_start': None,
                        'updated_at': {'$date': '2026-03-04T00:00:00.000Z'}
                    }
                }
            )
            reset_count += 1

        print(f'Successfully reset {reset_count} entries to 0s')

        # Also reset any metrics for this period
        await db.user_daily_metrics.delete_many({
            'user_id': 'user_001',
            'period_id': {'$regex': f'^{period_start.isoformat()}'}
        })

        print('Reset complete - all earnings for current period are now 0s')

    except Exception as e:
        print(f'Error resetting period: {e}')
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == '__main__':
    asyncio.run(reset_current_period())