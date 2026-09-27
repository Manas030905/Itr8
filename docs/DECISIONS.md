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
**Status:** ~~Accepted~~ **Superseded by ADR-015**
**Decision:** Allowed domains are rows in `colleges`, seeded with IIIT Raichur (`iiitr.ac.in`). Exact-domain match, lowercase.
**Consequences:** Adding a college needs no code change. Subdomains (e.g. `students.iiitr.ac.in`) are **not** matched automatically — add them to the array if they exist.
**Verification:** `iiitr.ac.in` confirmed as the institute's official mail domain from iiitr.ac.in (`info@iiitr.ac.in`, `queries@iiitr.ac.in`). Not publicly verifiable: whether *student* mailboxes use exactly this domain and are Google-backed.

## ADR-006 — Domain check = verified email + domain match; `hd` claim optional
**Status:** Accepted (needs real-account confirmation)
**Context:** Google's `hd` claim proves a Google Workspace-managed account, but only works if IIIT Raichur mail runs on Google Workspace, which is unknown.
**Decision:** Require `email_verified` and exact domain match. `GOOGLE_REQUIRE_HD` (default false) additionally requires `hd`. `ALLOWED_TEST_EMAILS` allows named exceptions.
**Update (founder):** student accounts are shown as `@iiitr.ac.in`; student-council accounts use `@students.iiitr.ac.in`, which the pilot does **not** allow. Enabling it is a config change (ADR-015).
**Consequences:** If student mail is not Google-backed, students would need a Google account registered with their college address (works, but clunky) — then consider Microsoft/email-OTP login. Faculty/staff on the same domain are also admitted. **Founder action:** test with a real student account before pilot; if `hd` is present, set `GOOGLE_REQUIRE_HD=true`.

## ADR-007 — Sync SQLAlchemy 2.0 + psycopg 3
**Status:** Accepted
**Decision:** Sync engine/sessions; async only for Authlib's redirect/callback, with DB work in the threadpool.
**Consequences:** Simpler code and tests; revisit only if profiling shows a real bottleneck.

## ADR-008 — Authlib for the OAuth flow (explicit Google endpoints)
**Status:** Accepted
**Decision:** Authlib's Starlette client handles state, nonce, PKCE (S256) and ID-token validation. Google endpoints are configured explicitly (no discovery fetch at startup).
**Consequences:** Less hand-rolled security code; no startup network dependency. OAuth state is kept in a short-lived signed cookie (`itr8_oauth`), separate from the app session.

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

## ADR-015 — Allowed email domains come from `ALLOWED_EMAIL_DOMAINS` (supersedes ADR-005)
**Status:** Accepted (founder decision)
**Context:** The founder does not want the domain hard-coded in application logic and wants more domains addable later.
**Decision:** `ALLOWED_EMAIL_DOMAINS` (comma-separated, lowercase, exact match, no wildcards). No built-in default: empty means nobody can sign in, and non-local environments refuse to start with it empty. Invalid entries (`*`, `*.x.com`, bare hostnames) fail at startup. The `colleges` table keeps identity only (name, slug); `email_domains` was removed and migration `0001` was edited in place, which was safe because nothing had been deployed.
**Consequences:** One source of truth, changeable without a migration or code change. Every allowed domain maps to `DEFAULT_COLLEGE_SLUG`; when a second college is added we need a domain→college mapping (a small migration plus config format), noted for a later milestone.

## ADR-016 — Pin both `iss` and `aud` when validating the Google ID token
**Status:** Accepted
**Context:** Testing with locally forged tokens showed Authlib's defaults reject bad signatures, expiry and nonce, but do **not** check the issuer, and a token with a foreign `aud` and `azp` set to our client id was accepted. Not exploitable today (it needs a validly signed Google token), but "our client id must be in `aud`" is baseline OIDC.
**Decision:** Pass `claims_options` requiring `iss` in Google's two issuer forms and `aud` containing our client id. Tests assert the exact error class for each forgery (wrong issuer, audience, nonce, expiry, missing claims, unknown signing key) so they cannot pass for the wrong reason.
**Consequences:** Multi-audience tokens that include us are still accepted.

## ADR-017 — Docker/Compose conventions
**Status:** Accepted (unproven under real Docker; see TODO)
**Decision:** API image has `dev` (adds pytest/ruff/mypy; used by Compose) and `prod` (default, no dev tools) targets. A fresh clone runs with **no `.env`**: Compose supplies local-safe defaults (`ALLOWED_EMAIL_DOMAINS=iiitr.ac.in`, `DEV_LOGIN_ENABLED=true`, Google unset, so sign-in fails safe with a clear message). Next.js `standalone` output is opt-in via `NEXT_OUTPUT=standalone` (set only in the Docker build) so `npm start` keeps working. `API_INTERNAL_URL` is a build-time arg because Next bakes rewrite destinations in at build. The test database is created by `scripts/init-db.sql` on first volume init.
**Consequences:** `DEV_LOGIN_ENABLED` defaulting to true is acceptable only because Compose forces `ENVIRONMENT=local`, and the API independently ignores it elsewhere. A bug found while replaying the image: `config.py` indexed `Path.parents[4]`, which does not exist at `/app/app/core/config.py` and would have crashed the container at import; it now falls back safely.

## ADR-018 — Product renamed from "Builder Hub" to "Itr8"
**Status:** Accepted (founder decision)
**Context:** Founder decided on the name Itr8 partway through Milestone 1, after initial branding work as "Builder Hub".
**Decision:** Renamed everywhere: UI copy (logo, page titles, meta description, landing/login copy), docs, `README.md`, `CLAUDE.md`, package names (`itr8-api`, `itr8-web`), the Postgres role/database names (`itr8`, `itr8_test`), the Docker Compose project name, and the session/OAuth cookie names (`itr8_session`, `itr8_oauth`). Left untouched: feature/persona words that aren't the brand ("Builder Profile", "student builders", "Team Finder"), and past git commit messages (history, not current state).
**Consequences:** Full test suite (130 backend, 19 frontend), lint, mypy, typecheck, production build, live smoke test, and a real-browser check were all re-run after the rename and pass. Anyone with an existing local `.env` or database from before this change needs to update `ALLOWED_TEST_EMAILS`-style values are unaffected, but `DATABASE_URL`/`TEST_DATABASE_URL` and the Postgres role must be updated to `itr8`/`itr8_dev` (or their own custom values) — see updated `.env.example`.
