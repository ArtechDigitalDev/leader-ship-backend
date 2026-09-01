"""add_coaching_sessions_table_and_lesson_diagnosis_tags

Revision ID: f3a9c1b7d2e4
Revises: e7f84fc9e2a1
Create Date: 2026-09-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f3a9c1b7d2e4'
down_revision: Union[str, None] = 'e7f84fc9e2a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


scenario_type_enum = sa.Enum(
    'UNDERPERFORMANCE', 'DIFFICULT_CONVERSATION', 'RETENTION_RISK', 'CONFLICT', 'SOMETHING_ELSE',
    name='scenariotype',
)
issue_duration_enum = sa.Enum(
    'JUST_STARTED', 'WEEKS', 'MONTHS', 'LONG_TIME',
    name='issueduration',
)
diagnosis_type_enum = sa.Enum(
    'ACCOUNTABILITY_ISSUE', 'CLARITY_ISSUE', 'CONTEXT_ISSUE',
    name='diagnosistype',
)
action_timing_enum = sa.Enum(
    'TODAY', 'TOMORROW', 'THIS_WEEK',
    name='actiontiming',
)
session_outcome_enum = sa.Enum(
    'GOOD', 'MIXED', 'BAD',
    name='sessionoutcome',
)
session_status_enum = sa.Enum(
    'IN_PROGRESS', 'AWAITING_ACTION', 'COMPLETED', 'ABANDONED',
    name='sessionstatus',
)
coaching_screen_enum = sa.Enum(
    'S1_ENTRY', 'S2_USER_INPUT', 'S3_SPECIFICS', 'S4_DURATION', 'S5_ACCOUNTABILITY',
    'S6_DIAGNOSIS', 'S7_GUIDANCE', 'S8_CONVERSATION_BUILDER', 'S9_CONVERSATION_STEPS',
    'S10_COMMITMENT', 'S11_FOLLOW_UP_SCHEDULED', 'S12_CHECK_IN', 'S13_REFLECTION', 'S14_LEARNING',
    name='coachingscreen',
)


def upgrade() -> None:
    op.create_table(
        'coaching_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('scenario_type', scenario_type_enum, nullable=True),
        sa.Column('raw_input_text', sa.Text(), nullable=True),
        sa.Column('problem_detail', sa.Text(), nullable=True),
        sa.Column('duration', issue_duration_enum, nullable=True),
        sa.Column('accountability_flag', sa.Boolean(), nullable=True),
        sa.Column('is_avoidance_case', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('diagnosis_type', diagnosis_type_enum, nullable=True),
        sa.Column('action_timing', action_timing_enum, nullable=True),
        sa.Column('follow_up_scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('follow_up_sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reminder_sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completion_status', sa.Boolean(), nullable=True),
        sa.Column('outcome', session_outcome_enum, nullable=True),
        sa.Column('current_screen', coaching_screen_enum, nullable=False, server_default='S1_ENTRY'),
        sa.Column('status', session_status_enum, nullable=False, server_default='IN_PROGRESS'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_coaching_sessions_id'), 'coaching_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_coaching_sessions_user_id'), 'coaching_sessions', ['user_id'], unique=False)
    op.create_index(op.f('ix_coaching_sessions_status'), 'coaching_sessions', ['status'], unique=False)

    # Diagnosis tags on lessons — used by coaching-session recommendations (S14)
    op.add_column('daily_lessons', sa.Column('diagnosis_tags', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('daily_lessons', 'diagnosis_tags')

    op.drop_index(op.f('ix_coaching_sessions_status'), table_name='coaching_sessions')
    op.drop_index(op.f('ix_coaching_sessions_user_id'), table_name='coaching_sessions')
    op.drop_index(op.f('ix_coaching_sessions_id'), table_name='coaching_sessions')
    op.drop_table('coaching_sessions')

    bind = op.get_bind()
    for enum in (
        coaching_screen_enum,
        session_status_enum,
        session_outcome_enum,
        action_timing_enum,
        diagnosis_type_enum,
        issue_duration_enum,
        scenario_type_enum,
    ):
        enum.drop(bind, checkfirst=True)
