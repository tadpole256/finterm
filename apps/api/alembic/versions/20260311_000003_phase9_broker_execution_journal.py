"""phase9_broker_execution_journal

Revision ID: 20260311_000003
Revises: 20260311_000002
Create Date: 2026-03-11 15:05:00.000000

"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260311_000003"
down_revision = "20260311_000002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "broker_order_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("broker_account_id", sa.String(length=36), nullable=True),
        sa.Column("external_order_id", sa.String(length=120), nullable=False),
        sa.Column("symbol", sa.String(length=24), nullable=False),
        sa.Column("side", sa.String(length=8), nullable=False),
        sa.Column("order_type", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 6), nullable=False),
        sa.Column("limit_price", sa.Numeric(18, 6), nullable=True),
        sa.Column("filled_quantity", sa.Numeric(18, 6), nullable=False),
        sa.Column("avg_fill_price", sa.Numeric(18, 6), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("event_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["broker_account_id"], ["broker_accounts.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_broker_order_events_user_submitted",
        "broker_order_events",
        ["user_id", "submitted_at"],
        unique=False,
    )
    op.create_index(
        "ix_broker_order_events_symbol_status",
        "broker_order_events",
        ["symbol", "status"],
        unique=False,
    )

    op.create_table(
        "reconciliation_exceptions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("portfolio_id", sa.String(length=36), nullable=True),
        sa.Column("symbol", sa.String(length=24), nullable=False),
        sa.Column("issue_type", sa.String(length=32), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("local_quantity", sa.Numeric(18, 6), nullable=True),
        sa.Column("broker_quantity", sa.Numeric(18, 6), nullable=True),
        sa.Column("local_market_value", sa.Numeric(20, 2), nullable=True),
        sa.Column("broker_market_value", sa.Numeric(20, 2), nullable=True),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_reconciliation_exceptions_user_status",
        "reconciliation_exceptions",
        ["user_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_reconciliation_exceptions_symbol_type",
        "reconciliation_exceptions",
        ["symbol", "issue_type"],
        unique=False,
    )

    op.create_table(
        "trade_journal_entries",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("portfolio_id", sa.String(length=36), nullable=True),
        sa.Column("transaction_id", sa.String(length=36), nullable=True),
        sa.Column("broker_order_event_id", sa.String(length=36), nullable=True),
        sa.Column("symbol", sa.String(length=24), nullable=True),
        sa.Column("entry_type", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["broker_order_event_id"], ["broker_order_events.id"]),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"]),
        sa.ForeignKeyConstraint(["transaction_id"], ["transactions.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_trade_journal_entries_user_symbol_created",
        "trade_journal_entries",
        ["user_id", "symbol", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_trade_journal_entries_user_symbol_created", table_name="trade_journal_entries")
    op.drop_table("trade_journal_entries")
    op.drop_index("ix_reconciliation_exceptions_symbol_type", table_name="reconciliation_exceptions")
    op.drop_index("ix_reconciliation_exceptions_user_status", table_name="reconciliation_exceptions")
    op.drop_table("reconciliation_exceptions")
    op.drop_index("ix_broker_order_events_symbol_status", table_name="broker_order_events")
    op.drop_index("ix_broker_order_events_user_submitted", table_name="broker_order_events")
    op.drop_table("broker_order_events")
