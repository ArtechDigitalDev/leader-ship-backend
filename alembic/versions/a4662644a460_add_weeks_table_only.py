"""add_weeks_table_only

Revision ID: a4662644a460
Revises: 8648f8053158
Create Date: 2025-09-17 16:59:18.027729

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a4662644a460'
down_revision: Union[str, None] = '793e0436f3dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create weeks table
    op.create_table('weeks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('topic', sa.String(), nullable=False),
        sa.Column('week_number', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('intro', sa.Text(), nullable=False),
        sa.Column('weekly_challenge', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_weeks_id'), 'weeks', ['id'], unique=False)


def downgrade() -> None:
    # Drop weeks table
    op.drop_index(op.f('ix_weeks_id'), table_name='weeks')
    op.drop_table('weeks')
