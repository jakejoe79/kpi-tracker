# Deployment Guide for Render

This guide will help you deploy the KPI Tracker application to Render.

## Current Status

**Last Updated:** March 4, 2026

### Deployment Status
- ✅ Backend: Ready to deploy
- ✅ Frontend: Ready to deploy
- ⚠️ Known issues after deployment (see README.md for details)

## Prerequisites

1. A Render account (sign up at https://render.com)
2. A MongoDB Atlas account with a cluster set up (https://www.mongodb.com/cloud/atlas)
3. Your code pushed to a Git repository (GitHub, GitLab, or Bitbucket)

## Deployment Options

### Option 1: Using render.yaml (Recommended)

This method deploys both backend and frontend automatically using the `render.yaml` blueprint.

1. **Connect your repository to Render:**
   - Go to https://dashboard.render.com
   - Click "New" → "Blueprint"
   - Connect your Git repository
   - Render will automatically detect the `render.yaml` file

2. **Configure environment variables:**
   - In the Render dashboard, go to your backend service
   - Add the following environment variable:
     - `MONGO_URL`: Your MongoDB connection string (e.g., `mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority`)
   
3. **Deploy:**
   - Click "Apply" to deploy both services
   - Wait for the build to complete (5-10 minutes)

4. **Update frontend API URL:**
   - After backend deploys, note its URL (e.g., `https://kpi-tracker-backend.onrender.com`)
   - Go to frontend service settings
   - Update `REACT_APP_BACKEND_URL` environment variable with your backend URL
   - Trigger a manual redeploy of the frontend

### Option 2: Manual Deployment

#### Deploy Backend

1. **Create a new Web Service:**
   - Go to Render Dashboard → "New" → "Web Service"
   - Connect your repository
   - Configure:
     - Name: `kpi-tracker-backend`
     - Runtime: `Python 3`
     - Build Command: `pip install -r backend/requirements.txt`
     - Start Command: `gunicorn backend.server:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`

2. **Add environment variables:**
   - `MONGO_URL`: Your MongoDB connection string
   - `DB_NAME`: `kpi_tracker`
   - `ENV`: `production`
   - `PYTHON_VERSION`: `3.11.0`

3. **Deploy and note the URL**

#### Deploy Frontend

1. **Create a new Static Site:**
   - Go to Render Dashboard → "New" → "Static Site"
   - Connect your repository
   - Configure:
     - Name: `kpi-tracker-frontend`
     - Build Command: `cd frontend && npm install && npm run build`
     - Publish Directory: `frontend/build`

2. **Add environment variable:**
   - `REACT_APP_BACKEND_URL`: Your backend URL from step above

3. **Configure rewrites (for React Router):**
   - Add rewrite rule: `/*` → `/index.html`

4. **Deploy**

## MongoDB Setup

1. **Create a MongoDB Atlas cluster:**
   - Go to https://www.mongodb.com/cloud/atlas
   - Create a free cluster
   - Create a database user with read/write permissions
   - Whitelist Render's IP addresses (or use `0.0.0.0/0` for all IPs)

2. **Get connection string:**
   - Click "Connect" on your cluster
   - Choose "Connect your application"
   - Copy the connection string
   - Replace `<password>` with your database user password

## Post-Deployment

1. **Test the application:**
   - Visit your frontend URL
   - Check that API calls work correctly
   - Monitor logs in Render dashboard

2. **Set up custom domain (optional):**
   - In Render dashboard, go to your service settings
   - Add custom domain under "Custom Domains"
   - Update DNS records as instructed

## Troubleshooting

### Backend Issues

- **Check logs:** Render Dashboard → Backend Service → Logs
- **Common issues:**
  - MongoDB connection: Verify `MONGO_URL` is correct and IP whitelist is configured
  - Port binding: Ensure start command uses `$PORT` variable
  - Dependencies: Check `requirements.txt` includes all packages

### Frontend Issues

- **API connection fails:**
  - Verify `REACT_APP_BACKEND_URL` points to correct backend URL
  - Check CORS settings in backend (currently set to allow all origins)
  - Ensure backend is running and healthy

- **404 on page refresh:**
  - Verify rewrite rule is configured: `/*` → `/index.html`

- **Live Goals Dashboard blank:**
  - This is a known issue - the DashboardLayout component needs to be fixed
  - The component expects nested data structure but backend returns flat structure

### Performance

- **Free tier limitations:**
  - Services spin down after 15 minutes of inactivity
  - First request after spin-down will be slow (cold start)
  - Consider upgrading to paid tier for production use

## Environment Variables Reference

### Backend
- `MONGO_URL` (required): MongoDB connection string
- `DB_NAME` (optional): Database name, defaults to `kpi_tracker`
- `ENV` (optional): Environment name, set to `production`
- `PYTHON_VERSION` (optional): Python version, defaults to `3.11.0`

### Frontend
- `REACT_APP_BACKEND_URL` (required): Backend API URL
- `NODE_VERSION` (optional): Node.js version, defaults to `18.17.0`

## Costs

- **Free Tier:**
  - Backend: 750 hours/month (enough for 1 service)
  - Frontend: Unlimited bandwidth for static sites
  - MongoDB Atlas: 512MB storage free tier

- **Paid Plans:**
  - Start at $7/month for always-on services
  - See https://render.com/pricing for details

## Support

- Render Documentation: https://render.com/docs
- MongoDB Atlas Documentation: https://docs.atlas.mongodb.com
- Project Issues: [Your repository issues page]
