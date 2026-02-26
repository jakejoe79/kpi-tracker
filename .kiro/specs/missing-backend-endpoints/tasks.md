# Implementation Plan: Missing Backend Endpoints

## Overview

This plan implements 16 missing FastAPI endpoints to restore full functionality to the KPI Tracker application. The implementation follows the existing FastAPI + MongoDB architecture with Pydantic models, plan-based access control, and async/await patterns. All endpoints will be added to the existing server.py file, reusing existing models and database connections.

## Tasks

- [x] 1. Implement statistics endpoints (today, week, period)
  - [x] 1.1 Implement GET /api/stats/today endpoint
    - Create async endpoint handler function
    - Query daily_entries collection for current date
    - Calculate aggregated statistics using existing DailyStats model
    - Return zero values when no entries exist
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_
  
  - [ ]* 1.2 Write property test for statistics aggregation
    - **Property 1: Statistics Aggregation Correctness**
    - **Validates: Requirements 1.2, 2.3, 2.4, 3.3**
  
  - [ ]* 1.3 Write property test for conversion rate calculation
    - **Property 2: Conversion Rate Calculation**
    - **Validates: Requirements 1.2, 6.4, 9.5, 12.4**
  
  - [x] 1.4 Implement GET /api/stats/week endpoint with Pro+ access control
    - Add check_feature_access() call for Pro plan verification
    - Return 403 if insufficient access
    - Query daily_entries for past 7 days
    - Aggregate statistics across date range
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_
  
  - [x] 1.5 Implement GET /api/stats/period endpoint with Pro+ access control
    - Add check_feature_access() call for Pro plan verification
    - Return 403 if insufficient access
    - Calculate current pay period boundaries (1st-14th or 15th-end)
    - Query daily_entries for period date range
    - Calculate period totals and goals_met status
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_
  
  - [ ]* 1.6 Write property test for Pro+ access control
    - **Property 3: Access Control Enforcement for Pro+ Features**
    - **Validates: Requirements 2.1, 2.2, 3.1, 3.2, 14.1, 14.2**

- [x] 2. Implement settings endpoints
  - [x] 2.1 Implement GET /api/settings endpoint
    - Query user_settings collection by user_id
    - Return default settings from DEFAULT_GOALS if not found
    - Return UserSettings model as JSON
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  
  - [x] 2.2 Implement PUT /api/settings endpoint
    - Accept partial settings update as Dict[str, Any]
    - Retrieve existing settings from database
    - Merge provided settings with existing settings
    - Persist merged settings to MongoDB
    - Return complete updated settings
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_
  
  - [ ]* 2.3 Write property test for settings merge behavior
    - **Property 5: Settings Merge Preserves Existing Fields**
    - **Validates: Requirements 13.3**

- [x] 3. Implement entry retrieval and calls update
  - [x] 3.1 Implement GET /api/entries/today endpoint
    - Query daily_entries for current date
    - Create new entry with zero values if not found
    - Return DailyEntry model as JSON
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_
  
  - [x] 3.2 Implement PUT /api/entries/{date}/calls endpoint
    - Validate date parameter format (YYYY-MM-DD)
    - Accept calls_received value from request body
    - Update or create daily entry with new calls value
    - Recalculate conversion rate (bookings / calls)
    - Return updated DailyEntry
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_
  
  - [ ]* 3.3 Write property test for date format validation
    - **Property 10: Date Format Validation**
    - **Validates: Requirements 6.1, 6.2, 19.2**

- [ ] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement timer endpoints
  - [x] 5.1 Implement POST /api/entries/{date}/timer/start endpoint
    - Validate date parameter format
    - Check timer_running is false, return 400 if already running
    - Set timer_start to current timestamp
    - Set timer_running to true
    - Return updated DailyEntry
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_
  
  - [x] 5.2 Implement POST /api/entries/{date}/timer/stop endpoint
    - Validate date parameter format
    - Check timer_running is true, return 400 if not running
    - Set timer_end to current timestamp
    - Calculate elapsed time: (timer_end - timer_start) in minutes
    - Add elapsed time to total_time_minutes
    - Clear timer_start and set timer_running to false
    - Return updated DailyEntry
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_
  
  - [ ]* 5.3 Write property test for timer elapsed time calculation
    - **Property 6: Timer Elapsed Time Calculation**
    - **Validates: Requirements 8.3, 8.4**
  
  - [ ]* 5.4 Write property test for timer state transitions
    - **Property 7: Timer State Transitions**
    - **Validates: Requirements 7.2, 8.2**

