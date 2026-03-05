#!/usr/bin/env python3
"""
Clear all spins from daily_entries
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def clear_spins():
    mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017/kpi_tracker')
    client = AsyncIOMotorClient(mongo_url)
    db_name = os.getenv('DB_NAME', 'kpi_tracker')
    db = client[db_name]

    try:
        # Clear spins for all entries
        result = await db.daily_entries.update_many(
            {'user_id': 'user_001'},
            {'$set': {'spins': []}}
        )
        print(f'Cleared spins from {result.modified_count} entries')

    except Exception as e:
        print(f'Error clearing spins: {e}')
    finally:
        client.close()

if __name__ == '__main__':
    asyncio.run(clear_spins())