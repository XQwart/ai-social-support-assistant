"""chunks: per-chunk region_code and place_of_work overrides

Revision ID: d1f4a2c8b6e0
Revises: c7a3e9d1f2b4
Create Date: 2026-04-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d1f4a2c8b6e0"
down_revision: Union[str, Sequence[str], None] = "c7a3e9d1f2b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "chunks",
        sa.Column("region_code", sa.String(length=4), nullable=True),
    )
    op.add_column(
        "chunks",
        sa.Column("place_of_work", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("chunks", "place_of_work")
    op.drop_column("chunks", "region_code")
