"""Add persisted model routes and image-friendly asset fields.

Revision ID: 002
Revises: 001
Create Date: 2026-05-09 01:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "model_routes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("task", sa.String(64), nullable=False, unique=True),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("model", sa.String(128), nullable=True),
        sa.Column("fallback_providers", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_model_routes_task", "model_routes", ["task"], unique=True)

    op.add_column("assets", sa.Column("proxy_path", sa.String(1024), nullable=True))


def downgrade() -> None:
    op.drop_column("assets", "proxy_path")
    op.drop_index("ix_model_routes_task", table_name="model_routes")
    op.drop_table("model_routes")
