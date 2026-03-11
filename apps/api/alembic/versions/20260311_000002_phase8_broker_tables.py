"""phase8_broker_tables

Revision ID: 20260311_000002
Revises: 20260310_000001
Create Date: 2026-03-11 13:45:00.000000

"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260311_000002"
down_revision = "20260310_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "broker_accounts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("external_account_id", sa.String(length=120), nullable=False),
        sa.Column("account_name", sa.String(length=120), nullable=False),
        sa.Column("account_type", sa.String(length=32), nullable=False),
        sa.Column("base_currency", sa.String(length=8), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("account_meta", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "provider",
            "external_account_id",
            name="uq_broker_account_user_provider_external",
        ),
    )
    op.create_index(
        "ix_broker_accounts_user_provider",
        "broker_accounts",
        ["user_id", "provider"],
        unique=False,
    )

    op.create_table(
        "broker_position_snapshots",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("broker_account_id", sa.String(length=36), nullable=False),
        sa.Column("instrument_id", sa.String(length=36), nullable=True),
        sa.Column("symbol", sa.String(length=24), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 6), nullable=False),
        sa.Column("avg_cost", sa.Numeric(18, 6), nullable=True),
        sa.Column("market_price", sa.Numeric(18, 6), nullable=True),
        sa.Column("market_value", sa.Numeric(20, 2), nullable=True),
        sa.Column("as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_provider", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["broker_account_id"], ["broker_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["instrument_id"], ["instruments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_broker_position_snapshots_account_as_of",
        "broker_position_snapshots",
        ["broker_account_id", "as_of"],
        unique=False,
    )
    op.create_index(
        "ix_broker_position_snapshots_symbol_as_of",
        "broker_position_snapshots",
        ["symbol", "as_of"],
        unique=False,
    )

    op.create_table(
        "broker_sync_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fetched_accounts", sa.Integer(), nullable=False),
        sa.Column("fetched_positions", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_broker_sync_runs_user_provider_started",
        "broker_sync_runs",
        ["user_id", "provider", "started_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_broker_sync_runs_user_provider_started", table_name="broker_sync_runs")
    op.drop_table("broker_sync_runs")
    op.drop_index("ix_broker_position_snapshots_symbol_as_of", table_name="broker_position_snapshots")
    op.drop_index("ix_broker_position_snapshots_account_as_of", table_name="broker_position_snapshots")
    op.drop_table("broker_position_snapshots")
    op.drop_index("ix_broker_accounts_user_provider", table_name="broker_accounts")
    op.drop_table("broker_accounts")
