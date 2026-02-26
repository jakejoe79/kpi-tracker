# Design Document: Missing Backend Endpoints

## Overview

This design implements 16 missing FastAPI endpoints to restore full functionality to the KPI Tracker application. The frontend currently receives 404 errors for all user operations because these endpoints don't exist in the backend.

The implementation follows the existing FastAPI + MongoDB architecture with Pydantic models for validation, plan-based access control (trial/individual/pro/group), and async/await patterns. The design prioritizes consistency with the existing `/api/stats/biweekly` endpoint pattern while adding proper error handling, validation, and access control.

Key design principles:
- Reuse existing Pydantic models (DailyEntry, BookingCreate, SpinCreate, etc.)
- Follow existing authentication pattern (CURRENT_USER_ID hardcoded auth)
- Maintain consistent error responses (HTTPException with status codes)
- Use existing MongoDB collections (daily_entries, user_settings, daily_snapshots)
- Implement plan-based access control using check_feature_access()
- Calculate statistics server-side, return formatted JSON to frontend

## Architecture

### System Components

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Frontend  │────────▶│  API Router  │────────▶│  MongoDB    │
│   (React)   │◀────────│  (FastAPI)   │◀────────│  Database   │
└─────────────┘         └──────────────┘         └─────────────┘
                              │
                              ▼
                        ┌──────────────┐
                        │   Access     │
                        │  Controller  │
                        └──────────────┘
