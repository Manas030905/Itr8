# Database Schema

PostgreSQL 16. Managed with Alembic (`apps/api/migrations`). **Never edit the database by hand.**
The migrations are the source of truth; this file is a readable summary.

## Conventions

- UUID primary keys (`gen_random_uuid()` server default).
- `created_at` / `updated_at` are `timestamptz`, default `now()`.
- Emails are stored lowercase (enforced by a CHECK constraint).
- Constraint/index names come from a naming convention in `app/db/base.py`, so migrations are
  deterministic.
- Soft delete via `deleted_at` on users (and, later, projects).

## Milestone 1 — implemented

### `colleges`
The allowlist of institutions. Adding a college = inserting a row (no code change).

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| name | text | "IIIT Raichur" |
| slug | text unique | `iiit-raichur` |
| email_domains | text[] | `{iiitr.ac.in}`; lowercase, exact match |
| created_at | timestamptz | |

Seeded by the initial migration with IIIT Raichur.

### `users`
| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| email | text unique | lowercase (CHECK) |
| name | text | display name; editable |
| avatar_url | text null | from Google |
| college_id | uuid FK → colleges | resolved from email domain at first login |
| role | text | `student` (default) \| `admin` (CHECK) |
| deleted_at | timestamptz null | soft delete; deleted users cannot sign in |
| created_at, updated_at | timestamptz | |

### `oauth_accounts`
| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| user_id | uuid FK → users (cascade) | |
| provider | text | `google` (GitHub added in Milestone 2) |
| provider_user_id | text | Google `sub` |
| created_at | timestamptz | |

Unique: `(provider, provider_user_id)` and `(user_id, provider)`.

### `sessions`
| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| user_id | uuid FK → users (cascade) | |
| token_hash | text unique | SHA-256 hex of the cookie token. Raw token is never stored. |
| created_at, expires_at, last_seen_at | timestamptz | |

Logout deletes the row. Expired rows are ignored on lookup and pruned at login.

### `profiles`
One row per user (created at first login).

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| user_id | uuid FK → users, unique (cascade) | |
| branch | text null | 1–80 chars |
| year | smallint null | CHECK 1–6 |
| bio | text null | ≤ 500 chars |
| onboarding_completed_at | timestamptz null | set **server-side** once name+branch+year exist |
| created_at, updated_at | timestamptz | |

## Planned (not yet migrated)

| Milestone | Tables / columns |
|-----------|------------------|
| 2 | `profiles.username` (+ availability, looking_for, github_url, linkedin_url), `skills`, `user_skills` (level), GitHub in `oauth_accounts` |
| 3 | `projects`, `project_skills`, `project_members` |
| 4 | `team_requirements`, `applications` (unique per requirement+applicant), contact-reveal field on projects |
| 6 | `notifications`, `reports` |
| Later | posts/comments/likes, communities, opportunities, invitations, embeddings (`pgvector`) |

## Relationships (current)

```
colleges 1───* users 1───1 profiles
                 │
                 ├───* oauth_accounts
                 └───* sessions
```
