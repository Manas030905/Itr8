# Itr8 — Project Context

> Condensed from the founder's Master Context. This is the "why". For the "what" see
> `PRODUCT_REQUIREMENTS.md`; for the "how" see `ARCHITECTURE.md`.
> If the code and this document disagree about *implementation status*, the code wins.

## What Itr8 is

A platform for **Indian engineering students and student builders** to discover projects,
showcase what they are building, find collaborators, form teams, and eventually access
opportunities (hackathons, internships, startups).

One-liner: *Itr8 is a platform for engineering students to discover projects, find
teammates, collaborate, showcase their work, and connect with opportunities.*

It borrows ideas from GitHub, Reddit, X, Discord, LinkedIn and hackathon platforms, but it is
**not** a clone of any of them. The focus is: **student builders + projects + collaboration.**
Positioning: *a builder network for engineering students.*

## The problem

1. **Finding collaborators.** Students have an idea and some skills but not the complementary ones
   (frontend, backend, ML, design, hardware, DevOps…). No student-focused place to find them.
2. **Fragmented identity.** Work is scattered across GitHub, LinkedIn, WhatsApp, Discord, college groups.
3. **Discoverability.** Good projects never leave a friend group.
4. **Collaboration friction.** Hard to see what a project needs, who to contact, how to contribute.
5. **"What should I build?"** Students don't know which projects or skills would improve their portfolio.

## Users

Primary: engineering students (IIT / NIT / IIIT / other B.Tech / B.E.).
**Pilot: IIIT Raichur only.** Later: other IIITs → NITs → IITs → all engineering colleges.

## Strategy

- **Cold start is the main risk.** A collaboration network with 10 users is useless. Launch in one
  college, get a dense active community, validate, then expand.
- **College as distribution channel.** Professors/clubs/hackathon teams can bring cohorts in
  (e.g. a professor collecting project submissions through Itr8 — always transparently
  branded as Itr8).
- **Validate before monetizing.** Monetization ideas (premium profiles, hiring, sponsored projects,
  hackathon sponsorship, college partnerships) are long-term and must not drive the MVP.

## The core loop (what the MVP must prove)

```
Student → Builder Profile → Discover Projects/Builders → Create/Join Project
        → Team Requirement → Application → Collaboration
```

Early success questions: Do students use it? Create projects? Discover each other? *Actually
collaborate?* Does it solve a real problem? Can the community grow?

## Principles

1. Preserve the product vision; explain trade-offs before changing anything major.
2. Keep the MVP focused. If a feature doesn't help students **build, discover, collaborate, or
   grow**, it is probably not MVP.
3. Simple + maintainable + scalable-enough beats complex + theoretically scalable.
4. **No AI for its own sake.** Every AI feature must name the user problem it solves
   (e.g. "teammate matcher that recommends complementary collaborators", not "AI chatbot").
5. Security and privacy from day one (students are the users; some may be minors).
6. Docs are a source of truth; update them when decisions change.

## Explicitly out of scope for the MVP

AI features and AI chat, feed, chat/messaging, communities, opportunities board, hackathon hub,
startup corner, monetization, learning paths, skill-gap analysis, advanced recommendations.
(All remain in the long-term vision; see `DEVELOPMENT_ROADMAP.md`.)

## Long-term vision (for orientation only)

Idea → Team → Build → Showcase → Opportunity → Startup — the platform follows a student's
entire builder journey, becoming "digital infrastructure for student builders".

Working tagline (not locked): *Where Student Builders Find Their Team.*
