# Builder Hub

A platform for Indian engineering students to discover projects, find collaborators, form teams
and showcase what they build. **Pilot: IIIT Raichur.**

> Status: **Milestone 1 — Deployed Walking Skeleton with Identity.**
> Sign in with a college Google account → complete a profile → see it saved.

## Repository layout

```
apps/api/    FastAPI + SQLAlchemy + Alembic (modular monolith)
apps/web/    Next.js (App Router) + Tailwind + shadcn-style UI
docs/        Product & engineering docs (start with PROJECT_CONTEXT.md)
scripts/     Helper scripts (OpenAPI export, smoke test)
```

Docs: [Context](docs/PROJECT_CONTEXT.md) · [Requirements](docs/PRODUCT_REQUIREMENTS.md) ·
[Architecture](docs/ARCHITECTURE.md) · [DB schema](docs/DATABASE_SCHEMA.md) ·
[Roadmap](docs/DEVELOPMENT_ROADMAP.md) · [Decisions](docs/DECISIONS.md) · [TODO](docs/TODO.md) ·
[Deployment](docs/DEPLOYMENT.md)

## Run locally

Prerequisites: Python 3.12+, [uv](https://docs.astral.sh/uv/), Node 20+ (22 recommended), PostgreSQL 16 (or Docker).

_(Detailed steps are filled in at the end of the Milestone 1 build.)_
