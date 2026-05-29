"""add tag column to wins

Revision ID: 001
Revises:
Create Date: 2025-05-29

"""
from typing import Sequence, Union
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Safe to run on existing DBs that already have this column (IF NOT EXISTS)
    op.execute("ALTER TABLE wins ADD COLUMN IF NOT EXISTS tag VARCHAR(50)")


def downgrade() -> None:
    op.execute("ALTER TABLE wins DROP COLUMN IF EXISTS tag")
