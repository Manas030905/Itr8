# Development Roadmap

Each feature follows: requirement → design → implementation → testing → bug fixing → docs.
Estimates are rough dev-days for 1–2 part-time developers with AI assistance.

| # | Milestone | Scope | Est. | Status |
|---|-----------|-------|------|--------|
| 0 | Architecture | Phase 0 design, decisions | — | ✅ approved |
| 1 | **Walking skeleton with identity** | Monorepo, CI, Docker, Google login (IIIT Raichur domain), sessions, onboarding, profile view/edit, deployment configs | 8–12 | 🚧 code complete; staging deploy needs founder accounts |
| 2 | **Profiles & skills** | Skills taxonomy, skill levels, interests, availability, looking-for, usernames, public profile, GitHub connect | 6–9 | ⬜ |
| 3 | **Projects** | Create/edit, public page, status, tech stack, links | 4–6 | ⬜ |
| 4 | **Team requirements & applications** | Open roles, apply/accept/reject/withdraw, contact reveal | 5–8 | ⬜ |
| 5 | **Discovery** | Search + filters for projects/people; rule-based recommendations | 6–10 | ⬜ |
| 6 | **Notifications, moderation, analytics** | In-app + email notifications, reports, admin, PostHog | 6–9 | ⬜ |
| 7 | **Hardening & pilot prep** | Security pass, rate limiting, CSP, backup-restore test, privacy policy, seed 15–20 real projects, onboard first 20–30 users | 4–6 | ⬜ |
| — | **IIIT Raichur pilot** | Measure activation, projects created, collaboration requests, team formations, retention | — | ⬜ |

## Post-pilot (only after the core loop is validated)

AI project assistant → skill-gap analysis → AI teammate matching (embeddings) → personalised
recommendations → communities → hackathon hub → opportunities board → startup corner →
company/college partnerships and monetization.

## Rules of the road

- Ship each milestone to staging and click through it before starting the next.
- Cap build time before real students touch the product. Cut scope, not the pilot date.
- Seed content is a launch requirement, not a nice-to-have.
