# Architecture

Simple, maintainable, scalable-enough for the IIIT Raichur pilot (hundreds to low thousands of
users) and extensible for multi-college expansion and later AI features.

Decision records live in `DECISIONS.md`. Schema details live in `DATABASE_SCHEMA.md`.

## Overview

```
Browser
  │  https://app.example.com  (one origin)
  ▼
Next.js (apps/web) ──── /api/* rewrite (server-side proxy) ────► FastAPI (apps/api)
  │  SSR pages, guards                                              │ modular monolith
  │  (server-side fetch forwards the session cookie)                ▼
  └────────────────────────────────────────────────────────►  PostgreSQL
                                          Google OAuth ◄── FastAPI (auth module)
                          Sentry (errors, optional)
```

**Why one origin.** The browser only ever talks to the Next.js origin. `/api/*` is proxied to
FastAPI. That means: no CORS, first-party cookies, simple `SameSite=Lax` sessions, and the Google
OAuth redirect URI is `{FRONTEND_URL}/api/v1/auth/google/callback`.

## Stack

| Layer | Choice |
|-------|--------|
| Frontend | Next.js (App Router), TypeScript, Tailwind CSS v4, shadcn/ui-style components, react-hook-form + zod |
| API client | Generated from FastAPI's OpenAPI schema (`openapi-typescript` + `openapi-fetch`) |
| Backend | FastAPI, Pydantic v2, SQLAlchemy 2.0 (sync), Alembic, psycopg 3 |
| Database | PostgreSQL 16 |
| Auth | Google OAuth 2.0 / OIDC via Authlib; opaque server-side sessions |
| Tooling | uv (Python), npm (web), ruff, pytest, ESLint, GitHub Actions, Docker |

Deliberately **not** used: microservices, Redis, queues, GraphQL, Elasticsearch, WebSockets,
Kubernetes. Add only when a concrete need appears.

## Backend: modular monolith

One FastAPI service. Code is grouped by domain module; each module owns its
`router.py` (HTTP), `service.py` (business logic), `models.py` (SQLAlchemy), `schemas.py` (Pydantic).
Dependency direction: `router → service → models`. No separate repository layer.

```
apps/api/app/
├── main.py            # app factory, middleware, router registration
├── core/              # config (pydantic-settings), db engine/session, security helpers, deps
├── db/                # Base metadata + naming convention, model registry
└── modules/
    ├── health/        # liveness + readiness
    ├── auth/          # Google OAuth, sessions, login/logout, /auth/me
    ├── users/         # User, College, OAuthAccount models
    └── profiles/      # Profile model + /profiles/me
```

Planned modules (not built yet): `skills`, `projects`, `teams`, `discovery`, `notifications`, `admin`.

### Sync SQLAlchemy

FastAPI runs sync endpoints in a threadpool. At pilot scale this is plenty, tests are simpler, and
there is no async-ORM footgun. The only `async` code is the OAuth redirect/callback (Authlib's
Starlette client is async); its DB work is pushed to the threadpool.

### Sessions

- Login creates a random 256-bit token (`secrets.token_urlsafe(32)`).
- Only the **SHA-256 hash** is stored in `sessions.token_hash`; the raw token lives only in the cookie.
- Cookie `bh_session`: `HttpOnly`, `Secure` (except `ENVIRONMENT=local`), `SameSite=Lax`, `Path=/`.
- Absolute lifetime `SESSION_TTL_DAYS` (default 14). Logout deletes the row → immediate revocation.
- `last_seen_at` is refreshed at most every 5 minutes to avoid a write per request.

### CSRF

State-changing requests (POST/PUT/PATCH/DELETE) carrying a session cookie must have an `Origin`
(or `Referer`) header matching `FRONTEND_URL`; otherwise 403. Combined with `SameSite=Lax`, this
blocks cross-site request forgery without tokens, because there is exactly one legitimate origin.

### Access control

The domain allowlist is **configuration**, not code: `ALLOWED_EMAIL_DOMAINS` (comma-separated,
exact match, no wildcards; empty = nobody can sign in). Login succeeds only if (a) Google says
`email_verified`, and (b) the email's domain is in that list — or the exact email is in
`ALLOWED_TEST_EMAILS`. Optional stricter check: Google `hd` claim (`GOOGLE_REQUIRE_HD`). New users
join the college named by `DEFAULT_COLLEGE_SLUG` (ADR-015). The ID token's signature, issuer,
audience, expiry and nonce are all validated (ADR-016).

### Extensibility for matching / AI (later)

Matching will sit behind a single interface, `score(candidate, requirement) → float + reasons`.
V1 = transparent rule-based scoring; embeddings (`pgvector`) can replace it without API/UI changes.
No AI code exists yet, by decision.

## Frontend

```
apps/web/src/
├── app/
│   ├── layout.tsx, page.tsx (landing), login/
│   └── (app)/            # authenticated area: layout enforces session + onboarding
│       ├── onboarding/, me/, me/edit/
├── components/ui/        # shadcn-style primitives (button, input, label, textarea, select)
├── features/             # feature folders (profiles, auth, …) as the app grows
└── lib/                  # api client (browser + server), auth helpers, utils
```

- **Server-side guard.** `(app)/layout.tsx` calls `GET /api/v1/auth/me` with the incoming cookie:
  401 → `/login`; onboarding incomplete → `/onboarding`.
- **Typed client.** `npm run generate:api` regenerates `src/lib/api/schema.d.ts` from
  `apps/api/openapi.json` (exported by `scripts/export_openapi.py`). CI fails if it is stale.
- **Data fetching.** Server components fetch directly; forms use `fetch` via the typed client.
  TanStack Query is deferred until Discover (Milestone 5) when client caching actually matters.

## Deployment (target)

```
Vercel/Cloudflare (web) ──/api proxy──► Render/Railway/Fly (api, Docker) ──► Managed Postgres (Neon/Supabase)
```

Environments: local (Docker Compose or manual), staging (auto-deploy from `main`), production
(manual/tag). See `docs/DEPLOYMENT.md`. Migrations run on API deploy (`alembic upgrade head`).

## Security checklist (✅ = covered by automated tests, not just implemented)

| Area | Status |
|------|--------|
| No password storage | ✅ (Google only) |
| Hashed session tokens, HttpOnly/Secure/SameSite cookie | ✅ |
| Server-side revocation on logout | ✅ |
| Origin-based CSRF check | ✅ |
| OAuth `state` + `nonce` + PKCE (S256); issuer + audience pinned | ✅ (via Authlib; forged tokens tested) |
| Open-redirect protection on `next` | ✅ |
| Input validation (Pydantic), ORM-only queries | ✅ |
| Secrets only in env; startup validation in non-local envs | ✅ |
| Rate limiting | ⬜ deferred (TODO P1) |
| CSP header | ⬜ deferred (TODO P1) |
| Dependency scanning (Dependabot) | ⬜ TODO P1 |
| Privacy policy / account deletion (DPDP Act) | ⬜ TODO P1, before pilot launch |
