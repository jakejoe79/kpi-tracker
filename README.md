# KPI Tracker Application

A full-stack KPI tracking application with forecasting and analytics capabilities.

## Tech Stack

- **Backend:** FastAPI (Python)
- **Frontend:** React with shadcn/ui components
- **Database:** MongoDB
- **Deployment:** Render

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

## Features

- Daily KPI tracking (calls, reservations, profit)
- Biweekly period management with automatic archiving
- Team forecasting and analytics
- Risk scoring and intervention signals
- Customizable goals and targets
- Multi-user support ready

## Environment Variables

### Backend
- `MONGO_URL`: MongoDB connection string (required)
- `DB_NAME`: Database name (default: kpi_tracker)
- `ENV`: Environment (production/development)

### Frontend
- `REACT_APP_BACKEND_URL`: Backend API URL

## License

Private project
