from fastapi import APIRouter

from app.core.deps import CurrentUser, DbSession
from app.modules.profiles import service
from app.modules.profiles.schemas import ProfileUpdate
from app.modules.users.schemas import MeOut, build_me

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("/me", response_model=MeOut)
def get_my_profile(user: CurrentUser) -> MeOut:
    return build_me(user)


@router.patch("/me", response_model=MeOut)
def update_my_profile(payload: ProfileUpdate, user: CurrentUser, db: DbSession) -> MeOut:
    """Update my name, branch, year and bio. Completes onboarding once all are present."""
    return build_me(service.update_my_profile(db, user, payload))
