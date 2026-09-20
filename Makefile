# Convenience shortcuts. Everything here is also documented as plain commands in README.md.
.PHONY: up down reset test lint smoke generate-api api-dev web-dev

up:            ## Start the whole stack in Docker (db + api + web)
	docker compose up --build

down:
	docker compose down

reset:         ## Stop and DELETE the local database volume
	docker compose down -v

test:          ## Run backend + frontend tests
	cd apps/api && uv run pytest
	cd apps/web && npm test

lint:
	cd apps/api && uv run ruff check . && uv run ruff format --check . && uv run mypy app
	cd apps/web && npm run lint && npm run typecheck

generate-api:  ## Re-export OpenAPI and regenerate the typed web client
	cd apps/api && uv run python ../../scripts/export_openapi.py
	cd apps/web && npm run generate:api

smoke:         ## End-to-end check against a RUNNING stack
	uv run --project apps/api python scripts/smoke_test.py

api-dev:
	cd apps/api && uv run alembic upgrade head && uv run uvicorn app.main:app --reload --port 8000

web-dev:
	cd apps/web && DEV_LOGIN_ENABLED=$${DEV_LOGIN_ENABLED:-true} npm run dev