- [x] 6. Implement booking, spin, and misc income addition endpoints
  - [x] 6.1 Implement POST /api/entries/{date}/bookings endpoint
    - Validate date parameter format
    - Validate request body against BookingCreate schema
    - Generate unique booking ID using uuid.uuid4().hex
    - Append booking to bookings array in daily entry
    - Recalculate conversion rate
    - Return updated DailyEntry
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_
  
  - [x] 6.2 Implement POST /api/entries/{date}/spins endpoint
    - Validate date parameter format
    - Validate request body against SpinCreate schema
    - Generate unique spin ID using uuid.uuid4().hex
    - Append spin to spins array in daily entry
    - Update total spin income calculations
    - Return updated DailyEntry
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_
  
  - [x] 6.3 Implement POST /api/entries/{date}/misc endpoint
    - Validate date parameter format
    - Validate request body against MiscIncomeCreate schema
    - Generate unique income ID using uuid.uuid4().hex
    - Append income entry to misc_income array in daily entry
    - Update total miscellaneous income calculations
    - Return updated DailyEntry
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6_
  
  - [ ]* 6.4 Write property test for array item addition
    - **Property 8: Array Item Addition**
    - **Validates: Requirements 9.3, 9.4, 10.3, 10.4, 11.3, 11.4**
  
  - [ ]* 6.5 Write property test for Pydantic schema validation
    - **Property 11: Pydantic Schema Validation**
    - **Validates: Requirements 9.1, 9.2, 10.1, 10.2, 11.1, 11.2, 13.1, 13.2, 19.1, 19.4, 18.5**
  
  - [ ]* 6.6 Write property test for non-negative numeric validation
    - **Property 12: Non-Negative Numeric Validation**
    - **Validates: Requirements 19.3**

- [x] 7. Implement booking deletion endpoint
  - [x] 7.1 Implement DELETE /api/entries/{date}/bookings/{id} endpoint
    - Validate date parameter format
    - Locate booking with specified ID in bookings array
    - Return 404 if booking ID not found
    - Remove booking from bookings array
    - Recalculate conversion rate
    - Return updated DailyEntry
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_
  
  - [ ]* 7.2 Write property test for array item deletion
    - **Property 9: Array Item Deletion**
    - **Validates: Requirements 12.1, 12.3**

- [ ] 8. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Implement CSV export endpoint
  - [x] 9.1 Implement GET /api/export/csv endpoint with Pro+ access control
    - Add check_feature_access() call for Pro plan verification
    - Return 403 if insufficient access
    - Query all daily_entries for authenticated user
    - Format entries as CSV with headers: date, calls, bookings, conversion_rate, spins, misc_income, total_time
    - Set Content-Type header to text/csv
    - Set Content-Disposition header with filename "kpi_export_{date}.csv"
    - Return CSV content
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6_
  
  - [ ]* 9.2 Write property test for CSV export format
    - **Property 15: CSV Export Format**
    - **Validates: Requirements 14.4**
  
  - [ ]* 9.3 Write property test for CSV export headers
    - **Property 16: CSV Export Headers**
    - **Validates: Requirements 14.5, 14.6**

