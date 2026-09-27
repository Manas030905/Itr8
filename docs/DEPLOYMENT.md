# Deployment

**Status: configuration written, NOT yet deployed.** Deploying needs accounts only the founder
can create. Everything below is a checklist for the first staging deploy. Nothing here has been
executed against a real host — expect to fix small things on first run and record them in
`DECISIONS.md`.

## Topology

```
Vercel (apps/web) ──/api/* rewrite──► Render / Railway / Fly (apps/api, Docker) ──► Managed Postgres
```

The browser only talks to the web origin. That origin is `FRONTEND_URL` for the API, and the
Google OAuth redirect URI is `{FRONTEND_URL}/api/v1/auth/google/callback`.

## 1. Postgres
Create a managed Postgres 16 (Neon, Supabase, or the API host's own). Copy the connection string
into the API's `DATABASE_URL` (`postgres://` / `postgresql://` are accepted and converted).
Turn on automated backups and do one test restore before the pilot.

## 2. API (Docker, `apps/api/Dockerfile`, default `prod` target)
- Root/context directory: `apps/api`. Health check path: `/api/v1/health/ready`.
- The container runs `alembic upgrade head` and then starts uvicorn on `$PORT` (or 8000).
- Required env vars (the app **refuses to start** in staging/production if any are wrong):

| Variable | Value |
|---|---|
| `ENVIRONMENT` | `staging` (or `production`) |
| `DATABASE_URL` | from step 1 |
| `FRONTEND_URL` | the public https URL of the web app, no trailing slash |
| `SECRET_KEY` | `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | from Google Cloud (step 4) |
| `ALLOWED_EMAIL_DOMAINS` | `iiitr.ac.in` |
| `DEFAULT_COLLEGE_SLUG` | `iiit-raichur` |
| `SENTRY_DSN` | optional |

Do **not** set `DEV_LOGIN_ENABLED` (startup fails if it is true outside local).

## 3. Web (Vercel)
- Root directory: `apps/web`. Framework: Next.js.
- Env vars (needed at **build** and runtime — rewrites are baked in at build):
  `API_INTERNAL_URL` = the API's public URL, e.g. `https://itr8-api-staging.onrender.com`.
- Redeploy the web app whenever the API URL changes.
- Cloudflare Pages needs extra care for Next.js rewrites; prefer Vercel for now (ADR-004).

## 4. Google OAuth client
Google Cloud Console → APIs & Services → Credentials → Create OAuth client ID → Web application.
- Authorised redirect URI: `https://<staging-web-host>/api/v1/auth/google/callback`
  (add `http://localhost:3000/api/v1/auth/google/callback` for local use).
- Consent screen: set user type; while in "Testing", add testers. For real students you will
  eventually need to publish the app. Scopes needed: `openid email profile` (non-sensitive).

## 5. First-deploy verification (~10 minutes)
1. `GET https://<api>/api/v1/health/ready` → `{"status":"ok","database":"ok"}`.
2. Visit the web URL → landing page loads with fonts.
3. Sign in with a real `@iiitr.ac.in` account → onboarding → save → land on `/me`.
4. Refresh `/me` → data persists. Sign out → `/me` redirects to `/login`.
5. Sign in with a non-college Google account → clear "not on the pilot list" message.
6. In Google's response, check whether an `hd` claim exists for student accounts (ADR-006).
7. Run the smoke test against staging: `uv run --project apps/api python scripts/smoke_test.py https://<web>`
   (it needs `dev-login`, which is disabled outside local, so the smoke test only fully applies
   to local/Docker; on staging do steps 1–6 by hand).

## Auto-deploy from `main`
Connect the GitHub repo in Render/Railway (API) and Vercel (web) and enable auto-deploy on `main`.
CI (`.github/workflows/ci.yml`) is the gate: only merge when green.
