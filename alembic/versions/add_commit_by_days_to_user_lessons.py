"""add commit_by_days to user_lessons

Revision ID: e7f84fc9e2a1
Revises: 25d253d8d93c
Create Date: 2025-01-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e7f84fc9e2a1'
down_revision: Union[str, None] = '25d253d8d93c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'user_lessons',
        sa.Column('commit_by_days', sa.Integer(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('user_lessons', 'commit_by_days')