- [ ] 10. Implement team endpoints
  - [ ] 10.1 Implement GET /api/team/forecast endpoint with Individual+ access control
    - Add check_feature_access() call for Individual plan verification
    - Return 403 if insufficient access
    - Call existing get_rep_forecast() and calculate_risk_score() functions
    - Calculate projected totals, risk scores, confidence levels for team members
    - Return TeamForecast model with RepForecast array
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5_
  
  - [ ] 10.2 Implement GET /api/team/top-signals endpoint with Individual+ access control
    - Add check_feature_access() call for Individual plan verification
    - Return 403 if insufficient access
    - Accept limit query parameter (default 5)
    - Accept force_refresh query parameter (default false)
    - Call existing calculate_top_signals_live() function
    - If force_refresh=true, recalculate from current data
    - If force_refresh=false, use cached daily_snapshots data
    - Rank signals by risk_score descending
    - Return top N signals as TopSignalsResponse
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5, 16.6, 16.7_
  
  - [ ]* 10.3 Write property test for Individual+ access control
    - **Property 4: Access Control Enforcement for Individual+ Features**
    - **Validates: Requirements 15.1, 15.2, 16.1, 16.2**
  
  - [ ]* 10.4 Write property test for top signals ranking
    - **Property 17: Top Signals Ranking**
    - **Validates: Requirements 16.4, 16.5**
  
  - [ ]* 10.5 Write property test for force refresh behavior
    - **Property 18: Force Refresh Bypasses Cache**
    - **Validates: Requirements 16.6**
  
  - [ ]* 10.6 Write property test for team forecast completeness
    - **Property 25: Team Forecast Completeness**
    - **Validates: Requirements 15.4**

- [ ] 11. Implement cross-cutting concerns
  - [ ] 11.1 Add authentication requirement to all new endpoints
    - Ensure all endpoints use existing authentication dependency
    - Verify user_id extraction from auth token
    - Scope all database queries to authenticated user
    - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5_
  
  - [ ] 11.2 Add consistent error handling to all endpoints
    - Use HTTPException for all error responses
    - Map error conditions to appropriate status codes (400, 401, 403, 404, 422, 500)
    - Return JSON with "detail" field for all errors
    - Add try-catch blocks for database operations
    - Log errors with appropriate levels (INFO, WARNING, ERROR)
    - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5_
  
  - [ ]* 11.3 Write property test for user data scoping
    - **Property 13: User Data Scoping**
    - **Validates: Requirements 17.3, 17.4**
  
  - [ ]* 11.4 Write property test for authentication requirement
    - **Property 14: Authentication Requirement**
    - **Validates: Requirements 17.1, 17.2**
  
  - [ ]* 11.5 Write property test for error status code mapping
    - **Property 19: Error Status Code Mapping**
    - **Validates: Requirements 18.1, 18.3**
  
  - [ ]* 11.6 Write property test for error response format
    - **Property 20: Error Response Format**
    - **Validates: Requirements 18.2**

- [ ] 12. Implement response format consistency
  - [ ] 12.1 Verify all responses use snake_case field naming
    - Review all Pydantic models for consistent naming
    - Ensure FastAPI serialization preserves snake_case
    - _Requirements: 20.2_
  
  - [ ] 12.2 Verify timestamp fields use ISO 8601 format
    - Ensure datetime fields serialize to ISO 8601
    - Add timezone handling if needed
    - _Requirements: 20.3_
  
  - [ ] 12.3 Verify empty arrays are represented as []
    - Check all list fields in responses
    - Ensure Pydantic models default to empty lists, not None
    - _Requirements: 20.4_
  
  - [ ]* 12.4 Write property test for response field naming convention
    - **Property 21: Response Field Naming Convention**
    - **Validates: Requirements 20.2**
  
  - [ ]* 12.5 Write property test for timestamp format consistency
    - **Property 22: Timestamp Format Consistency**
    - **Validates: Requirements 20.3**
  
  - [ ]* 12.6 Write property test for empty array representation
    - **Property 23: Empty Array Representation**
    - **Validates: Requirements 20.4**
  
  - [ ]* 12.7 Write property test for period statistics goals met
    - **Property 24: Period Statistics Include Goals Met**
    - **Validates: Requirements 3.4**

- [ ] 13. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 14. Integration and verification
  - [ ] 14.1 Test all endpoints with frontend application
    - Start backend server
    - Verify frontend can call all 16 endpoints without 404 errors
    - Test user flows: view stats, add entries, update settings, export CSV
    - Verify access control for premium features
    - _Requirements: All requirements_
  
  - [ ]* 14.2 Write integration tests for complete user workflows
    - Test end-to-end flows: timer start/stop, booking add/delete
    - Test settings update and retrieval
    - Test statistics calculation across multiple entries
    - _Requirements: All requirements_

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties using hypothesis library
- Unit tests validate specific examples and edge cases
- All endpoints will be added to the existing server.py file
- Reuse existing Pydantic models, database connections, and helper functions
- Follow existing code patterns from /api/stats/biweekly endpoint
