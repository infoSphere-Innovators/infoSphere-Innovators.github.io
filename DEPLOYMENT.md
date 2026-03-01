# Deployment Guide – DavaoBuild AI

## Overview
- **Backend**: Flask API deployed on Render.com (free tier)
- **Frontend**: Static site on GitHub Pages
- **Auto-Deploy**: Push to GitHub → automatic deployment

---

## Step 1: Deploy Backend to Render.com

### 1a. Create Render Account
1. Go to [render.com](https://render.com)
2. Sign up with GitHub
3. Authorize GitHub access

### 1b. Create Web Service
1. Click **New** → **Web Service**
2. Connect your **infoSphere-Innovators.github.io** repository
3. Fill in:
   - **Name**: `davao-build-api` (or similar)
   - **Runtime**: `Python 3.11`
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `cd backend && gunicorn -w 4 -b 0.0.0.0:$PORT app:app`
   - **Plan**: Free (0.1 CPU, 512 MB RAM)
4. Click **Create Web Service**

Render will build and deploy. You'll get a URL like: `https://davao-build-api.onrender.com`

---

## Step 2: Deploy Frontend to GitHub Pages

### 2a. Update Frontend API URL
After backend deploys, edit [frontend/main.js](frontend/main.js) line 5:

```javascript
// PRODUCTION — Replace with your Render backend URL
const API_BASE_URL = 'https://davao-build-api.onrender.com';
```

Push the change.

### 2b. Enable GitHub Pages
1. Go to your **GitHub repo** → **Settings**
2. Scroll to **Pages** section
3. Set **Source** to `main` branch → `/root`
4. Click **Save**

Your frontend will be live at: `https://<username>.github.io/infoSphere-Innovators.github.io`

---

## Step 3: Test Live Deployment

1. Open `https://<username>.github.io/infoSphere-Innovators.github.io` in browser
2. Click **Predict** button
3. All fetch calls should hit your Render backend ✓

---

## Notes

- **Render free tier**: App sleeps after 15 min of inactivity. First request takes ~30s to wake up.
- **Production improvement**: Use Render/Railway/Fly.io paid tier for always-on backend.
- **Domain**: You can add a custom domain in Render settings ($12/mo or use your own DNS).

---

## Troubleshooting

| Error | Solution |
|-------|----------|
| `Failed to fetch - 404` | Check backend URL in `main.js` line 5 is correct |
| `CORS error` | Backend `app.py` already has `CORS(app)` ✓ |
| `Backend not responding` | Render free tier may be asleep; refresh page after 30s |
| `Models not loading on deployment` | Ensure `backend/models/*.joblib` are committed to GitHub |

---

## Environment Variables (Optional)

For production, set environment variables in Render:
1. Go to **Settings** → **Environment**
2. Add `DEBUG=False`
3. Add custom `API_KEY` if needed

Modify `backend/app.py` to use them:
```python
import os
DEBUG = os.getenv('DEBUG', 'True') == 'True'
app.run(debug=DEBUG)
```

---

## Local Testing Before Deployment

To test locally before pushing:
```powershell
cd backend
python app.py
# In another terminal:
cd frontend
# Open index.html in browser
```

---

**Questions?** Check Render docs: https://render.com/docs
