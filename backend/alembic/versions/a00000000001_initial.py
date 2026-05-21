"""initial

Revision ID: a00000000001
Revises:
Create Date: 2026-05-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "a00000000001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── users ──────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_unique_constraint("uq_users_email", "users", ["email"])

    # ── servers ────────────────────────────────────────────────────────
    op.create_table(
        "servers",
        sa.Column("id", sa.Uuid(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("hostname", sa.String(255), nullable=True),
        sa.Column("api_token_hash", sa.String(255), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_servers_user_id", "servers", ["user_id"])
    op.create_index("ix_servers_api_token_hash", "servers", ["api_token_hash"])

    # ── metrics ────────────────────────────────────────────────────────
    op.create_table(
        "metrics",
        sa.Column("id", sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column("server_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("cpu_percent", sa.Float(), nullable=False),
        sa.Column("ram_percent", sa.Float(), nullable=False),
        sa.Column("ram_used_mb", sa.Integer(), nullable=False),
        sa.Column("ram_total_mb", sa.Integer(), nullable=False),
        sa.Column("disk_percent", sa.Float(), nullable=False),
        sa.Column("disk_used_gb", sa.Float(), nullable=False),
        sa.Column("disk_total_gb", sa.Float(), nullable=False),
        sa.Column("net_rx_bytes", sa.BigInteger(), nullable=False),
        sa.Column("net_tx_bytes", sa.BigInteger(), nullable=False),
        sa.Column("uptime_seconds", sa.BigInteger(), nullable=False),
        sa.Column("load_avg_1", sa.Float(), nullable=True),
        sa.Column("load_avg_5", sa.Float(), nullable=True),
        sa.Column("load_avg_15", sa.Float(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["server_id"], ["servers.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_metrics_server_recorded",
        "metrics",
        ["server_id", sa.text("recorded_at DESC")],
    )


def downgrade() -> None:
    op.drop_table("metrics")
    op.drop_table("servers")
    op.drop_table("users")
