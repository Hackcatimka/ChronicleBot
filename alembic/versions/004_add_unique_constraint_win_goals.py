"""add unique constraint to win_goals

Revision ID: 004
Revises: 003
Create Date: 2026-06-01
"""
from typing import Union
from alembic import op


revision: str = "004"
down_revision: Union[str, None] = "003"


def upgrade() -> None:
    op.execute("""
        DELETE FROM win_goals wg1
        USING win_goals wg2
        WHERE wg1.id > wg2.id
          AND wg1.win_id = wg2.win_id
          AND wg1.goal_id = wg2.goal_id
    """)
    op.create_unique_constraint("uq_win_goals_win_goal", "win_goals", ["win_id", "goal_id"])


def downgrade() -> None:
    op.drop_constraint("uq_win_goals_win_goal", "win_goals", type_="unique")
