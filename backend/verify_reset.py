#!/usr/bin/env python3
"""
Verify Current Period Reset
"""
import asyncio
from datetime import date, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def verify_reset():
    mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017/kpi_tracker')
    client = AsyncIOMotorClient(mongo_url)
    db_name = os.getenv('DB_NAME', 'kpi_tracker')
    db = client[db_name]

    try:
        # Get current period
        today = date.today()
        if today.day <= 15:
            period_start = today.replace(day=1)
        else:
            period_start = today.replace(day=16)

        period_end = period_start + timedelta(days=13)

        print(f'Verifying reset for period: {period_start} to {period_end}')

        # Check entries in current period
        entries = await db.daily_entries.find({
            'user_id': 'user_001',
            'date': {
                '$gte': period_start.isoformat(),
                '$lte': period_end.isoformat()
            }
        }).to_list(None)

        print(f'Found {len(entries)} entries in current period')

        total_bookings = 0
        total_misc = 0
        total_calls = 0

        for entry in entries:
            bookings = entry.get('bookings', [])
            misc_income = entry.get('misc_income', [])
            calls = entry.get('calls_received', 0)

            total_bookings += len(bookings)
            total_misc += len(misc_income)
            total_calls += calls

            print(f'{entry["date"]}: {len(bookings)} bookings, {len(misc_income)} misc, {calls} calls')

        print(f'\nTOTAL - Bookings: {total_bookings}, Misc Income: {total_misc}, Calls: {total_calls}')

        if total_bookings == 0 and total_misc == 0 and total_calls == 0:
            print('✅ SUCCESS: All earnings data reset to 0s!')
        else:
            print('❌ ISSUE: Some earnings data still exists')

    except Exception as e:
        print(f'Error: {e}')
    finally:
        client.close()

if __name__ == '__main__':
    asyncio.run(verify_reset())