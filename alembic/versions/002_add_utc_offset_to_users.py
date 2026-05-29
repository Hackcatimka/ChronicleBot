"""add utc_offset to users

Revision ID: 002
Revises: 001
Create Date: 2026-05-29
"""
from typing import Union
from alembic import op


revision: str = "002"
down_revision: Union[str, None] = "001"


def upgrade() -> None:
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS utc_offset INTEGER NOT NULL DEFAULT 0")


def downgrade() -> None:
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS utc_offset")
