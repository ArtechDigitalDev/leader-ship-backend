"""make_weekly_challenge_optional

Revision ID: eb9632fbecac
Revises: a4662644a460
Create Date: 2025-09-17 17:20:17.941512

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eb9632fbecac'
down_revision: Union[str, None] = 'a4662644a460'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make weekly_challenge column nullable
    op.alter_column('weeks', 'weekly_challenge',
                   existing_type=sa.JSON(),
                   nullable=True)


def downgrade() -> None:
    # Make weekly_challenge column non-nullable (this will fail if there are NULL values)
    op.alter_column('weeks', 'weekly_challenge',
                   existing_type=sa.JSON(),
                   nullable=False)