```

### Component Responsibilities

**API Router (FastAPI)**
- Route HTTP requests to handler functions
- Validate request parameters and bodies using Pydantic
- Execute business logic (calculations, data transformations)
- Return JSON responses with appropriate status codes
- Handle errors with HTTPException

**Access Controller**
- Verify user plan level against feature requirements
- Return 403 Forbidden for insufficient access
- Use existing check_feature_access() function
- Enforce plan hierarchy: trial < individual < pro < group

**MongoDB Database**
- Store daily_entries collection (KPI data per date)
- Store user_settings collection (goals, preferences)
- Store daily_snapshots collection (cached team calculations)
- Provide async queries via motor.motor_asyncio

**Stats Aggregator**
- Calculate KPI statistics from daily entries
- Aggregate calls, bookings, spins, income across date ranges
- Compute conversion rates (bookings / calls)
- Build MetricStat, ConversionStat, TimeStat objects

**Timer Manager**
- Track work session start/stop times
- Calculate elapsed time between timer_start and timer_end
- Accumulate total_time_minutes in daily entries
- Validate timer state (prevent double-start, stop without start)

**CSV Exporter**
- Query all daily entries for authenticated user
- Format data as CSV with headers
- Set Content-Type: text/csv and Content-Disposition headers
- Generate filename with current date

**Team Forecaster**
- Calculate projected totals for team members
- Compute risk scores based on gap to goal and trends
- Use existing calculate_risk_score() and get_rep_forecast() functions
- Return TeamForecast with RepForecast array

**Signal Analyzer**
- Identify team members needing intervention
- Rank by risk_score descending
- Return top N signals (default 5)
- Use existing calculate_top_signals_live() function

## Components and Interfaces

### Endpoint Definitions

All endpoints use `/api` prefix and require authentication (except /api/health and root).

#### Statistics Endpoints

**GET /api/stats/today**
- Returns: DailyStats (JSON)
- Access: All authenticated users
- Calculates today's KPI totals from daily_entries collection

**GET /api/stats/week**
- Returns: WeeklyStats (JSON)
- Access: Pro+ users only (403 if insufficient)
- Aggregates past 7 days of daily_entries

**GET /api/stats/period**
- Returns: PeriodTotals (JSON)
- Access: Pro+ users only (403 if insufficient)
- Aggregates current pay period (1st-14th or 15th-end)

#### Settings Endpoints

**GET /api/settings**
- Returns: UserSettings (JSON)
- Access: All authenticated users
- Retrieves from user_settings collection, returns defaults if not found

**PUT /api/settings**
- Request Body: Dict[str, Any] (partial settings update)
- Returns: UserSettings (JSON)
- Access: All authenticated users
- Merges provided settings with existing, persists to MongoDB

#### Entry Management Endpoints

**GET /api/entries/today**
- Returns: DailyEntry (JSON)
- Access: All authenticated users
- Retrieves or creates today's entry with zero values

**PUT /api/entries/{date}/calls**
- Path Param: date (YYYY-MM-DD)
- Request Body: {"calls_received": int}
- Returns: DailyEntry (JSON)
- Access: All authenticated users
- Updates calls_received, recalculates conversion rate

**POST /api/entries/{date}/timer/start**
- Path Param: date (YYYY-MM-DD)
- Returns: DailyEntry (JSON)
- Access: All authenticated users
- Sets timer_start to current timestamp, timer_running to true

**POST /api/entries/{date}/timer/stop**
- Path Param: date (YYYY-MM-DD)
- Returns: DailyEntry (JSON)
- Access: All authenticated users
- Sets timer_end, calculates elapsed time, adds to total_time_minutes

**POST /api/entries/{date}/bookings**
- Path Param: date (YYYY-MM-DD)
- Request Body: BookingCreate (JSON)
- Returns: DailyEntry (JSON)
- Access: All authenticated users
- Generates booking ID, appends to bookings array, recalculates conversion

**POST /api/entries/{date}/spins**
- Path Param: date (YYYY-MM-DD)
- Request Body: SpinCreate (JSON)
- Returns: DailyEntry (JSON)
- Access: All authenticated users
- Generates spin ID, appends to spins array, updates spin income

**POST /api/entries/{date}/misc**
- Path Param: date (YYYY-MM-DD)
- Request Body: MiscIncomeCreate (JSON)
- Returns: DailyEntry (JSON)
- Access: All authenticated users
- Generates income ID, appends to misc_income array, updates misc income total

**DELETE /api/entries/{date}/bookings/{id}**
- Path Params: date (YYYY-MM-DD), id (string)
- Returns: DailyEntry (JSON)
- Access: All authenticated users
- Removes booking from array, recalculates conversion rate

#### Export Endpoints

**GET /api/export/csv**
- Returns: CSV file (text/csv)
- Access: Pro+ users only (403 if insufficient)
- Exports all daily_entries as CSV with filename header

#### Team Endpoints

**GET /api/team/forecast**
- Returns: TeamForecast (JSON)
- Access: Individual+ users only (403 if insufficient)
- Calculates team member projections and risk scores

**GET /api/team/top-signals**
- Query Params: limit (int, default 5), force_refresh (bool, default false)
- Returns: TopSignalsResponse (JSON)
- Access: Individual+ users only (403 if insufficient)
- Returns top N intervention signals ranked by risk_score

### Data Models

All models already exist in server.py. Key models:

**DailyEntry**
```python
{
  "date": "2024-01-15",
  "user_id": "user_001",
  "period_id": "2024-01-15_to_2024-01-31",
  "calls_received": 5,
  "bookings": [BookingCreate],
  "spins": [SpinCreate],
  "misc_income": [MiscIncomeCreate],
  "timer_start": "2024-01-15T09:00:00",
  "timer_running": true,
  "total_time_minutes": 120
}
```

**DailyStats**
```python
{
  "calls": MetricStat,
  "bookings": MetricStat,
  "conversion": ConversionStat,
  "spins": MetricStat,
  "income": MetricStat,
  "time": TimeStat
}
```

**UserSettings**
```python
{
  "user_id": "user_001",
  "goals": {
    "calls_biweekly": 10,
    "reservations_biweekly": 5,
    ...
  },
  "preferences": {...},
  "notifications": {...}
}
```

### Database Schema

**Collections:**

1. **daily_entries**
   - Primary key: {user_id, date}
   - Indexes: user_id, date, period_id
   - Stores DailyEntry documents

2. **user_settings**
   - Primary key: user_id
   - Stores UserSettings documents

3. **daily_snapshots**
   - Primary key: {user_id, period_id}
   - Stores cached team forecast and signals
   - Used for Pro plan daily snapshots

### Error Handling Strategy

**HTTP Status Codes:**
- 200: Success
- 400: Bad request (invalid date format, timer state errors)
- 401: Unauthorized (missing/invalid auth)
- 403: Forbidden (insufficient plan access)
- 404: Not found (booking/spin/misc income ID not found)
- 422: Unprocessable entity (Pydantic validation errors)
- 500: Internal server error (database failures)

**Error Response Format:**
```json
{
  "detail": "Error message describing the issue"
}
```

FastAPI automatically formats HTTPException as {"detail": message}.

**Validation Errors:**
Pydantic automatically returns 422 with field-level errors:
```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## Data Models

