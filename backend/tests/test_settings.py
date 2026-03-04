"""Tests for settings persistence functionality."""
import pytest
from fastapi.testclient import TestClient
from backend.server import app, get_database
from backend.config import MONGODB_URI, MONGODB_DB_NAME
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

client = TestClient(app)

# Test user ID
TEST_USER_ID = "test_user_settings"
CURRENT_USER_ID = TEST_USER_ID

# Override the CURRENT_USER_ID for testing
import backend.server as server_module
server_module.CURRENT_USER_ID = TEST_USER_ID


@pytest.fixture(scope="module")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def setup_database():
    """Set up test database."""
    # Connect to test database
    test_client = AsyncIOMotorClient(MONGODB_URI)
    test_db = test_client[MONGODB_DB_NAME]
    
    # Clean up any existing test data
    await test_db.user_settings.delete_one({"user_id": TEST_USER_ID})
    
    yield test_db
    
    # Clean up after test
    await test_db.user_settings.delete_one({"user_id": TEST_USER_ID})
    test_client.close()


@pytest.mark.asyncio
async def test_get_settings_returns_default_when_none_exist(setup_database):
    """Test that GET /settings returns default values when no settings exist."""
    response = client.get("/api/settings")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == TEST_USER_ID
    assert data["peso_rate"] == 17.50  # Default value
    assert "goals" in data


@pytest.mark.asyncio
async def test_update_settings_persists_peso_rate(setup_database):
    """Test that updating peso_rate persists to database."""
    # Update settings with custom peso rate
    response = client.put("/api/settings", json={
        "peso_rate": 55.0,
        "processing_fee_percent": 15,
        "period_fee": 50
    })
    assert response.status_code == 200
    data = response.json()
    assert data["peso_rate"] == 55.0
    
    # Verify it persisted by fetching again
    response = client.get("/api/settings")
    assert response.status_code == 200
    data = response.json()
    assert data["peso_rate"] == 55.0  # Should still be 55, not default 17.50


@pytest.mark.asyncio
async def test_update_settings_persists_goals(setup_database):
    """Test that updating goals persists to database."""
    test_goals = {
        "calls_daily": 5,
        "reservations_daily": 2,
        "profit_daily": 500,
        "calls_biweekly": 20,
        "reservations_biweekly": 10,
        "profit_biweekly": 2000
    }
    
    # Update settings with custom goals
    response = client.put("/api/settings", json={
        "peso_rate": 20.0,
        "goals": test_goals
    })
    assert response.status_code == 200
    data = response.json()
    assert data["goals"]["calls_daily"] == 5
    assert data["goals"]["profit_biweekly"] == 2000
    
    # Verify it persisted by fetching again
    response = client.get("/api/settings")
    assert response.status_code == 200
    data = response.json()
    assert data["goals"]["calls_daily"] == 5
    assert data["goals"]["profit_biweekly"] == 2000


@pytest.mark.asyncio
async def test_update_settings_validates_peso_rate(setup_database):
    """Test that invalid peso_rate values are rejected."""
    # Try negative peso rate
    response = client.put("/api/settings", json={
        "peso_rate": -10.0
    })
    assert response.status_code == 400
    
    # Try zero peso rate
    response = client.put("/api/settings", json={
        "peso_rate": 0
    })
    assert response.status_code == 400
    
    # Try non-numeric peso rate
    response = client.put("/api/settings", json={
        "peso_rate": "invalid"
    })
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_settings_persistence_survives_multiple_requests(setup_database):
    """Test that settings persist across multiple API calls."""
    # Set initial value
    response = client.put("/api/settings", json={"peso_rate": 75.0})
    assert response.status_code == 200
    
    # Make multiple GET requests to verify persistence
    for _ in range(5):
        response = client.get("/api/settings")
        assert response.status_code == 200
        assert response.json()["peso_rate"] == 75.0
