"""Add preliminary TEO fields to projects.

Revision ID: 004_project_teo_fields
Revises: 003_document_permissions
Create Date: 2025-02-14 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "004_project_teo_fields"
down_revision = "003_document_permissions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("planned_duration_days", sa.Integer(), nullable=True))
    op.add_column("projects", sa.Column("expected_start", sa.Date(), nullable=True))
    op.add_column("projects", sa.Column("expected_completion", sa.Date(), nullable=True))
    op.add_column("projects", sa.Column("preliminary_budget", sa.Numeric(15, 2), nullable=True))
    op.add_column("projects", sa.Column("preliminary_teo_path", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("projects", "preliminary_teo_path")
    op.drop_column("projects", "preliminary_budget")
    op.drop_column("projects", "expected_completion")
    op.drop_column("projects", "expected_start")
    op.drop_column("projects", "planned_duration_days")

