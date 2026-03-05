"""Tests for the timer start/stop endpoints and normalization.
"""
import pytest
from fastapi.testclient import TestClient
from backend.server import app
from datetime import date, timedelta, datetime
import os
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

MONGODB_URI = os.getenv('MONGO_URL', 'mongodb://localhost:27017/kpi_tracker')
MONGODB_DB_NAME = os.getenv('DB_NAME', 'kpi_tracker')

client = TestClient(app)

TEST_USER_ID = "test_timer_user"

# Monkey patch the server's CURRENT_USER_ID so our requests act as the test user
import backend.server as server_module
server_module.CURRENT_USER_ID = TEST_USER_ID

@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="module")
async def setup_database():
    test_client = AsyncIOMotorClient(MONGODB_URI)
    test_db = test_client[MONGODB_DB_NAME]
    # cleanup
    await test_db.daily_entries.delete_many({"user_id": TEST_USER_ID})
    yield test_db
    await test_db.daily_entries.delete_many({"user_id": TEST_USER_ID})
    test_client.close()

@pytest.mark.asyncio
async def test_timer_flow(setup_database=None):
    today = date.today().isoformat()

    # ensure no entry exists initially
    resp = client.get(f"/api/entries/{today}")
    assert resp.status_code == 404

    # start timer
    resp = client.post(f"/api/entries/{today}/timer/start")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("work_timer_start") is not None
    assert data.get("total_time_minutes") == 0 or data.get("total_time_minutes") == 0.0

    # query timer status immediately
    resp = client.get(f"/api/entries/{today}/timer")
    assert resp.status_code == 200
    status = resp.json()
    assert status.get("elapsed_minutes") >= 0

    # simulate time passage by manually setting a past start
    past = (datetime.utcnow() - timedelta(hours=1)).isoformat()
    db = setup_database
    await db.daily_entries.update_one({"user_id": TEST_USER_ID, "date": today}, {"$set": {"work_timer_start": past}})

    # check elapsed reflects ~60 minutes
    resp = client.get(f"/api/entries/{today}/timer")
    assert resp.status_code == 200
    status = resp.json()
    assert 50 <= status.get("elapsed_minutes", 0) <= 70

    # stop timer and ensure total_time_minutes updated and start cleared
    resp = client.post(f"/api/entries/{today}/timer/stop")
    assert resp.status_code == 200
    stopped = resp.json()
    assert stopped.get("work_timer_start") is None
    assert stopped.get("total_time_minutes") >= 50

    # fetch entry to ensure elapsed == total_time_minutes after stop
    resp = client.get(f"/api/entries/{today}")
    assert resp.status_code == 200
    entry = resp.json()
    assert entry.get("elapsed_minutes") == entry.get("total_time_minutes")