### Request/Response Models

All models are already defined in server.py as Pydantic BaseModel classes:

**Input Models:**
- BookingCreate: {name, phone, email, notes, amount}
- SpinCreate: {type, amount, notes}
- MiscIncomeCreate: {source, amount, notes}

**Output Models:**
- DailyEntry: Complete entry with all fields
- DailyStats: Aggregated statistics for a single day
- BiweeklyStats: Aggregated statistics for 14-day period
- PeriodTotals: Current period statistics with goals_met
- TeamForecast: Array of RepForecast objects
- TopSignalsResponse: Array of InterventionSignal objects

**Shared Models:**
- MetricStat: {total, goal, progress, status}
- ConversionStat: {rate, bookings, calls, goal_rate}
- TimeStat: {total_minutes, avg_minutes, goal_minutes}

### Database Document Structure

**daily_entries document:**
```python
{
  "_id": ObjectId,
  "date": "2024-01-15",
  "user_id": "user_001",
  "period_id": "2024-01-15_to_2024-01-31",
  "calls_received": 5,
  "bookings": [
    {
      "id": "uuid",
      "name": "John Doe",
      "phone": "555-1234",
      "email": "john@example.com",
      "notes": "VIP guest",
      "amount": 150.00,
      "created_at": "2024-01-15T10:30:00"
    }
  ],
  "spins": [...],
  "misc_income": [...],
  "timer_start": "2024-01-15T09:00:00",
  "timer_running": true,
  "total_time_minutes": 120
}
```

**user_settings document:**
```python
{
  "_id": ObjectId,
  "user_id": "user_001",
  "goals": {
    "calls_biweekly": 10,
    "reservations_biweekly": 5,
    "profit_biweekly": 0,
    ...
  },
  "preferences": {
    "theme": "light",
    "notifications_enabled": true
  },
  "notifications": {
    "email": true,
    "push": false
  }
}
```

### Data Validation Rules

**Date Validation:**
- Format: YYYY-MM-DD (ISO 8601)
- Validated by FastAPI path parameter parsing
- Invalid format returns 422 Unprocessable Entity

**Numeric Validation:**
- calls_received: non-negative integer
- amount fields: non-negative float
- Validated by Pydantic model constraints

**String Validation:**
- All string inputs sanitized (no special handling needed, MongoDB handles escaping)
- Required fields enforced by Pydantic (Field(...) or non-Optional)

**Timer State Validation:**
- Start: timer_running must be false, else 400 error
- Stop: timer_running must be true, else 400 error

**ID Validation:**
- Booking/spin/misc income IDs: must exist in array, else 404 error
- Generated using uuid.uuid4().hex


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After analyzing all acceptance criteria, several redundant properties were identified and consolidated:

- Access control properties (2.1, 2.2, 3.1, 3.2, 14.1, 14.2, 15.1, 15.2, 16.1, 16.2) follow the same pattern and can be tested with a single property per access level
- Schema validation properties (9.1, 9.2, 10.1, 10.2, 11.1, 11.2, 13.1, 13.2) follow the same Pydantic validation pattern
- Conversion rate recalculation (6.4, 9.5, 12.4) is the same calculation triggered by different operations
- HTTP 200 success responses (1.5, 4.4, 5.4, 6.5, etc.) are redundant - testing the response content implies success
- JSON format responses (1.3, 2.5, 3.5, 4.4, 5.4, etc.) are redundant - FastAPI automatically serializes to JSON
- ID generation properties (9.3, 10.3, 11.3) follow the same pattern

