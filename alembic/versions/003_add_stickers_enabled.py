"""add stickers_enabled to users

Revision ID: 003
Revises: 002
Create Date: 2026-05-30
"""
from typing import Union
from alembic import op


revision: str = "003"
down_revision: Union[str, None] = "002"


def upgrade() -> None:
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS stickers_enabled BOOLEAN NOT NULL DEFAULT TRUE")


def downgrade() -> None:
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS stickers_enabled")
