# Deployment

Three separately configured pieces. Deploying one does NOT deploy the others.

**1. Database (PostgreSQL 14+)** - managed Postgres recommended. Create a database and a user with a strong password. Connection string: `postgresql+psycopg://USER:PASSWORD@HOST:5432/DB`.

**2. API (container from `backend/Dockerfile`)** - environment: `APP_ENV=production`, `DATABASE_URL`, `SECRET_KEY` (>=32 random chars), `COOKIE_SECURE=true`, `ALLOWED_ORIGINS=https://your-frontend-domain`, `LLM_*`. Run `alembic upgrade head` before/at start (the image does this). Serve only over HTTPS. Do not publish port 8000 publicly if you keep `--forwarded-allow-ips='*'`; otherwise restrict it to your proxy's IP.

**3. Frontend (static build from `frontend/`)** - `npm ci && npm run build` produces `dist/`. The simplest setup is the provided nginx image, which proxies `/api/` to the API so browser and API share an origin (cookies work, no cross-site CORS). If you host the static files on a separate domain (Netlify, Vercel, S3), you MUST proxy/rewrite `/api/*` to the API on that same domain; the app uses same-origin relative URLs and `SameSite=Lax` cookies and will not authenticate across different sites.

Migrations: `docker compose exec backend alembic upgrade head` (also run on container start). Rollback one step: `alembic downgrade -1`.
Backups: schedule `pg_dump` on the database. Content versions are stored in the DB and grow over time.
