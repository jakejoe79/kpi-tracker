"""
Unit tests for GET /api/stats/today endpoint
Feature: missing-backend-endpoints
Task: 1.1 Implement GET /api/stats/today endpoint
"""

import pytest
from httpx import AsyncClient
from datetime import date
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from server import app, db, CURRENT_USER_ID


@pytest.fixture
async def client():
    """Create test client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def clean_db():
    """Clean database before each test"""
    await db.daily_entries.delete_many({"user_id": CURRENT_USER_ID})
    yield
    await db.daily_entries.delete_many({"user_id": CURRENT_USER_ID})


@pytest.mark.asyncio
async def test_get_today_stats_no_entries(client, clean_db):
    """
    Test that /api/stats/today returns zero values when no entries exist
    Validates: Requirement 1.4 - Return zero values when no entries exist
    """
    response = await client.get("/api/stats/today")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify structure
    assert "date" in data
    assert data["date"] == date.today().isoformat()
    
    # Verify zero values
    assert data["calls"]["current"] == 0
    assert data["reservations"]["current"] == 0
    assert data["conversion_rate"]["current"] == 0
    assert data["profit"]["current"] == 0
    assert data["spins"]["current"] == 0
    assert data["combined"]["current"] == 0
    assert data["avg_time"]["current"] == 0
    assert data["earnings"]["usd"]["total"] == 0


@pytest.mark.asyncio
async def test_get_today_stats_with_entry(client, clean_db):
    """
    Test that /api/stats/today calculates statistics correctly from entry data
    Validates: Requirements 1.1, 1.2, 1.3, 1.5
    """
    today = date.today().isoformat()
    
    # Insert test entry
    test_entry = {
        "user_id": CURRENT_USER_ID,
        "date": today,
        "calls_received": 10,
        "bookings": [
            {"id": "b1", "profit": 50.0, "time_since_last": 30},
            {"id": "b2", "profit": 75.0, "time_since_last": 45}
        ],
        "spins": [
            {"id": "s1", "amount": 25.0}
        ],
        "misc_income": [
            {"id": "m1", "amount": 10.0}
        ]
    }
    
    await db.daily_entries.insert_one(test_entry)
    
    # Make request
    response = await client.get("/api/stats/today")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify calculations
    assert data["calls"]["current"] == 10
    assert data["reservations"]["current"] == 2
    assert data["profit"]["current"] == 125.0  # 50 + 75
    assert data["spins"]["current"] == 25.0
    assert data["combined"]["current"] == 150.0  # 125 + 25
    assert data["conversion_rate"]["current"] == 20.0  # 2/10 * 100
    assert data["avg_time"]["current"] == 37.5  # (30 + 45) / 2
    assert data["earnings"]["usd"]["total"] == 160.0  # 125 + 25 + 10


@pytest.mark.asyncio
async def test_get_today_stats_conversion_rate_zero_calls(client, clean_db):
    """
    Test that conversion rate is 0 when calls_received is 0
    Validates: Requirement 1.2 - Handle division by zero in conversion rate
    """
    today = date.today().isoformat()
    
    # Insert entry with bookings but no calls
    test_entry = {
        "user_id": CURRENT_USER_ID,
        "date": today,
        "calls_received": 0,
        "bookings": [
            {"id": "b1", "profit": 50.0}
        ],
        "spins": [],
        "misc_income": []
    }
    
    await db.daily_entries.insert_one(test_entry)
    
    response = await client.get("/api/stats/today")
    
    assert response.status_code == 200
    data = response.json()
    
    # Conversion rate should be 0, not error
    assert data["conversion_rate"]["current"] == 0
