import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import os

async def test_timer():
    mongo_url = os.getenv('MONGODB_URL', 'mongodb://localhost:27017/kpi_tracker')
    client = AsyncIOMotorClient(mongo_url)
    db = client.kpi_tracker
    date = '2026-03-04'
    user_id = 'user_001'

    # ensure clean slate
    await db.daily_entries.delete_many({'user_id': user_id, 'date': date})

    print('starting timer using update endpoint logic...')
    # simulate start_timer
    entry = await db.daily_entries.find_one({'user_id': user_id, 'date': date})
    if entry and entry.get('work_timer_start'):
        timer_start = datetime.fromisoformat(entry['work_timer_start'])
        elapsed_minutes = (datetime.utcnow() - timer_start).total_seconds() / 60
        await db.daily_entries.update_one({'user_id': user_id, 'date': date}, {'$set': {'work_timer_start': None, 'updated_at': datetime.utcnow()}, '$inc': {'total_time_minutes': elapsed_minutes}})
    _, _, period_id = ('', '', '2026-03-01')
    await db.daily_entries.update_one({'user_id': user_id, 'date': date}, {'$set': {'work_timer_start': datetime.utcnow().isoformat(), 'updated_at': datetime.utcnow()}, '$setOnInsert': {'id': 'test-entry', 'user_id': user_id, 'date': date, 'period_id': period_id, 'calls_received': 0, 'bookings': [], 'spins': [], 'misc_income': [], 'total_time_minutes': 0.0, 'created_at': datetime.utcnow()}}, upsert=True)
    entry = await db.daily_entries.find_one({'user_id': user_id, 'date': date})
    print('after start', entry)

    # wait a bit
    await asyncio.sleep(1)

    # simulate get_timer_status
    work_start = entry.get('work_timer_start')
    total_time = entry.get('total_time_minutes', 0.0)
    elapsed = total_time
    if work_start:
        start_dt = datetime.fromisoformat(work_start)
        elapsed += (datetime.utcnow() - start_dt).total_seconds() / 60
    print('elapsed computed', elapsed)

    # simulate stop_timer
    entry = await db.daily_entries.find_one({'user_id': user_id, 'date': date})
    if entry and entry.get('work_timer_start'):
        timer_start = datetime.fromisoformat(entry['work_timer_start'])
        elapsed_minutes = (datetime.utcnow() - timer_start).total_seconds() / 60
        await db.daily_entries.update_one({'user_id': user_id, 'date': date}, {'$set': {'work_timer_start': None, 'updated_at': datetime.utcnow()}, '$inc': {'total_time_minutes': elapsed_minutes}})
    entry = await db.daily_entries.find_one({'user_id': user_id, 'date': date})
    print('after stop', entry)

    client.close()

if __name__ == '__main__':
    asyncio.run(test_timer())
