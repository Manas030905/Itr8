# syntax=docker/dockerfile:1
# Stages: base -> dev (adds test/lint tools; used by docker compose) -> prod (default target).
FROM python:3.12-slim AS base
COPY --from=ghcr.io/astral-sh/uv:0.11.7 /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY pyproject.toml uv.lock ./

FROM base AS dev
RUN uv sync --frozen --no-install-project
COPY . .
RUN useradd --create-home app && chown -R app:app /app
USER app
EXPOSE 8000
# Apply migrations, then serve. Safe to run on every start (Alembic is idempotent).
CMD ["sh", "-c", "uv run --no-sync alembic upgrade head && exec uv run --no-sync uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

FROM base AS prod
RUN uv sync --frozen --no-dev --no-install-project
COPY . .
RUN useradd --create-home app && chown -R app:app /app
USER app
EXPOSE 8000
CMD ["sh", "-c", "uv run --no-sync alembic upgrade head && exec uv run --no-sync uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
