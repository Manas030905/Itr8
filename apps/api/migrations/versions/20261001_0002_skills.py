"""skills and user skills

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-01
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SKILLS = [
    ("Python", "python"),
    ("C++", "cpp"),
    ("Java", "java"),
    ("JavaScript", "javascript"),
    ("TypeScript", "typescript"),
    ("React", "react"),
    ("Next.js", "nextjs"),
    ("Node.js", "nodejs"),
    ("FastAPI", "fastapi"),
    ("Django", "django"),
    ("Machine Learning", "machine-learning"),
    ("Deep Learning", "deep-learning"),
    ("Generative AI", "generative-ai"),
    ("Data Science", "data-science"),
    ("Computer Vision", "computer-vision"),
    ("NLP", "nlp"),
    ("SQL", "sql"),
    ("PostgreSQL", "postgresql"),
    ("Docker", "docker"),
    ("AWS", "aws"),
    ("Git", "git"),
    ("UI/UX", "ui-ux"),
    ("Cybersecurity", "cybersecurity"),
    ("Flutter", "flutter"),
]


def upgrade() -> None:
    op.create_table(
        "skills",
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_skills")),
        sa.UniqueConstraint("slug", name=op.f("uq_skills_slug")),
    )
    op.create_table(
        "user_skills",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("skill_id", sa.UUID(), nullable=False),
        sa.Column("level", sa.String(length=20), server_default="beginner", nullable=False),
        sa.CheckConstraint(
            "level IN ('beginner', 'intermediate', 'advanced')",
            name=op.f("ck_user_skills_level_valid"),
        ),
        sa.ForeignKeyConstraint(
            ["skill_id"], ["skills.id"], name=op.f("fk_user_skills_skill_id_skills"), ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_user_skills_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("user_id", "skill_id", name=op.f("pk_user_skills")),
    )

    skills = sa.table(
        "skills",
        sa.column("name", sa.Text()),
        sa.column("slug", sa.String(length=80)),
    )
    op.bulk_insert(skills, [{"name": name, "slug": slug} for name, slug in SKILLS])


def downgrade() -> None:
    op.drop_table("user_skills")
    op.drop_table("skills")
