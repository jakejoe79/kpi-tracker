# Requirements Document

## Introduction

The KPI Tracker frontend application is currently non-functional because it makes API calls to 16 backend endpoints that do not exist in the backend implementation. This results in 404 errors for all user operations including viewing statistics, managing daily entries, updating settings, and accessing premium features. This specification defines the requirements for implementing these missing endpoints to restore full application functionality.

The backend uses FastAPI with MongoDB and includes plan-based access control (trial, individual, pro, group). Existing infrastructure includes Pydantic models, authentication, and one working endpoint (/api/stats/biweekly).

## Glossary

- **API_Server**: The FastAPI backend server that handles HTTP requests
- **Frontend**: The React-based user interface application
- **Daily_Entry**: A MongoDB document containing KPI data for a specific date (calls, bookings, spins, misc income, timer data)
- **User_Settings**: Configuration data stored per user (goals, preferences, notification settings)
- **Stats_Aggregator**: The component that calculates KPI statistics from daily entries
- **Access_Controller**: The component that enforces plan-based feature access (trial/individual/pro/group)
- **Timer_Manager**: The component that tracks active work session timing
- **CSV_Exporter**: The component that generates CSV files from user data
- **Team_Forecaster**: The component that calculates team-level projections
- **Signal_Analyzer**: The component that identifies intervention signals for team members

## Requirements

### Requirement 1: Daily Statistics Endpoint

**User Story:** As a user, I want to view my KPI statistics for today, so that I can track my current performance.

#### Acceptance Criteria

1. WHEN a GET request is made to /api/stats/today, THE API_Server SHALL return daily statistics for the current date
2. THE Stats_Aggregator SHALL calculate total calls, bookings, spins, conversion rate, and income for today
3. THE API_Server SHALL return statistics in JSON format matching the DailyStats schema
4. IF no entries exist for today, THEN THE API_Server SHALL return zero values for all metrics
5. THE API_Server SHALL return HTTP 200 status code for successful requests

### Requirement 2: Weekly Statistics Endpoint

**User Story:** As a Pro+ user, I want to view my weekly statistics, so that I can analyze my performance trends over the week.

#### Acceptance Criteria

1. WHEN a GET request is made to /api/stats/week, THE Access_Controller SHALL verify the user has Pro or Group plan access
2. IF the user lacks required access, THEN THE API_Server SHALL return HTTP 403 status code with denial reason
3. WHEN access is granted, THE Stats_Aggregator SHALL calculate statistics for the past 7 days
4. THE Stats_Aggregator SHALL aggregate calls, bookings, spins, conversion rates, and income across the 7-day period
5. THE API_Server SHALL return weekly statistics in JSON format

### Requirement 3: Pay Period Statistics Endpoint

**User Story:** As a Pro+ user, I want to view statistics for the current pay period, so that I can track progress toward period goals.

#### Acceptance Criteria

1. WHEN a GET request is made to /api/stats/period, THE Access_Controller SHALL verify the user has Pro or Group plan access
2. IF the user lacks required access, THEN THE API_Server SHALL return HTTP 403 status code with denial reason
3. WHEN access is granted, THE Stats_Aggregator SHALL calculate statistics from the period start date to current date
4. THE Stats_Aggregator SHALL include period totals, goals met status, and daily averages
5. THE API_Server SHALL return period statistics in JSON format matching the PeriodTotals schema

### Requirement 4: User Settings Retrieval

**User Story:** As a user, I want to retrieve my saved settings, so that the application displays my preferences and goals.

#### Acceptance Criteria

1. WHEN a GET request is made to /api/settings, THE API_Server SHALL retrieve the user's settings document from MongoDB
2. IF no settings document exists, THEN THE API_Server SHALL return default settings values
3. THE API_Server SHALL return settings including goals, preferences, and notification configuration
4. THE API_Server SHALL return HTTP 200 status code with settings in JSON format
5. THE API_Server SHALL include all fields defined in the user settings schema

### Requirement 5: Today's Entry Retrieval

**User Story:** As a user, I want to retrieve today's entry data, so that I can view and edit my current day's activities.

#### Acceptance Criteria

1. WHEN a GET request is made to /api/entries/today, THE API_Server SHALL retrieve the daily entry for the current date
2. IF no entry exists for today, THEN THE API_Server SHALL create a new entry with zero values
3. THE API_Server SHALL return the entry including calls, bookings, spins, misc income, and timer state
4. THE API_Server SHALL return HTTP 200 status code with entry data in JSON format
5. THE Daily_Entry SHALL include the normalized entry format with period_id and user_id

### Requirement 6: Calls Update Endpoint

**User Story:** As a user, I want to update the number of calls received, so that I can track my call volume accurately.

#### Acceptance Criteria

