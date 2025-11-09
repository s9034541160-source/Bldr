"""Documents and Projects tables

Revision ID: 002
Revises: 001
Create Date: 2025-01-09

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Создание таблицы projects
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('code', sa.String(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('planned_end_date', sa.Date(), nullable=True),
        sa.Column('budget', sa.Numeric(15, 2), nullable=True),
        sa.Column('spent', sa.Numeric(15, 2), nullable=False, server_default='0'),
        sa.Column('status', sa.String(), nullable=False, server_default='planning'),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('manager_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['manager_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_projects_id'), 'projects', ['id'], unique=False)
    op.create_index(op.f('ix_projects_name'), 'projects', ['name'], unique=False)
    op.create_index(op.f('ix_projects_code'), 'projects', ['code'], unique=True)
    op.create_index(op.f('ix_projects_status'), 'projects', ['status'], unique=False)
    op.create_index(op.f('ix_projects_owner_id'), 'projects', ['owner_id'], unique=False)
    op.create_index(op.f('ix_projects_manager_id'), 'projects', ['manager_id'], unique=False)

    # Создание таблицы documents
    op.create_table(
        'documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('document_type', sa.String(), nullable=False),
        sa.Column('file_name', sa.String(), nullable=False),
        sa.Column('file_path', sa.String(), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('parent_version_id', sa.Integer(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='draft'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['parent_version_id'], ['documents.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('file_path')
    )
    op.create_index(op.f('ix_documents_id'), 'documents', ['id'], unique=False)
    op.create_index(op.f('ix_documents_title'), 'documents', ['title'], unique=False)
    op.create_index(op.f('ix_documents_document_type'), 'documents', ['document_type'], unique=False)
    op.create_index(op.f('ix_documents_project_id'), 'documents', ['project_id'], unique=False)

    # Создание таблицы document_versions
    op.create_table(
        'document_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('file_path', sa.String(), nullable=False),
        sa.Column('file_hash', sa.String(), nullable=False),
        sa.Column('change_description', sa.Text(), nullable=True),
        sa.Column('changed_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['changed_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_versions_id'), 'document_versions', ['id'], unique=False)
    op.create_index(op.f('ix_document_versions_document_id'), 'document_versions', ['document_id'], unique=False)

    # Создание таблицы document_metadata
    op.create_table(
        'document_metadata',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('value_type', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_metadata_id'), 'document_metadata', ['id'], unique=False)
    op.create_index(op.f('ix_document_metadata_document_id'), 'document_metadata', ['document_id'], unique=False)
    op.create_index(op.f('ix_document_metadata_key'), 'document_metadata', ['key'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_document_metadata_key'), table_name='document_metadata')
    op.drop_index(op.f('ix_document_metadata_document_id'), table_name='document_metadata')
    op.drop_index(op.f('ix_document_metadata_id'), table_name='document_metadata')
    op.drop_table('document_metadata')
    op.drop_index(op.f('ix_document_versions_document_id'), table_name='document_versions')
    op.drop_index(op.f('ix_document_versions_id'), table_name='document_versions')
    op.drop_table('document_versions')
    op.drop_index(op.f('ix_documents_project_id'), table_name='documents')
    op.drop_index(op.f('ix_documents_document_type'), table_name='documents')
    op.drop_index(op.f('ix_documents_title'), table_name='documents')
    op.drop_index(op.f('ix_documents_id'), table_name='documents')
    op.drop_table('documents')
    op.drop_index(op.f('ix_projects_manager_id'), table_name='projects')
    op.drop_index(op.f('ix_projects_owner_id'), table_name='projects')
    op.drop_index(op.f('ix_projects_status'), table_name='projects')
    op.drop_index(op.f('ix_projects_code'), table_name='projects')
    op.drop_index(op.f('ix_projects_name'), table_name='projects')
    op.drop_index(op.f('ix_projects_id'), table_name='projects')
    op.drop_table('projects')

