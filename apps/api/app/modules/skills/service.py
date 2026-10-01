from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modules.skills.models import Skill, UserSkill
from app.modules.skills.schemas import UserSkillsUpdate
from app.modules.users.models import User


def list_skills(db: Session) -> list[Skill]:
    return list(db.scalars(select(Skill).order_by(Skill.name)).all())


def list_my_skills(db: Session, user: User) -> list[UserSkill]:
    stmt = (
        select(UserSkill)
        .where(UserSkill.user_id == user.id)
        .options(selectinload(UserSkill.skill))
        .order_by(UserSkill.skill_id)
    )
    return list(db.scalars(stmt).all())


def replace_my_skills(db: Session, user: User, payload: UserSkillsUpdate) -> list[UserSkill]:
    skill_ids = [item.skill_id for item in payload.skills]
    if len(skill_ids) != len(set(skill_ids)):
        raise ValueError("Duplicate skills are not allowed")

    if skill_ids:
        existing = set(
            db.scalars(select(Skill.id).where(Skill.id.in_(skill_ids))).all()
        )
        if existing != set(skill_ids):
            raise ValueError("One or more selected skills do not exist")

    db.query(UserSkill).filter(UserSkill.user_id == user.id).delete(synchronize_session=False)
    for item in payload.skills:
        db.add(UserSkill(user_id=user.id, skill_id=item.skill_id, level=item.level))
    db.commit()
    return list_my_skills(db, user)
