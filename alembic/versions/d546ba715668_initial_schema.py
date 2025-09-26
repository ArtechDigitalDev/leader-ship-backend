"""initial_schema

Revision ID: d546ba715668
Revises: 
Create Date: 2025-09-26 08:31:41.801780

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd546ba715668'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=False),
        sa.Column('mobile_number', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('role', sa.Enum('PARTICIPANT', 'COACH', 'ADMIN', name='userrole'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=True),
        sa.Column('is_email_verified', sa.Boolean(), nullable=True),
        sa.Column('terms_accepted', sa.Boolean(), nullable=True),
        sa.Column('requested_role', sa.Enum('PARTICIPANT', 'COACH', 'ADMIN', name='userrole'), nullable=True),
        sa.Column('role_request_status', sa.Enum('PENDING', 'APPROVED', 'REJECTED', name='rolerequeststatus'), nullable=True),
        sa.Column('role_request_reason', sa.Text(), nullable=True),
        sa.Column('role_requested_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('role_approved_by', sa.Integer(), nullable=True),
        sa.Column('role_approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_mobile_number'), 'users', ['mobile_number'], unique=True)

    

    # Create assessments table
    op.create_table('assessments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create weeks table
    op.create_table('weeks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('topic', sa.String(), nullable=False),
        sa.Column('week_number', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('intro', sa.Text(), nullable=False),
        sa.Column('weekly_challenge', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create daily_lessons table
    op.create_table('daily_lessons',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('week_id', sa.Integer(), nullable=False),
        sa.Column('day_number', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('daily_tip', sa.JSON(), nullable=False),
        sa.Column('swipe_cards', sa.JSON(), nullable=False),
        sa.Column('scenario', sa.JSON(), nullable=False),
        sa.Column('go_deeper', sa.JSON(), nullable=False),
        sa.Column('reflection_prompt', sa.Text(), nullable=False),
        sa.Column('leader_win', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['week_id'], ['weeks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('daily_lessons')
    op.drop_table('weeks')
    op.drop_table('assessments')
    op.drop_table('users')