The following properties represent the unique, non-redundant correctness requirements:

### Property 1: Statistics Aggregation Correctness

*For any* set of daily entries for a given date range, the aggregated statistics SHALL correctly sum calls_received, bookings count, spins count, total income, and total time across all entries.

**Validates: Requirements 1.2, 2.3, 2.4, 3.3**

### Property 2: Conversion Rate Calculation

*For any* daily entry with calls_received and bookings, the conversion rate SHALL equal (bookings count / calls_received) when calls > 0, and 0 when calls = 0.

**Validates: Requirements 1.2, 6.4, 9.5, 12.4**

### Property 3: Access Control Enforcement for Pro+ Features

*For any* user with plan level below "pro", requests to /api/stats/week, /api/stats/period, or /api/export/csv SHALL return HTTP 403 with denial reason.

**Validates: Requirements 2.1, 2.2, 3.1, 3.2, 14.1, 14.2**

### Property 4: Access Control Enforcement for Individual+ Features

*For any* user with plan level below "individual", requests to /api/team/forecast or /api/team/top-signals SHALL return HTTP 403 with denial reason.

**Validates: Requirements 15.1, 15.2, 16.1, 16.2**

### Property 5: Settings Merge Preserves Existing Fields

*For any* existing user settings and partial settings update, the merged result SHALL contain all fields from the existing settings that were not included in the update, plus all fields from the update.

**Validates: Requirements 13.3**

### Property 6: Timer Elapsed Time Calculation

*For any* timer session with timer_start and timer_end timestamps, the elapsed time in minutes SHALL equal (timer_end - timer_start) converted to minutes, and this value SHALL be added to total_time_minutes.

**Validates: Requirements 8.3, 8.4**

### Property 7: Timer State Transitions

*For any* daily entry, starting a timer SHALL only succeed when timer_running is false, and stopping a timer SHALL only succeed when timer_running is true.

**Validates: Requirements 7.2, 8.2**

### Property 8: Array Item Addition

*For any* valid BookingCreate, SpinCreate, or MiscIncomeCreate data, adding the item to its respective array SHALL increase the array length by 1 and the new item SHALL have a unique generated ID.

**Validates: Requirements 9.3, 9.4, 10.3, 10.4, 11.3, 11.4**

### Property 9: Array Item Deletion

*For any* existing booking ID in a daily entry, deleting that booking SHALL remove it from the bookings array and decrease the array length by 1.

**Validates: Requirements 12.1, 12.3**

### Property 10: Date Format Validation

*For any* date parameter in path or query, the API SHALL accept ISO 8601 format (YYYY-MM-DD) and reject any other format with HTTP 400 or 422 status code.

**Validates: Requirements 6.1, 6.2, 19.2**

### Property 11: Pydantic Schema Validation

*For any* POST or PUT request with a request body, the API SHALL validate the body against the corresponding Pydantic schema and return HTTP 422 with field-level errors if validation fails.

**Validates: Requirements 9.1, 9.2, 10.1, 10.2, 11.1, 11.2, 13.1, 13.2, 19.1, 19.4, 18.5**

### Property 12: Non-Negative Numeric Validation

*For any* numeric input field (calls_received, amount, etc.), the API SHALL reject negative values with HTTP 422 validation error.

**Validates: Requirements 19.3**

### Property 13: User Data Scoping

*For any* authenticated request to a data endpoint, the API SHALL only return or modify data belonging to the authenticated user, never data from other users.

**Validates: Requirements 17.3, 17.4**

### Property 14: Authentication Requirement

*For any* endpoint except /api/health and root (/), the API SHALL require valid authentication and return HTTP 401 if authentication is missing or invalid.

**Validates: Requirements 17.1, 17.2**

### Property 15: CSV Export Format

