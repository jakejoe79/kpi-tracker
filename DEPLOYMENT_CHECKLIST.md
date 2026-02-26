# Render Deployment Checklist

## Pre-Deployment

- [ ] Code pushed to Git repository (GitHub, GitLab, or Bitbucket)
- [ ] MongoDB Atlas cluster created and configured
- [ ] MongoDB connection string ready
- [ ] MongoDB IP whitelist configured (0.0.0.0/0 or Render IPs)

## Deployment Steps

### 1. Deploy Using Blueprint (Recommended)

- [ ] Go to https://dashboard.render.com
- [ ] Click "New" → "Blueprint"
- [ ] Connect your Git repository
- [ ] Render detects `render.yaml` automatically
- [ ] Click "Apply"

### 2. Configure Backend Environment Variables

- [ ] Go to backend service in Render dashboard
- [ ] Add environment variable:
  - Key: `MONGO_URL`
  - Value: Your MongoDB connection string
  - Example: `mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority`
- [ ] Save changes
- [ ] Backend will automatically redeploy

### 3. Update Frontend Configuration

- [ ] Wait for backend to finish deploying
- [ ] Copy backend URL (e.g., `https://kpi-tracker-backend.onrender.com`)
- [ ] Go to frontend service settings
- [ ] Update environment variable:
  - Key: `REACT_APP_BACKEND_URL`
  - Value: Your backend URL (without trailing slash)
- [ ] Save and trigger manual redeploy

### 4. Verify Deployment

- [ ] Backend health check: Visit `https://your-backend.onrender.com/api/health`
- [ ] Frontend loads: Visit your frontend URL
- [ ] API connection works: Check browser console for errors
- [ ] Test creating an entry
- [ ] Test viewing stats

## Post-Deployment

- [ ] Monitor logs for any errors
- [ ] Test all major features
- [ ] Set up custom domain (optional)
- [ ] Configure monitoring/alerts (optional)

## Troubleshooting

### Backend won't start
1. Check logs in Render dashboard
2. Verify `MONGO_URL` is correct
3. Test MongoDB connection from local machine
4. Check all dependencies in `requirements.txt`

### Frontend can't connect to backend
1. Verify `REACT_APP_BACKEND_URL` is correct
2. Check backend is running and healthy
3. Look for CORS errors in browser console
4. Ensure backend URL doesn't have trailing slash

### Database connection fails
1. Check MongoDB Atlas IP whitelist
2. Verify connection string format
3. Test credentials with MongoDB Compass
4. Check database user permissions

## Free Tier Limitations

- Services spin down after 15 minutes of inactivity
- First request after spin-down takes 30-60 seconds (cold start)
- 750 hours/month for web services (enough for 1 service)
- Consider paid plan ($7/month) for production use

## Upgrade to Paid Plan

Benefits:
- No spin-down (always-on)
- Faster response times
- More resources
- Custom domains with SSL
- Priority support

To upgrade:
1. Go to service settings
2. Click "Upgrade Plan"
3. Select plan and payment method

## Support Resources

- Render Docs: https://render.com/docs
- MongoDB Atlas Docs: https://docs.atlas.mongodb.com
- FastAPI Docs: https://fastapi.tiangolo.com
- React Docs: https://react.dev

## Quick Commands

### View backend logs:
```bash
# In Render dashboard: Backend Service → Logs
```

### Trigger manual deploy:
```bash
# In Render dashboard: Service → Manual Deploy → Deploy latest commit
```

### Check service status:
```bash
curl https://your-backend.onrender.com/api/health
```

## Environment Variables Summary

### Backend (Required)
- `MONGO_URL`: MongoDB connection string

### Backend (Optional)
- `DB_NAME`: Database name (default: kpi_tracker)
- `ENV`: Environment (default: production)
- `PYTHON_VERSION`: Python version (default: 3.11.0)

### Frontend (Required)
- `REACT_APP_BACKEND_URL`: Backend API URL

### Frontend (Optional)
- `NODE_VERSION`: Node.js version (default: 18.17.0)

---

**Note:** After any environment variable change, the service will automatically redeploy. This takes 3-5 minutes for backend and 5-10 minutes for frontend.
