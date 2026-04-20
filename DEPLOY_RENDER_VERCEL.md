# SmartSpend Free Public Deployment (Render + Vercel)

This setup keeps SmartSpend public even when AWS resources are off.

## 1) Push project to GitHub

From project root:

```powershell
git add .
git commit -m "Configure Render + Vercel deployment"
git push
```

## 2) Deploy backend on Render

1. Go to Render dashboard -> `New` -> `Blueprint`.
2. Select your GitHub repo.
3. Render will read `render.yaml` and create `smartspend-api`.
4. In service environment variables, set:
   - `ALLOWED_ORIGINS` = your Vercel URL(s), comma-separated.
   Example:
   `https://smartspend-yourname.vercel.app,https://smartspend.vercel.app`
5. Deploy and copy backend URL:
   `https://<render-service>.onrender.com`

Health check:

`https://<render-service>.onrender.com/health`

## 3) Deploy frontend on Vercel

1. Go to Vercel -> `Add New Project`.
2. Import the same GitHub repo.
3. Set `Root Directory` to `frontend`.
4. Confirm build settings:
   - Build Command: `npm run build`
   - Output Directory: `dist`
5. Add environment variable:
   - `VITE_API_BASE` = your Render backend URL (no trailing slash)
6. Deploy.

## 4) Redeploy backend CORS for final domain

After Vercel gives final URL, update Render env:

- `ALLOWED_ORIGINS=https://<your-vercel-domain>`

Then redeploy backend once.

## 5) Final public links

- Frontend: `https://<your-project>.vercel.app`
- Backend: `https://<your-service>.onrender.com`

## Notes

- Render free web services may sleep after inactivity.
- First API hit after sleep can take ~30-60 seconds.
