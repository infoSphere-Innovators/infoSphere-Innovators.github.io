# Quick Start: Deploy in 5 Minutes

## 1️⃣ Push to GitHub (Do this once)

```powershell
# From repo root
git add .
git commit -m "Add deployment configs: Procfile, requirements.txt, .gitignore"
git push origin main
```

---

## 2️⃣ Deploy Backend on Render (5 min)

**Go to:** https://render.com → Sign up with GitHub

1. Click **New** → **Web Service**
2. Select your **infoSphere-Innovators.github.io** repo
3. Fill form:
   ```
   Name: davao-build-api
   Runtime: Python 3.11
   Build Command: pip install -r backend/requirements.txt
   Start Command: cd backend && gunicorn -w 4 -b 0.0.0.0:$PORT app:app
   Plan: Free
   ```
4. Click **Create Web Service**
5. **Wait 2-3 min** for deployment
6. **Copy the URL** (e.g., `https://davao-build-api.onrender.com`)

---

## 3️⃣ Update Frontend API URL

Edit [frontend/main.js](frontend/main.js) **line 5**:

**Change from:**
```javascript
const API_BASE_URL = 'http://127.0.0.1:5000';
```

**To:**
```javascript
const API_BASE_URL = 'https://davao-build-api.onrender.com'; // Update with YOUR Render URL
```

Push to GitHub:
```powershell
git add frontend/main.js
git commit -m "Update API URL to deployed backend"
git push origin main
```

---

## 4️⃣ Deploy Frontend on GitHub Pages (instant)

1. Go to **repo Settings** → **Pages**
2. Under **Source**, select **main** branch
3. Set folder to **/ (root)**
4. Click **Save**
5. **Wait 1 min** for deployment

Your site is live at:
```
https://<YOUR-GITHUB-USERNAME>.github.io/infoSphere-Innovators.github.io
```

---

## 5️⃣ Share with Clients

Send them the link:
```
https://<YOUR-GITHUB-USERNAME>.github.io/infoSphere-Innovators.github.io
```

✅ **That's it!** No more local server needed. Push → Auto-deploy.

---

## 🔄 Future Updates

Every time you push code to GitHub, Render & GitHub Pages auto-redeploy. Just:

```powershell
git add .
git commit -m "Your message"
git push origin main
```

Done! Clients see the update within 2 minutes.

---

## ❓ Troubleshooting

**"Failed to fetch" or "CORS error"?**
- Check API URL in `main.js` line 5 matches your Render URL
- Render free tier sleeps after 15 min—first request takes 30s

**Backend not loading models?**
- Ensure all `backend/models/*.joblib` files are committed to Git
- Check Render build logs in **Settings** → **Logs**

**Site not updating after push?**
- GitHub Pages caches for 5 min; do a hard refresh (Ctrl+Shift+Del)

---

**Got questions?**
- Render docs: https://render.com/docs
- GitHub Pages: https://pages.github.com
