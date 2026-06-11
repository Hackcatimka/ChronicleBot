"""add portrait to users

Revision ID: 006
Revises: 005
Create Date: 2026-06-11
"""
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "006"
down_revision: Union[str, None] = "005"


def upgrade() -> None:
    op.add_column("users", sa.Column("portrait", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "portrait")