1. WHEN a PUT request is made to /api/entries/{date}/calls with calls_received value, THE API_Server SHALL validate the date format
2. IF the date format is invalid, THEN THE API_Server SHALL return HTTP 400 status code with error message
3. WHEN the date is valid, THE API_Server SHALL update or create the daily entry with the new calls_received value
4. THE API_Server SHALL recalculate conversion rate based on updated calls and existing bookings
5. THE API_Server SHALL return HTTP 200 status code with the updated entry in JSON format

### Requirement 7: Timer Start Endpoint

**User Story:** As a user, I want to start a work session timer, so that I can track my active working time.

#### Acceptance Criteria

1. WHEN a POST request is made to /api/entries/{date}/timer/start, THE Timer_Manager SHALL record the current timestamp as timer_start
2. IF a timer is already running for this date, THEN THE API_Server SHALL return HTTP 400 status code with error message
3. THE Timer_Manager SHALL store the timer_start timestamp in the daily entry document
4. THE API_Server SHALL set timer_running status to true
5. THE API_Server SHALL return HTTP 200 status code with updated entry including timer state

### Requirement 8: Timer Stop Endpoint

**User Story:** As a user, I want to stop the work session timer, so that I can record the duration of my work session.

#### Acceptance Criteria

1. WHEN a POST request is made to /api/entries/{date}/timer/stop, THE Timer_Manager SHALL record the current timestamp as timer_end
2. IF no timer is running for this date, THEN THE API_Server SHALL return HTTP 400 status code with error message
3. THE Timer_Manager SHALL calculate elapsed time between timer_start and timer_end
4. THE Timer_Manager SHALL add the elapsed time to the total_time_minutes field
5. THE Timer_Manager SHALL clear timer_start and set timer_running to false
6. THE API_Server SHALL return HTTP 200 status code with updated entry including accumulated time

### Requirement 9: Add Booking Endpoint

**User Story:** As a user, I want to add a booking entry, so that I can record successful reservations.

#### Acceptance Criteria

1. WHEN a POST request is made to /api/entries/{date}/bookings with booking data, THE API_Server SHALL validate the booking data against BookingCreate schema
2. IF validation fails, THEN THE API_Server SHALL return HTTP 422 status code with validation errors
3. WHEN validation succeeds, THE API_Server SHALL generate a unique booking ID
4. THE API_Server SHALL append the booking to the bookings array in the daily entry
5. THE API_Server SHALL recalculate conversion rate based on updated bookings and existing calls
6. THE API_Server SHALL return HTTP 200 status code with the updated entry

### Requirement 10: Add Spin Endpoint

**User Story:** As a user, I want to add a spin entry, so that I can track spin-related activities and income.

#### Acceptance Criteria

1. WHEN a POST request is made to /api/entries/{date}/spins with spin data, THE API_Server SHALL validate the spin data against SpinCreate schema
2. IF validation fails, THEN THE API_Server SHALL return HTTP 422 status code with validation errors
3. WHEN validation succeeds, THE API_Server SHALL generate a unique spin ID
4. THE API_Server SHALL append the spin to the spins array in the daily entry
5. THE API_Server SHALL update total spin income calculations
6. THE API_Server SHALL return HTTP 200 status code with the updated entry

### Requirement 11: Add Miscellaneous Income Endpoint

**User Story:** As a user, I want to add miscellaneous income entries, so that I can track additional revenue sources.

#### Acceptance Criteria

1. WHEN a POST request is made to /api/entries/{date}/misc with income data, THE API_Server SHALL validate the income data against MiscIncomeCreate schema
2. IF validation fails, THEN THE API_Server SHALL return HTTP 422 status code with validation errors
3. WHEN validation succeeds, THE API_Server SHALL generate a unique income ID
4. THE API_Server SHALL append the income entry to the misc_income array in the daily entry
5. THE API_Server SHALL update total miscellaneous income calculations
6. THE API_Server SHALL return HTTP 200 status code with the updated entry

### Requirement 12: Delete Booking Endpoint

**User Story:** As a user, I want to delete a booking entry, so that I can correct mistakes or remove cancelled bookings.

#### Acceptance Criteria

1. WHEN a DELETE request is made to /api/entries/{date}/bookings/{id}, THE API_Server SHALL locate the booking with the specified ID
2. IF the booking ID does not exist, THEN THE API_Server SHALL return HTTP 404 status code with error message
3. WHEN the booking exists, THE API_Server SHALL remove it from the bookings array
4. THE API_Server SHALL recalculate conversion rate based on remaining bookings and existing calls
5. THE API_Server SHALL return HTTP 200 status code with the updated entry

### Requirement 13: Update Settings Endpoint

**User Story:** As a user, I want to update my settings, so that I can customize goals and preferences.

#### Acceptance Criteria

1. WHEN a PUT request is made to /api/settings with settings data, THE API_Server SHALL validate the settings data structure
2. IF validation fails, THEN THE API_Server SHALL return HTTP 422 status code with validation errors
3. WHEN validation succeeds, THE API_Server SHALL merge the provided settings with existing settings
4. THE API_Server SHALL persist the updated settings to the MongoDB user settings collection
5. THE API_Server SHALL return HTTP 200 status code with the complete updated settings

