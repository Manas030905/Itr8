# Itr8

A platform for Indian engineering students to discover projects, find collaborators, form teams
and showcase what they build. **Pilot: IIIT Raichur.**

> **Status: Milestone 1 — Walking Skeleton with Identity.** Sign in with a college Google account →
> complete a profile → see it saved. Projects, teams and discovery come in later milestones
> (see [roadmap](docs/DEVELOPMENT_ROADMAP.md)).

## Repository layout

```
apps/api/      FastAPI + SQLAlchemy 2.0 + Alembic (modular monolith)  ·  tests in apps/api/tests
apps/web/      Next.js (App Router) + TypeScript + Tailwind v4 + shadcn-style components
docs/          Product & engineering docs (start with PROJECT_CONTEXT.md)
scripts/       export_openapi.py, smoke_test.py, init-db.sql
docker-compose.yml   db + api + web for local development
.github/workflows/   CI
```

Docs: [Context](docs/PROJECT_CONTEXT.md) · [Requirements](docs/PRODUCT_REQUIREMENTS.md) ·
[Architecture](docs/ARCHITECTURE.md) · [DB schema](docs/DATABASE_SCHEMA.md) ·
[Roadmap](docs/DEVELOPMENT_ROADMAP.md) · [Decisions](docs/DECISIONS.md) · [TODO](docs/TODO.md) ·
[Deployment](docs/DEPLOYMENT.md) · [CLAUDE.md](CLAUDE.md) (for AI coding sessions)

## Run locally — option A: Docker (recommended)

Prerequisite: Docker with Compose v2. **No `.env` needed** for a first run.

```bash
docker compose up --build
```

- Web: http://localhost:3000 · API docs: http://localhost:8000/api/docs
- Postgres runs in a container (data persists in the `pgdata` volume; `docker compose down -v` wipes it).
- Migrations run automatically when the API container starts.
- Without Google credentials, use the **Dev sign-in** box on `/login` (enabled by default in
  Compose only). Use any address on an allowed domain, e.g. `you@iiitr.ac.in` — no email is sent.
- Run the tests inside the container: `docker compose exec api uv run --no-sync pytest`
- End-to-end check against the running stack: `make smoke`

> The Compose setup was validated with `docker compose config` and by replaying each Dockerfile
> step outside Docker, but it has **not yet been built and run by Docker itself** (the sandbox it
> was written in cannot pull images). The first CI run (`compose` job) is the real proof; if it
> reveals a problem, fix it and note it in `docs/DECISIONS.md`.

## Run locally — option B: without Docker

Prerequisites: Python 3.12+, [uv](https://docs.astral.sh/uv/), Node 22, PostgreSQL 16.

```bash
cp .env.example .env            # edit if needed; defaults work with the DB below
# create the databases once (user/password match .env.example):
#   CREATE USER itr8 WITH PASSWORD 'itr8_dev' CREATEDB;
#   CREATE DATABASE itr8 OWNER itr8;  CREATE DATABASE itr8_test OWNER itr8;

cd apps/api && uv sync && uv run alembic upgrade head
DEV_LOGIN_ENABLED=true uv run uvicorn app.main:app --reload      # http://localhost:8000

cd apps/web && npm install
DEV_LOGIN_ENABLED=true npm run dev                               # http://localhost:3000
```

The API reads the root `.env`; the web app reads `DEV_LOGIN_ENABLED` from its own process
environment (as above). `make api-dev` / `make web-dev` wrap these commands.

## Real Google sign-in (optional locally)

1. Google Cloud Console → Credentials → *OAuth client ID* → *Web application*.
2. Authorised redirect URI: `http://localhost:3000/api/v1/auth/google/callback`
3. Put `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` in `.env` and restart the API.
4. Only emails on `ALLOWED_EMAIL_DOMAINS` (`iiitr.ac.in` in `.env.example`) can sign in. To test
   with your own Gmail, add it to `ALLOWED_TEST_EMAILS`.

## Tests & checks

```bash
make test          # backend (pytest, real Postgres) + frontend (vitest)
make lint          # ruff, mypy, eslint, tsc
make smoke         # end-to-end against a RUNNING stack, through the web proxy
make generate-api  # after ANY API schema change: re-export OpenAPI + regenerate typed client
```

Backend tests need `TEST_DATABASE_URL` pointing at a database whose name ends in `_test`
(they rebuild its schema from the migrations and wipe its data; they refuse to run otherwise).

## Environment variables

Defined in [`.env.example`](.env.example). The app **refuses to start** outside `ENVIRONMENT=local`
if the security-critical ones are missing or unsafe.

| Variable | Purpose |
|---|---|
| `ENVIRONMENT` | `local` \| `staging` \| `production`. Non-local enables strict checks and Secure cookies |
| `DATABASE_URL` / `TEST_DATABASE_URL` | Postgres URLs (`postgres://` accepted). Test DB name must end `_test` |
| `FRONTEND_URL` | Public web origin (OAuth redirect, CSRF Origin check). https outside local |
| `SECRET_KEY` | Signs the OAuth handshake cookie. ≥ 32 random chars outside local |
| `SESSION_COOKIE_NAME`, `SESSION_TTL_DAYS` | Session cookie name (`itr8_session`) and lifetime (14 days) |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | Google OAuth credentials. Required outside local |
| `GOOGLE_REQUIRE_HD` | Also require Google's `hd` (hosted-domain) claim. Default `false` — see ADR-006 |
| `ALLOWED_EMAIL_DOMAINS` | Comma-separated domains allowed to sign in, e.g. `iiitr.ac.in`. Exact match. **Empty = nobody** |
| `DEFAULT_COLLEGE_SLUG` | College new users join (seeded: `iiit-raichur`) |
| `ALLOWED_TEST_EMAILS` | Extra exact addresses allowed (testing). Empty in production |
| `DEV_LOGIN_ENABLED` | Local-only login shortcut; startup fails if true outside local |
| `SENTRY_DSN` | Optional error reporting (API) |
| `API_INTERNAL_URL` | (web) where Next.js proxies `/api/*`. **Build-time** for rewrites |

## Authentication in one paragraph

Google OAuth 2.0 (authorization code + PKCE + state + nonce) → the API validates the ID token
(signature, issuer, audience, expiry, nonce) and requires a verified email on an allowed domain →
creates/loads the user → issues a random session token stored **hashed** in Postgres and sent as
an HttpOnly, SameSite=Lax (Secure outside local) cookie → logout deletes the session row, so it
is revoked immediately. State-changing requests must come from `FRONTEND_URL` (Origin check).
Details: [ARCHITECTURE.md](docs/ARCHITECTURE.md).