*For any* set of daily entries, the CSV export SHALL include columns for date, calls, bookings, conversion_rate, spins, misc_income, and total_time, with one row per entry plus a header row.

**Validates: Requirements 14.4**

### Property 16: CSV Export Headers

*For any* successful CSV export, the response SHALL include Content-Type: text/csv and Content-Disposition header with filename pattern "kpi_export_{date}.csv".

**Validates: Requirements 14.5, 14.6**

### Property 17: Top Signals Ranking

*For any* set of intervention signals, the top-signals endpoint SHALL return them sorted by risk_score in descending order, limited to the specified limit parameter (default 5).

**Validates: Requirements 16.4, 16.5**

### Property 18: Force Refresh Bypasses Cache

*For any* request to /api/team/top-signals with force_refresh=true, the API SHALL recalculate signals from current data instead of returning cached daily snapshot data.

**Validates: Requirements 16.6**

### Property 19: Error Status Code Mapping

*For any* error condition, the API SHALL return the appropriate HTTP status code: 400 for bad requests, 401 for authentication failures, 403 for authorization failures, 404 for not found, 422 for validation errors, and 500 for server errors.

**Validates: Requirements 18.1, 18.3**

### Property 20: Error Response Format

*For any* error response, the API SHALL return JSON with a "detail" field containing the error message.

**Validates: Requirements 18.2**

### Property 21: Response Field Naming Convention

*For any* JSON response, all field names SHALL use snake_case naming convention.

**Validates: Requirements 20.2**

### Property 22: Timestamp Format Consistency

*For any* timestamp field in a response, the value SHALL be in ISO 8601 format.

**Validates: Requirements 20.3**

### Property 23: Empty Array Representation

*For any* list field in a response (bookings, spins, misc_income, etc.), the field SHALL be an empty array [] when no items exist, never null or omitted.

**Validates: Requirements 20.4**

### Property 24: Period Statistics Include Goals Met

*For any* period statistics response, the response SHALL include a goals_met object with boolean flags for each goal type and calculated daily averages.

**Validates: Requirements 3.4**

### Property 25: Team Forecast Completeness

*For any* team forecast response, each team member's forecast SHALL include projected_total, risk_score, confidence_level, and trend_direction fields.

**Validates: Requirements 15.4**

### Edge Cases

The following edge cases require specific handling:

**Edge Case 1: No Entries for Today**
When no daily entries exist for the current date, /api/stats/today SHALL return DailyStats with all metric totals set to 0.
**Validates: Requirements 1.4**

**Edge Case 2: No Settings Document**
When no user_settings document exists for a user, /api/settings SHALL return default settings values from DEFAULT_GOALS.
**Validates: Requirements 4.2**

**Edge Case 3: No Entry for Today**
When no daily entry exists for the current date, /api/entries/today SHALL create a new entry with zero values for all metrics.
**Validates: Requirements 5.2**

**Edge Case 4: Timer Already Running**
When a timer is already running (timer_running=true), POST /api/entries/{date}/timer/start SHALL return HTTP 400 with error message "Timer already running".
**Validates: Requirements 7.2**

**Edge Case 5: Timer Not Running**
When no timer is running (timer_running=false), POST /api/entries/{date}/timer/stop SHALL return HTTP 400 with error message "No timer running".
**Validates: Requirements 8.2**

**Edge Case 6: Booking ID Not Found**
When a booking ID does not exist in the bookings array, DELETE /api/entries/{date}/bookings/{id} SHALL return HTTP 404 with error message "Booking not found".
**Validates: Requirements 12.2**


## Error Handling

### Error Categories and Responses

**Client Errors (4xx)**

1. **400 Bad Request**
   - Invalid date format in path parameters
   - Timer state violations (starting when running, stopping when not running)
   - Example: `{"detail": "Timer already running"}`

2. **401 Unauthorized**
   - Missing authentication token
   - Invalid authentication token
   - Example: `{"detail": "Not authenticated"}`

3. **403 Forbidden**
   - Insufficient plan level for premium features
   - Example: `{"detail": "This feature requires Pro plan or higher", "required_plan": "pro"}`

