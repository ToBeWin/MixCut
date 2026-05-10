"""Initial migration — all tables.

Revision ID: 001
Revises:
Create Date: 2026-05-09 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.String(1024), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "assets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("storage_path", sa.String(1024), nullable=False),
        sa.Column("content_type", sa.String(128), nullable=False, server_default="video/mp4"),
        sa.Column("status", sa.String(32), nullable=False, server_default="uploaded"),
        sa.Column("duration_seconds", sa.Float, nullable=True),
        sa.Column("width", sa.Integer, nullable=True),
        sa.Column("height", sa.Integer, nullable=True),
        sa.Column("fps", sa.Float, nullable=True),
        sa.Column("codec", sa.String(32), nullable=True),
        sa.Column("audio_present", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("audio_codec", sa.String(32), nullable=True),
        sa.Column("poster_path", sa.String(1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("goal", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("status", sa.String(32), nullable=False, server_default="queued"),
        sa.Column("progress", sa.Float, nullable=False, server_default=sa.text("0.0")),
        sa.Column("current_step", sa.String(64), nullable=True),
        sa.Column("output_path", sa.String(1024), nullable=True),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("trace_events", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "edit_scripts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("job_id", sa.String(36), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("version", sa.Integer, nullable=False, server_default=sa.text("1")),
        sa.Column("target_platform", sa.String(32), nullable=False, server_default="custom"),
        sa.Column("target_duration", sa.Integer, nullable=False, server_default=sa.text("30")),
        sa.Column("aspect_ratio", sa.String(8), nullable=False, server_default="9:16"),
        sa.Column("segments", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("bgm_path", sa.String(1024), nullable=True),
        sa.Column("voiceover_script", sa.Text, nullable=True),
        sa.Column("planning_rationale", sa.Text, nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "corrections",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("job_id", sa.String(36), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("raw_text", sa.Text, nullable=False),
        sa.Column("operations", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("affected_nodes", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("confidence", sa.Float, nullable=False, server_default=sa.text("0.0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("corrections")
    op.drop_table("edit_scripts")
    op.drop_table("jobs")
    op.drop_table("assets")
    op.drop_table("projects")