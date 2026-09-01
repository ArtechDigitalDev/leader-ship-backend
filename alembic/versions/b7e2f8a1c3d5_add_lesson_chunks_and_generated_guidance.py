"""add_lesson_chunks_table_and_generated_guidance

Revision ID: b7e2f8a1c3d5
Revises: f3a9c1b7d2e4
Create Date: 2026-09-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b7e2f8a1c3d5'
down_revision: Union[str, None] = 'f3a9c1b7d2e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'lesson_chunks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('daily_lesson_id', sa.Integer(), nullable=True),
        sa.Column('source_type', sa.String(length=30), nullable=False, server_default='lesson'),
        sa.Column('chunk_type', sa.String(length=30), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', sa.JSON(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['daily_lesson_id'], ['daily_lessons.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_lesson_chunks_id'), 'lesson_chunks', ['id'], unique=False)
    op.create_index(op.f('ix_lesson_chunks_daily_lesson_id'), 'lesson_chunks', ['daily_lesson_id'], unique=False)

    # Cache for RAG-generated S7 guidance on coaching sessions
    op.add_column('coaching_sessions', sa.Column('generated_guidance', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('coaching_sessions', 'generated_guidance')
    op.drop_index(op.f('ix_lesson_chunks_daily_lesson_id'), table_name='lesson_chunks')
    op.drop_index(op.f('ix_lesson_chunks_id'), table_name='lesson_chunks')
    op.drop_table('lesson_chunks')