4. **404 Not Found**
   - Booking/spin/misc income ID not found in array
   - Example: `{"detail": "Booking not found"}`

5. **422 Unprocessable Entity**
   - Pydantic validation failures
   - Invalid field types or missing required fields
   - Example:
   ```json
   {
     "detail": [
       {
         "loc": ["body", "amount"],
         "msg": "ensure this value is greater than or equal to 0",
         "type": "value_error.number.not_ge"
       }
     ]
   }
   ```

**Server Errors (5xx)**

1. **500 Internal Server Error**
   - MongoDB connection failures
   - Unexpected exceptions during processing
   - Example: `{"detail": "Internal server error"}`
   - Note: Detailed error logged server-side, generic message returned to client

### Error Handling Implementation

**FastAPI HTTPException Pattern:**
```python
from fastapi import HTTPException

# Example: Access control
if not check_feature_access(user, "export_data")["allowed"]:
    raise HTTPException(
        status_code=403,
        detail="This feature requires Pro plan or higher"
    )

# Example: Not found
if booking_id not in [b["id"] for b in entry["bookings"]]:
    raise HTTPException(
        status_code=404,
        detail="Booking not found"
    )

# Example: Bad request
if entry.get("timer_running"):
    raise HTTPException(
        status_code=400,
        detail="Timer already running"
    )
```

**Database Error Handling:**
```python
try:
    result = await db.daily_entries.update_one(...)
except Exception as e:
    logger.error(f"Database error: {e}")
    raise HTTPException(
        status_code=500,
        detail="Internal server error"
    )
```

**Validation Error Handling:**
Pydantic automatically raises 422 errors with detailed field-level messages. No custom handling needed.

### Logging Strategy

**Log Levels:**
- INFO: Successful operations, endpoint access
- WARNING: Access denied, validation failures
- ERROR: Database errors, unexpected exceptions

**Log Format:**
```
2024-01-15 10:30:00 - api - INFO - GET /api/stats/today - user_001 - 200
2024-01-15 10:31:00 - api - WARNING - GET /api/export/csv - user_001 - 403 - Insufficient plan
2024-01-15 10:32:00 - api - ERROR - POST /api/entries/2024-01-15/bookings - user_001 - 500 - Database connection failed
```

**Sensitive Data Protection:**
- Never log authentication tokens
- Never log full user documents
- Log user IDs only for tracing
- Sanitize error messages before returning to client

## Testing Strategy

### Dual Testing Approach

This feature requires both unit tests and property-based tests for comprehensive coverage:

**Unit Tests** focus on:
- Specific examples of endpoint behavior
- Edge cases (no data, timer state violations, ID not found)
- Integration between components (database operations, access control)
- Error conditions (authentication failures, validation errors)

**Property-Based Tests** focus on:
- Universal properties that hold for all inputs
- Comprehensive input coverage through randomization
- Calculation correctness (aggregation, conversion rates)
- Data integrity (array operations, merging)

### Property-Based Testing Configuration

**Library Selection:**
- Python: Use `hypothesis` library (industry standard for Python PBT)
- Installation: `pip install hypothesis`

**Test Configuration:**
- Minimum 100 iterations per property test
- Each test tagged with comment referencing design property
- Tag format: `# Feature: missing-backend-endpoints, Property {number}: {property_text}`

**Example Property Test Structure:**
```python
from hypothesis import given, strategies as st
import pytest

# Feature: missing-backend-endpoints, Property 2: Conversion Rate Calculation
@given(
    calls=st.integers(min_value=0, max_value=1000),
    bookings=st.integers(min_value=0, max_value=1000)
)
@pytest.mark.property_test
def test_conversion_rate_calculation(calls, bookings):
    """
    For any daily entry with calls_received and bookings,
    the conversion rate SHALL equal (bookings / calls) when calls > 0,
    and 0 when calls = 0.
    """
    entry = {"calls_received": calls, "bookings": [{"id": f"b{i}"} for i in range(bookings)]}
    
    if calls > 0:
        expected_rate = bookings / calls
    else:
        expected_rate = 0.0
    
    actual_rate = calculate_conversion_rate(entry)
    assert abs(actual_rate - expected_rate) < 0.001  # Float comparison tolerance
```