### Requirement 14: CSV Export Endpoint

**User Story:** As a Pro+ user, I want to export my data as CSV, so that I can analyze it in spreadsheet applications.

#### Acceptance Criteria

1. WHEN a GET request is made to /api/export/csv, THE Access_Controller SHALL verify the user has Pro or Group plan access
2. IF the user lacks required access, THEN THE API_Server SHALL return HTTP 403 status code with denial reason
3. WHEN access is granted, THE CSV_Exporter SHALL retrieve all daily entries for the user
4. THE CSV_Exporter SHALL format entries as CSV with columns for date, calls, bookings, conversion rate, spins, misc income, and total time
5. THE API_Server SHALL return HTTP 200 status code with Content-Type header set to text/csv
6. THE API_Server SHALL include Content-Disposition header with filename "kpi_export_{date}.csv"

### Requirement 15: Team Forecast Endpoint

**User Story:** As an Individual+ user, I want to view team forecast data, so that I can see projected team performance.

#### Acceptance Criteria

1. WHEN a GET request is made to /api/team/forecast, THE Access_Controller SHALL verify the user has Individual, Pro, or Group plan access
2. IF the user lacks required access, THEN THE API_Server SHALL return HTTP 403 status code with denial reason
3. WHEN access is granted, THE Team_Forecaster SHALL calculate forecasts for all team members
4. THE Team_Forecaster SHALL include projected totals, risk scores, and confidence levels for each team member
5. THE API_Server SHALL return HTTP 200 status code with team forecast data in JSON format matching TeamForecast schema

### Requirement 16: Top Signals Endpoint

**User Story:** As an Individual+ user, I want to view top intervention signals, so that I can identify team members who need support.

#### Acceptance Criteria

1. WHEN a GET request is made to /api/team/top-signals, THE Access_Controller SHALL verify the user has Individual, Pro, or Group plan access
2. IF the user lacks required access, THEN THE API_Server SHALL return HTTP 403 status code with denial reason
3. WHEN access is granted, THE Signal_Analyzer SHALL calculate intervention signals for all team members
4. THE Signal_Analyzer SHALL rank signals by risk score and return the top 5 by default
5. WHERE a limit query parameter is provided, THE API_Server SHALL return that number of top signals
6. WHERE a force_refresh query parameter is true, THE Signal_Analyzer SHALL recalculate signals instead of using cached data
7. THE API_Server SHALL return HTTP 200 status code with signals array in JSON format matching TopSignalsResponse schema

## Cross-Cutting Requirements

### Requirement 17: Authentication and Authorization

**User Story:** As a system administrator, I want all endpoints to be authenticated, so that only authorized users can access their data.

#### Acceptance Criteria

1. FOR ALL endpoints except /api/health and root, THE API_Server SHALL require valid authentication
2. IF authentication is missing or invalid, THEN THE API_Server SHALL return HTTP 401 status code
3. THE API_Server SHALL extract user identity from authentication token
4. THE API_Server SHALL scope all data operations to the authenticated user
5. THE Access_Controller SHALL enforce plan-based feature restrictions for premium endpoints

### Requirement 18: Error Handling

**User Story:** As a developer, I want consistent error responses, so that the frontend can handle errors predictably.

#### Acceptance Criteria

1. WHEN an error occurs, THE API_Server SHALL return appropriate HTTP status codes (400, 401, 403, 404, 422, 500)
2. THE API_Server SHALL include error details in JSON format with message and error type
3. IF a database operation fails, THEN THE API_Server SHALL return HTTP 500 status code with generic error message
4. THE API_Server SHALL log detailed error information for debugging without exposing sensitive data to clients
5. FOR ALL validation errors, THE API_Server SHALL return specific field-level error messages

### Requirement 19: Data Validation

**User Story:** As a system, I want to validate all input data, so that data integrity is maintained.

#### Acceptance Criteria

1. FOR ALL POST and PUT endpoints, THE API_Server SHALL validate request bodies against Pydantic schemas
2. THE API_Server SHALL validate date parameters match ISO 8601 format (YYYY-MM-DD)
3. THE API_Server SHALL validate numeric values are non-negative where applicable
4. IF validation fails, THEN THE API_Server SHALL return HTTP 422 status code with detailed validation errors
5. THE API_Server SHALL sanitize string inputs to prevent injection attacks

### Requirement 20: Response Format Consistency

**User Story:** As a frontend developer, I want consistent response formats, so that I can parse responses reliably.

#### Acceptance Criteria

1. FOR ALL successful responses, THE API_Server SHALL return JSON format with appropriate Content-Type header
2. THE API_Server SHALL use consistent field naming conventions (snake_case) across all responses
3. THE API_Server SHALL include timestamp fields in ISO 8601 format
4. FOR ALL list responses, THE API_Server SHALL return arrays even when empty
5. THE API_Server SHALL exclude null fields from responses or represent them consistently
