"""admin panel tables + chunks.qdrant_point_id + prompt seed

Revision ID: c7a3e9d1f2b4
Revises: b4f5b573914c
Create Date: 2026-04-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "c7a3e9d1f2b4"
down_revision: Union[str, Sequence[str], None] = "b4f5b573914c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # -------------------------------------------------------------------
    # 1. admins
    # -------------------------------------------------------------------
    op.create_table(
        "admins",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("totp_secret", sa.String(length=64), nullable=True),
        sa.Column(
            "is_totp_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "must_change_password",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "failed_login_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "locked_until",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "last_login_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("username", name="uq_admins_username"),
    )
    op.create_index(
        "ix_admins_username",
        "admins",
        ["username"],
        unique=False,
    )

    # -------------------------------------------------------------------
    # 2. admin_audit_log
    # -------------------------------------------------------------------
    op.create_table(
        "admin_audit_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("admin_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("target_type", sa.String(length=50), nullable=True),
        sa.Column("target_id", sa.String(length=100), nullable=True),
        sa.Column("payload_diff", postgresql.JSONB(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["admin_id"],
            ["admins.id"],
            ondelete="SET NULL",
            name="fk_admin_audit_log_admin_id",
        ),
    )
    op.create_index(
        "ix_admin_audit_log_admin_id",
        "admin_audit_log",
        ["admin_id"],
    )
    op.create_index(
        "ix_admin_audit_log_action",
        "admin_audit_log",
        ["action"],
    )
    op.create_index(
        "ix_admin_audit_log_created_at",
        "admin_audit_log",
        ["created_at"],
    )

    # -------------------------------------------------------------------
    # 3. prompts
    # -------------------------------------------------------------------
    op.create_table(
        "prompts",
        sa.Column("key", sa.String(length=100), primary_key=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "version",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("1"),
        ),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["updated_by"],
            ["admins.id"],
            ondelete="SET NULL",
            name="fk_prompts_updated_by",
        ),
    )

    # -------------------------------------------------------------------
    # 4. prompt_history
    # -------------------------------------------------------------------
    op.create_table(
        "prompt_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("prompt_key", sa.String(length=100), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("changed_by", sa.Integer(), nullable=True),
        sa.Column(
            "changed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["prompt_key"],
            ["prompts.key"],
            ondelete="CASCADE",
            name="fk_prompt_history_prompt_key",
        ),
        sa.ForeignKeyConstraint(
            ["changed_by"],
            ["admins.id"],
            ondelete="SET NULL",
            name="fk_prompt_history_changed_by",
        ),
    )
    op.create_index(
        "ix_prompt_history_prompt_key",
        "prompt_history",
        ["prompt_key"],
    )
    op.create_index(
        "ix_prompt_history_changed_at",
        "prompt_history",
        ["changed_at"],
    )

    # -------------------------------------------------------------------
    # 5. chunks.qdrant_point_id
    # -------------------------------------------------------------------
    op.add_column(
        "chunks",
        sa.Column(
            "qdrant_point_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_unique_constraint(
        "uq_chunks_qdrant_point_id",
        "chunks",
        ["qdrant_point_id"],
    )

    # -------------------------------------------------------------------
    # 6. Seed prompts with default bodies
    #
    # Imported lazily so the migration module stays importable even
    # when `app.agent.prompts` cannot be resolved (e.g. during
    # alembic --sql rendering in an isolated env). If the import fails
    # we leave the table empty — the backend PromptService will still
    # fall back to the constants at runtime.
    # -------------------------------------------------------------------
    try:
        from app.agent.prompts import DEFAULT_PROMPTS, PROMPT_DESCRIPTIONS
    except ImportError:  # pragma: no cover
        DEFAULT_PROMPTS = {}
        PROMPT_DESCRIPTIONS = {}

    if DEFAULT_PROMPTS:
        prompts_table = sa.table(
            "prompts",
            sa.column("key", sa.String()),
            sa.column("body", sa.Text()),
            sa.column("description", sa.Text()),
            sa.column("version", sa.Integer()),
        )
        rows = [
            {
                "key": key,
                "body": body,
                "description": PROMPT_DESCRIPTIONS.get(key),
                "version": 1,
            }
            for key, body in DEFAULT_PROMPTS.items()
        ]
        # ON CONFLICT DO NOTHING for idempotency.
        stmt = postgresql.insert(prompts_table).values(rows)
        stmt = stmt.on_conflict_do_nothing(index_elements=["key"])
        op.execute(stmt)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "uq_chunks_qdrant_point_id",
        "chunks",
        type_="unique",
    )
    op.drop_column("chunks", "qdrant_point_id")

    op.drop_index("ix_prompt_history_changed_at", table_name="prompt_history")
    op.drop_index("ix_prompt_history_prompt_key", table_name="prompt_history")
    op.drop_table("prompt_history")

    op.drop_table("prompts")

    op.drop_index("ix_admin_audit_log_created_at", table_name="admin_audit_log")
    op.drop_index("ix_admin_audit_log_action", table_name="admin_audit_log")
    op.drop_index("ix_admin_audit_log_admin_id", table_name="admin_audit_log")
    op.drop_table("admin_audit_log")

    op.drop_index("ix_admins_username", table_name="admins")
    op.drop_table("admins")