### Unit Test Coverage

**Endpoint Tests:**
- Test each endpoint with valid inputs
- Test authentication requirements
- Test access control for premium features
- Test error responses for invalid inputs

**Example Unit Test:**
```python
@pytest.mark.asyncio
async def test_get_today_stats_returns_zero_when_no_entries():
    """Edge Case 1: No entries for today returns zeros"""
    # Setup: Clear database
    await db.daily_entries.delete_many({"user_id": "test_user"})
    
    # Execute
    response = await client.get("/api/stats/today")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["calls"]["total"] == 0
    assert data["bookings"]["total"] == 0
    assert data["conversion"]["rate"] == 0.0
```

**Integration Tests:**
- Test database operations (create, read, update, delete)
- Test timer start/stop sequences
- Test booking/spin/misc income addition and deletion
- Test settings merge behavior

**Edge Case Tests:**
- No entries for today (Edge Case 1)
- No settings document (Edge Case 2)
- No entry for today (Edge Case 3)
- Timer already running (Edge Case 4)
- Timer not running (Edge Case 5)
- Booking ID not found (Edge Case 6)

### Test Data Generation

**Hypothesis Strategies:**
```python
from hypothesis import strategies as st
from datetime import date, timedelta

# Date strategy
dates = st.dates(
    min_value=date.today() - timedelta(days=365),
    max_value=date.today()
)

# Daily entry strategy
daily_entries = st.builds(
    dict,
    date=dates.map(lambda d: d.isoformat()),
    calls_received=st.integers(min_value=0, max_value=100),
    bookings=st.lists(
        st.builds(
            dict,
            id=st.uuids().map(str),
            amount=st.floats(min_value=0, max_value=1000)
        ),
        max_size=50
    )
)

# User plan strategy
plans = st.sampled_from(["trial", "individual", "pro", "group"])
```

### Test Execution

**Running Tests:**
```bash
# Run all tests
pytest tests/

# Run only unit tests
pytest tests/ -m "not property_test"

# Run only property tests
pytest tests/ -m property_test

# Run with coverage
pytest tests/ --cov=backend --cov-report=html
```

**CI/CD Integration:**
- Run all tests on every commit
- Require 80%+ code coverage for new endpoints
- Run property tests with 100 iterations in CI
- Run extended property tests (1000 iterations) nightly

### Test Organization

```
tests/
├── test_stats_endpoints.py          # Unit tests for statistics endpoints
├── test_settings_endpoints.py       # Unit tests for settings endpoints
├── test_entry_endpoints.py          # Unit tests for entry management
├── test_timer_endpoints.py          # Unit tests for timer operations
├── test_export_endpoints.py         # Unit tests for CSV export
├── test_team_endpoints.py           # Unit tests for team features
├── test_access_control.py           # Unit tests for authentication/authorization
├── property_tests/
│   ├── test_aggregation_properties.py    # Property 1, 2
│   ├── test_access_control_properties.py # Property 3, 4, 14
│   ├── test_data_operations_properties.py # Property 5, 8, 9, 13
│   ├── test_timer_properties.py          # Property 6, 7
│   ├── test_validation_properties.py     # Property 10, 11, 12
│   ├── test_export_properties.py         # Property 15, 16
│   ├── test_team_properties.py           # Property 17, 18, 25
│   └── test_response_properties.py       # Property 19, 20, 21, 22, 23, 24
└── conftest.py                      # Shared fixtures and configuration
```

### Success Criteria

**Definition of Done:**
- All 16 endpoints implemented and functional
- All 25 correctness properties pass with 100+ iterations
- All 6 edge cases handled correctly
- All unit tests pass
- Code coverage ≥ 80%
- Frontend successfully calls all endpoints without 404 errors
- Access control enforced for premium features
- Error responses consistent and informative

