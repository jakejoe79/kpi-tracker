# KPI Tracker Application

A full-stack KPI tracking application with elite performance infrastructure, forecasting, and real-time risk monitoring.

## Current Status

**Last Updated:** March 4, 2026

### What's Working
- ✅ User authentication (fake auth for development)
- ✅ Daily KPI tracking (calls, reservations, profit)
- ✅ Biweekly period management with automatic archiving
- ✅ Peso conversion settings
- ✅ Work timer functionality
- ✅ Booking management (add, delete, edit)
- ✅ Spin tracking
- ✅ Misc income tracking
- ✅ Settings management
- ✅ Pro tier default (free tier removed)
- ✅ Build process (npm run build)

### Known Issues
- ⚠️ Live Goals Dashboard shows blank screen
- ⚠️ Timer shows "Timer already running" but isn't actually running
- ⚠️ Deleted bookings don't update immediately (requires page refresh)
- ⚠️ Goals not calculating for calls or reservations
- ⚠️ Booking update functionality not working

### What's Missing to Make It Fully Functional
- Fix DashboardLayout component to properly display goals data
- Fix timer state synchronization between frontend and backend
- Implement real-time updates for deleted bookings
- Implement goal calculations for calls and reservations
- Fix booking update endpoint
- Add proper error handling for missing goals data

## Features

- Daily KPI tracking (calls, reservations, profit)
- Biweekly period management with automatic archiving
- Team forecasting and analytics
- Risk scoring and intervention signals
- Customizable goals and targets
- Multi-user support ready
- Peso conversion with service fees
- Work timer with auto-calculation
- Spin tracking with mega spin support

## Monetization Tiers

| Feature | Trial | Individual | Pro | Group |
|---------|-------|------------|-----|-------|
| **Duration** | 14 days | Unlimited | Unlimited | Unlimited |
| **Individual Dashboard** | ✅ | ✅ | ✅ | ✅ |
| **Custom Goals** | ❌ | ✅ | ✅ | ✅ |
| **Peso Conversion** | ❌ | ✅ | ✅ | ✅ |
| **Historical Reports** | 7 days | Unlimited | Unlimited | Unlimited |
| **Export Data** | ❌ | ✅ | ✅ | ✅ |
| **Period Summary** | ❌ | Top 5 Days | Top 5 Days | Top 5 Days |
| **Team Dashboard** | ❌ | ❌ | ✅ | ✅ |
| **Team Projection** | ❌ | ❌ | ✅ (daily 6PM) | ✅ (realtime) |
| **Real-Time Projections** | ❌ | ❌ | ❌ | ✅ |
| **Risk Scoring Engine** | ❌ | ❌ | ❌ | ✅ |
| **Top 5 Intervention Signals** | ❌ | ❌ | ❌ | ✅ |
| **Team Forecast** | ❌ | ❌ | ❌ | ✅ |
| **Confidence Indicators** | ❌ | ❌ | ❌ | ✅ |
| **Trend Analysis** | ❌ | ❌ | ❌ | ✅ |
| **Alert System** | ❌ | ❌ | ❌ | ✅ |
| **Update Frequency** | Manual | Manual | Daily 6 PM | Real-time (20s) |
| **Price** | Free | $9/mo | $29/mo | $99/mo |

**Plan Positioning:**
- **Trial:** Try before you buy - basic individual tracking (14 days)
- **Individual:** Solo performers - custom goals, full history, top 5 days this period
- **Pro:** Team leaders - daily team insights and projections
- **Group:** Managers - real-time forecasting, risk scoring, Top 5 intervention signals, trend analysis

**Group Plan Exclusive Features:**
- Real-time projections (live calculation of rep performance)
- Risk scoring (algorithm-based priority ranking)
- Top 5 intervention signals (Momentum + Risk cards)
- Team forecast (aggregate projection vs goal)
- Confidence indicators (High/Medium/Low stability rating)
- Trend analysis (3-day velocity comparison)

## Tech Stack

- **Backend:** FastAPI (Python)
- **Frontend:** React with shadcn/ui components
- **Database:** MongoDB
- **Deployment:** Render
- **Scheduler:** APScheduler (period archiving, daily reset, snapshots)

## Quick Start

### Local Development

1. **Backend:**
   ```bash
   cd backend
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with your MongoDB connection string
   uvicorn server:app --reload
   ```

2. **Frontend:**
   ```bash
   cd frontend
   yarn install
   yarn start
   ```

### Deployment to Render

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed deployment instructions.

**Quick Deploy:**
1. Push code to GitHub/GitLab
2. Connect repository to Render
3. Use the `render.yaml` blueprint for automatic deployment
4. Configure MongoDB connection string in environment variables

## Environment Variables

### Backend
- `MONGO_URL`: MongoDB connection string (required)
- `DB_NAME`: Database name (default: kpi_tracker)
- `ENV`: Environment (production/development)

### Frontend
- `REACT_APP_BACKEND_URL`: Backend API URL

## License

Private project
