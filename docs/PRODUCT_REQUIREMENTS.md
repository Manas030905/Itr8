# Product Requirements (MVP)

Status legend: ✅ done · 🚧 in progress · ⬜ not started

Priorities: **P0** = core loop, must ship · **P1** = needed for a good pilot · **P2** = post-pilot.

## Personas

- **Builder (student).** Has skills/ideas; wants teammates or a project to join.
- **Project owner.** A builder who created a project and needs specific roles filled.
- **Admin (pilot team).** Moderates reports, watches pilot metrics. (P1)

## Access rules (pilot)

- Sign-in with **Google only**. No passwords.
- Only accounts whose verified email domain belongs to an entry in the `colleges` table may sign in.
  Seeded college: **IIIT Raichur — `iiitr.ac.in`**.
- Optional exact-email allowlist (`ALLOWED_TEST_EMAILS`) for testers outside the domain.
- Faculty/staff also use `iiitr.ac.in`; the pilot allows them (see ADR-006). Revisit if it matters.

## Requirements

| ID | Requirement | Priority | Milestone | Status |
|----|-------------|----------|-----------|--------|
| AUTH-1 | Sign in with Google; only allowed college domains admitted | P0 | 1 | ⬜ |
| AUTH-2 | Secure server-side sessions; logout revokes the session server-side | P0 | 1 | ⬜ |
| AUTH-3 | Protected API routes return 401 without a valid session | P0 | 1 | ⬜ |
| PROF-1 | Onboarding: name, branch, year, short bio | P0 | 1 | ⬜ |
| PROF-2 | View and edit my profile | P0 | 1 | ⬜ |
| AUTH-4 | GitHub connect (verified GitHub identity) | P1 | 2 | ⬜ |
| PROF-3 | Skills (curated taxonomy + level), interests, availability, looking-for, GitHub/LinkedIn links | P0 | 2 | ⬜ |
| PROF-4 | Public profile page `/u/[username]` | P0 | 2 | ⬜ |
| PROJ-1 | Create/edit project: title, problem, description, status, tech stack, repo/demo links | P0 | 3 | ⬜ |
| PROJ-2 | Public project page (shareable link) | P0 | 3 | ⬜ |
| TEAM-1 | Owner posts open roles (skills, hours/week, duration) | P0 | 4 | ⬜ |
| TEAM-2 | Builders apply with a message; owner accepts/rejects; applicant can withdraw | P0 | 4 | ⬜ |
| TEAM-3 | On acceptance, owner's chosen contact channel is revealed to the new member | P0 | 4 | ⬜ |
| DISC-1 | Discover projects and people with search + filters | P0 | 5 | ⬜ |
| DISC-2 | Rule-based recommendations (projects for my skills; builders for this role) | P1 | 5 | ⬜ |
| NOTIF-1 | In-app notifications for applications and decisions | P0 | 6 | ⬜ |
| NOTIF-2 | Email notifications | P1 | 6 | ⬜ |
| MOD-1 | Report content/user; admin review | P1 | 6 | ⬜ |
| ANLY-1 | Product analytics for pilot metrics | P1 | 6 | ⬜ |

## Milestone 1 — "Deployed Walking Skeleton with Identity"

**Goal:** a real student signs in with their college Google account on a live staging URL,
completes a minimal profile, and sees it saved.

**Acceptance criteria**

1. A user from an allowed domain can sign in, complete onboarding, and see their profile after
   a refresh (on the deployed staging URL — requires the founder's hosting accounts).
2. A user from a disallowed domain is rejected with a clear message.
3. Logout invalidates the session server-side.
4. Protected API routes return 401 without a session.
5. CI is green; a fresh clone runs locally (`docker compose up`, or the manual steps in README).
6. At least one API test covers auth, and one covers profile-update authorization.

**Out of scope for Milestone 1:** GitHub OAuth, skills taxonomy, usernames/public profiles,
projects, discovery, notifications, rate limiting, any AI.

## Pilot success metrics (from Master Context)

Activation (profile completion), projects created, collaboration requests, successful team
formations, 7-/30-day retention, meaningful actions per user. Avoid vanity metrics (raw signups).

## Product gaps to resolve later

- "Actually collaborate" has no in-app chat. Plan: reveal owner's WhatsApp/Discord/email on
  acceptance (TEAM-3). Revisit after pilot feedback.
- Seed content: the pilot needs 15–20 real projects/roles pre-loaded or Discover is empty.
