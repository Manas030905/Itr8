from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text

from app.core.deps import DbSession

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def liveness() -> dict[str, str]:
    """Process is up. No dependencies checked (use for platform liveness probes)."""
    return {"status": "ok"}


@router.get("/ready")
def readiness(db: DbSession) -> dict[str, str]:
    """Process can reach the database."""
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable"
        ) from exc
    return {"status": "ok", "database": "ok"}
