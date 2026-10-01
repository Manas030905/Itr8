from fastapi import APIRouter, HTTPException

from app.core.deps import CurrentUser, DbSession
from app.modules.skills import service
from app.modules.skills.schemas import SkillOut, UserSkillOut, UserSkillsUpdate

router = APIRouter(prefix="/skills", tags=["skills"])


@router.get("", response_model=list[SkillOut])
def get_skills(db: DbSession) -> list[SkillOut]:
    return service.list_skills(db)


@router.get("/me", response_model=list[UserSkillOut])
def get_my_skills(user: CurrentUser, db: DbSession) -> list[UserSkillOut]:
    return service.list_my_skills(db, user)


@router.put("/me", response_model=list[UserSkillOut])
def replace_my_skills(
    payload: UserSkillsUpdate, user: CurrentUser, db: DbSession
) -> list[UserSkillOut]:
    try:
        return service.replace_my_skills(db, user, payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
