"""Document permissions tables

Revision ID: 003
Revises: 002
Create Date: 2025-01-09

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Создание таблицы document_permissions
    op.create_table(
        'document_permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('subject_type', sa.String(), nullable=False),
        sa.Column('subject_id', sa.Integer(), nullable=False),
        sa.Column('permission_type', sa.String(), nullable=False),
        sa.Column('inherited_from', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.ForeignKeyConstraint(['inherited_from'], ['document_permissions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_permissions_id'), 'document_permissions', ['id'], unique=False)
    op.create_index(op.f('ix_document_permissions_document_id'), 'document_permissions', ['document_id'], unique=False)

    # Создание таблицы document_access_logs
    op.create_table(
        'document_access_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('action_type', sa.String(), nullable=False),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_access_logs_id'), 'document_access_logs', ['id'], unique=False)
    op.create_index(op.f('ix_document_access_logs_document_id'), 'document_access_logs', ['document_id'], unique=False)
    op.create_index(op.f('ix_document_access_logs_user_id'), 'document_access_logs', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_document_access_logs_user_id'), table_name='document_access_logs')
    op.drop_index(op.f('ix_document_access_logs_document_id'), table_name='document_access_logs')
    op.drop_index(op.f('ix_document_access_logs_id'), table_name='document_access_logs')
    op.drop_table('document_access_logs')
    op.drop_index(op.f('ix_document_permissions_document_id'), table_name='document_permissions')
    op.drop_index(op.f('ix_document_permissions_id'), table_name='document_permissions')
    op.drop_table('document_permissions')

