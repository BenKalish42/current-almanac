# Production API Setup

## 404 on Live Site

The app calls `/api/interpret` and `/api/chat`. On the live site (benkalish.com), these must reach your backend.

### Option A: Set VITE_API_URL at build time (recommended)

1. Deploy the FastAPI backend somewhere (Render, Railway, Fly.io, etc.).
2. Before running `./scripts/deploy_to_benkalish.sh`, create `.env` in the project root:

   ```
   VITE_API_URL=https://your-backend.onrender.com
   ```

3. Run the deploy script. The build will bake this URL into the bundle; all API calls will go to your backend.

### Option B: Netlify proxy (if backend is on same domain)

If your backend is served from the same Netlify site or a subdomain, add to `netlify.toml` in PersonalWebsite:

```toml
[[redirects]]
  from = "/api/*"
  to = "https://YOUR_BACKEND_URL/api/:splat"
  status = 200
  force = true
```

Replace `YOUR_BACKEND_URL` with your actual backend URL.

## 500 / DeepSeek errors on dev

- **401**: Invalid or missing `DEEPSEEK_API_KEY`. Add to `backend/.env`.
- **429**: Rate limit. Wait and retry.
- **404**: Try `DEEPSEEK_BASE_URL=https://api.deepseek.com/v1` in `backend/.env`.
- **Connection errors**: Check network; ensure `DEEPSEEK_BASE_URL` is correct.

Get an API key at https://platform.deepseek.com/api_keys
