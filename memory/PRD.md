# KPI Tracker - Product Requirements Document

## Project Overview
A mobile-friendly web application for tracking Key Performance Indicators (KPIs) for a reservation setter job. Converted from Expo React Native to React.js web app for better web compatibility.

## User Personas
- **Primary User**: Reservation setter tracking daily/biweekly performance metrics
- **Use Case**: Input daily calls, bookings, spins (bonuses), and misc income to track progress toward goals

## Core Requirements

### KPI Metrics & Goals
| Metric | Daily Goal | Biweekly Goal |
|--------|-----------|---------------|
| Calls | 142 | 1,710 |
| Reservations | 22 | 270 |
| Profit | $72.08 | $865 |
| Spins | $74.17 | $890 |
| Combined | - | $1,800 |
| Misc Income | - | $35 |
| Avg Time/Booking | ≤30 min | ≤30 min |

### Biweekly Period Structure
- **Period A**: 1st - 14th of each month
- **Period B**: 15th - Last day of month
- Auto-archiving at period boundaries (1st and 15th)

### Spin Rules
- Spin earned every 4th booking
- Regular spin: ~$5 average
- Mega spin (every 4th spin): ~$49 average

## Tech Stack
- **Frontend**: React.js 19, Tailwind CSS, Lucide Icons, Sonner (toasts)
- **Backend**: FastAPI, MongoDB (Motor async), APScheduler
- **No Authentication**: Single user, no login required

## What's Been Implemented ✅
- [x] Full React.js web frontend (converted from Expo)
- [x] Dark theme "Performance Pro" design
- [x] Today tab with KPI cards, progress bars, status indicators
- [x] Biweekly tab with combined earnings tracking
- [x] History tab with archived periods viewer
- [x] Add Booking modal (profit, prepaid, refund protection, time)
- [x] Add Spin modal (amount, is_mega flag)
- [x] Add Misc Income modal (request lead / refund protection)
- [x] Calendar-based period tracking (1st-14th, 15th-end)
- [x] APScheduler for automatic period archiving
- [x] Lazy period closing on first access
- [x] Period logs for historical data

## API Endpoints
- `GET /api/health` - Health check with period info
- `GET /api/entries/today` - Today's entry
- `PUT /api/entries/{date}/calls` - Update calls
- `POST /api/entries/{date}/bookings` - Add booking
- `POST /api/entries/{date}/spins` - Add spin
- `POST /api/entries/{date}/misc` - Add misc income
- `DELETE /api/entries/{date}/bookings/{id}` - Remove booking
- `GET /api/stats/daily/{date}` - Daily stats
- `GET /api/stats/biweekly` - Biweekly stats
- `GET /api/periods/current` - Current period info
- `GET /api/periods` - Archived period logs

## Backlog / Future Tasks
- [ ] **P1**: Frontend monetization UI (pro vs free plan gating)
- [ ] **P2**: Charts/graphs in History tab
- [ ] **P3**: Real authentication (JWT or social login)
- [ ] **P4**: Stripe integration for pro subscription

## Date: Feb 9, 2026
- Initial React.js web version deployed
- Backend with full archiving system operational
- All core features tested and working
