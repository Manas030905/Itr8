# Decisions Log

Short ADR-style entries. Newest at the bottom. If a decision changes, add a new entry that
supersedes the old one rather than editing history.

Format: **Status** · **Context** · **Decision** · **Consequences**.

---

## ADR-001 — Next.js + FastAPI + PostgreSQL (two deployables)
**Status:** Accepted (founder, Phase 0)
**Context:** Team is strongest in Python; AI/matching features will be Python.
**Decision:** Next.js (App Router, TS, Tailwind, shadcn/ui) frontend; FastAPI + SQLAlchemy + Alembic backend; PostgreSQL.
**Consequences:** Two services to deploy, but no rewrite when AI arrives. Typed API client bridges the gap.

## ADR-002 — Modular monolith, no extra infrastructure
**Status:** Accepted (founder, Phase 0)
**Decision:** One FastAPI service split into modules. No microservices, Redis, queues, GraphQL, Elasticsearch, WebSockets, Kubernetes.
**Consequences:** Background work uses FastAPI background tasks until something needs retries/scheduling.

## ADR-003 — Google OAuth only, no passwords; opaque server-side sessions
**Status:** Accepted (founder, Phase 0)
**Decision:** Google sign-in; random session token in an HttpOnly/Secure/SameSite=Lax cookie; only its SHA-256 is stored server-side.
**Consequences:** Instant revocation and no JWT pitfalls; one DB lookup per authenticated request (fine at this scale).

## ADR-004 — Same-origin API via Next.js rewrite
**Status:** Accepted
**Decision:** Browser calls `/api/*` on the web origin; Next.js proxies to FastAPI (`API_INTERNAL_URL`).
**Consequences:** No CORS, first-party cookies, OAuth redirect URI lives on the web origin. Requires the web host to support rewrites (Vercel does; Cloudflare Pages needs care — see DEPLOYMENT.md).

## ADR-005 — Allowlist is data (`colleges.email_domains`)
**Status:** Accepted
**Decision:** Allowed domains are rows in `colleges`, seeded with IIIT Raichur (`iiitr.ac.in`). Exact-domain match, lowercase.
**Consequences:** Adding a college needs no code change. Subdomains (e.g. `students.iiitr.ac.in`) are **not** matched automatically — add them to the array if they exist.
**Verification:** `iiitr.ac.in` confirmed as the institute's official mail domain from iiitr.ac.in (`info@iiitr.ac.in`, `queries@iiitr.ac.in`). Not publicly verifiable: whether *student* mailboxes use exactly this domain and are Google-backed.

## ADR-006 — Domain check = verified email + domain match; `hd` claim optional
**Status:** Accepted (needs real-account confirmation)
**Context:** Google's `hd` claim proves a Google Workspace-managed account, but only works if IIIT Raichur mail runs on Google Workspace, which is unknown.
**Decision:** Require `email_verified` and exact domain match. `GOOGLE_REQUIRE_HD` (default false) additionally requires `hd`. `ALLOWED_TEST_EMAILS` allows named exceptions.
**Consequences:** If student mail is not Google-backed, students would need a Google account registered with their college address (works, but clunky) — then consider Microsoft/email-OTP login. Faculty/staff on the same domain are also admitted. **Founder action:** test with a real student account before pilot; if `hd` is present, set `GOOGLE_REQUIRE_HD=true`.

## ADR-007 — Sync SQLAlchemy 2.0 + psycopg 3
**Status:** Accepted
**Decision:** Sync engine/sessions; async only for Authlib's redirect/callback, with DB work in the threadpool.
**Consequences:** Simpler code and tests; revisit only if profiling shows a real bottleneck.

## ADR-008 — Authlib for the OAuth flow (explicit Google endpoints)
**Status:** Accepted
**Decision:** Authlib's Starlette client handles state, nonce, PKCE (S256) and ID-token validation. Google endpoints are configured explicitly (no discovery fetch at startup).
**Consequences:** Less hand-rolled security code; no startup network dependency. OAuth state is kept in a short-lived signed cookie (`bh_oauth`), separate from the app session.

## ADR-009 — Usernames deferred to Milestone 2
**Status:** Accepted
**Context:** Milestone 1 onboarding = name, branch, year, bio. Usernames only matter for public profile URLs.
**Decision:** No `username` column yet; added with the public profile page (`/u/[username]`).
**Consequences:** One extra small migration later; avoids collision/validation logic now.

## ADR-010 — Onboarding completion is derived server-side
**Status:** Accepted
**Decision:** `profiles.onboarding_completed_at` is set by the API when name, branch and year are present. Clients cannot set it.
**Consequences:** Route guards can trust it.

## ADR-011 — shadcn/ui components authored by hand
**Status:** Accepted
**Context:** The shadcn CLI pulls from a registry unreachable in the build sandbox.
**Decision:** Components are hand-written following shadcn conventions (cva + tailwind-merge + Radix Slot). `npx shadcn add <x>` works normally on a dev machine.
**Consequences:** None functionally.

## ADR-012 — Local-only `dev-login` (guarded)
**Status:** Accepted — flagged for founder awareness
**Context:** Manual testing and automated smoke tests need to sign in before Google credentials exist.
**Decision:** `POST /api/v1/auth/dev-login` exists only when `ENVIRONMENT=local` **and** `DEV_LOGIN_ENABLED=true`; otherwise the route 404s and the app refuses to start if the flag is set in staging/production.
**Consequences:** Small, guarded testing aid. Remove if you'd rather not have it.

## ADR-013 — Deferred hardening (Milestone 7 / TODO P1)
**Status:** Accepted
**Decision:** Rate limiting, CSP, Dependabot, frontend Sentry, and privacy policy/account deletion are not in Milestone 1.
**Consequences:** Must be done before the pilot opens to real users.

## ADR-014 — Python tooling: uv
**Status:** Accepted
**Decision:** `pyproject.toml` + `uv.lock`; `uv sync` / `uv run`.
**Consequences:** Fast, reproducible installs. `pip install .` also works.
