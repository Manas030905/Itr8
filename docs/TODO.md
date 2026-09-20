# TODO

P0 = critical · P1 = high · P2 = medium · P3 = low.
Update this file whenever work is finished or discovered. (Last updated: end of Milestone 1 build.)

## Founder actions (cannot be done by code)

- [ ] **P0** Create a Google Cloud OAuth client (Web app). Redirect URI = `{FRONTEND_URL}/api/v1/auth/google/callback` (one for local, one for staging).
- [ ] **P0** Test sign-in with a real `@iiitr.ac.in` student account. Check whether Google returns an `hd` claim → decide `GOOGLE_REQUIRE_HD` (ADR-006). If student mail is not Google-backed, tell me; we'll pick another login method.
- [ ] **P0** Create hosting accounts and deploy staging (see `docs/DEPLOYMENT.md`): Postgres (Neon/Supabase), API (Render/Railway/Fly), web (Vercel). Set env vars from `.env.example`.
- [ ] **P1** Create a Sentry project; set `SENTRY_DSN`.
- [ ] **P1** Student-council accounts use `@students.iiitr.ac.in` and are **not** allowed in the pilot. If they should be, set `ALLOWED_EMAIL_DOMAINS=iiitr.ac.in,students.iiitr.ac.in` (config only, no code change).

## Milestone 2 — Profiles & skills (next)

- [ ] **P0** Skills taxonomy (seeded) + `user_skills` with level
- [ ] **P0** Usernames + public profile `/u/[username]` (ADR-009)
- [ ] **P0** Profile fields: interests, availability, looking-for, GitHub/LinkedIn URLs
- [ ] **P1** GitHub OAuth (verified identity)
- [ ] **P2** Profile completeness indicator

## Hardening (before pilot; Milestone 7 unless noted)

- [ ] **P1** Rate limiting (auth, writes) — in-memory is fine for a single instance
- [ ] **P1** Content-Security-Policy + security headers on the API responses
- [ ] **P1** Dependabot + `pip-audit` / `npm audit` in CI
- [ ] **P1** Privacy policy, terms (incl. age line), account deletion endpoint (DPDP Act; get legal review)
- [ ] **P1** Frontend Sentry (`@sentry/nextjs`)
- [ ] **P1** Postgres backup schedule + tested restore
- [ ] **P2** Prune expired sessions on a schedule
- [ ] **P2** Playwright e2e for the core loop (2–3 tests) once projects/applications exist
- [ ] **P2** Sliding session expiry / "log out everywhere"
- [ ] **P3** Structured JSON logging + request IDs

## Known limitations of Milestone 1

- **Docker images were never built or run by Docker.** The build sandbox cannot pull images (registry blocked). `docker compose config` validates, and each Dockerfile step was replayed outside Docker (frozen dependency install, migration on an empty DB, standalone web build, smoke test against that stack), but the first real `docker compose up --build` is unproven. One real bug (config path crash inside `/app`) was found this way, so expect the possibility of others.
- **CI has never run.** The repo has not been pushed to GitHub; `.github/workflows/ci.yml` parses but is unexecuted. Every command in it was run locally and passes.
- No real Google round-trip was possible in the sandbox; the OAuth callback logic is tested with the token exchange mocked.
- Faculty/staff with `@iiitr.ac.in` can also sign in (ADR-006).
