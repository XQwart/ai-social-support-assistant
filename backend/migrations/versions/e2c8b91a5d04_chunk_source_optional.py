"""chunks: allow source_id and source_url to be NULL for ad-hoc chunks

Revision ID: e2c8b91a5d04
Revises: d1f4a2c8b6e0
Create Date: 2026-04-30 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e2c8b91a5d04"
down_revision: Union[str, Sequence[str], None] = "d1f4a2c8b6e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "chunks",
        "source_id",
        existing_type=sa.Integer(),
        nullable=True,
    )
    op.alter_column(
        "chunks",
        "source_url",
        existing_type=sa.String(length=2048),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "chunks",
        "source_url",
        existing_type=sa.String(length=2048),
        nullable=False,
    )
    op.alter_column(
        "chunks",
        "source_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
