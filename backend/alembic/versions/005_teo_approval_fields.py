"""Add TEO approval tracking columns.

Revision ID: 005_teo_approval_fields
Revises: 004_project_teo_fields
Create Date: 2025-02-15 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "005_teo_approval_fields"
down_revision = "004_project_teo_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "projects",
        sa.Column("teo_approval_status", sa.String(), nullable=False, server_default="not_required"),
    )
    op.add_column("projects", sa.Column("teo_approval_route", sa.JSON(), nullable=True))
    op.add_column("projects", sa.Column("teo_approval_history", sa.JSON(), nullable=True))
    op.add_column("projects", sa.Column("teo_approved_at", sa.DateTime(timezone=True), nullable=True))
    op.alter_column("projects", "teo_approval_status", server_default=None)


def downgrade() -> None:
    op.drop_column("projects", "teo_approved_at")
    op.drop_column("projects", "teo_approval_history")
    op.drop_column("projects", "teo_approval_route")
    op.drop_column("projects", "teo_approval_status")


