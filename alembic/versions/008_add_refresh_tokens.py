"""Add refresh tokens and token blacklist tables

Revision ID: 008_add_refresh_tokens
Revises: 007_postgresql_migration
Create Date: 2025-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '008_add_refresh_tokens'
down_revision = '007_postgresql_migration'
branch_labels = None
depends_on = None

def upgrade():
    # Create refresh_tokens table
    op.create_table('refresh_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token_hash', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('device_info', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash')
    )
    
    # Create token_blacklist table
    op.create_table('token_blacklist',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token_jti', sa.String(length=255), nullable=False),
        sa.Column('blacklisted_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('reason', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_jti')
    )
    
    # Create indexes for performance
    op.create_index('idx_refresh_tokens_user_id', 'refresh_tokens', ['user_id'])
    op.create_index('idx_refresh_tokens_expires_at', 'refresh_tokens', ['expires_at'])
    op.create_index('idx_refresh_tokens_active', 'refresh_tokens', ['is_active'])
    op.create_index('idx_token_blacklist_jti', 'token_blacklist', ['token_jti'])
    op.create_index('idx_token_blacklist_expires_at', 'token_blacklist', ['expires_at'])

def downgrade():
    # Drop indexes
    op.drop_index('idx_token_blacklist_expires_at', table_name='token_blacklist')
    op.drop_index('idx_token_blacklist_jti', table_name='token_blacklist')
    op.drop_index('idx_refresh_tokens_active', table_name='refresh_tokens')
    op.drop_index('idx_refresh_tokens_expires_at', table_name='refresh_tokens')
    op.drop_index('idx_refresh_tokens_user_id', table_name='refresh_tokens')
    
    # Drop tables
    op.drop_table('token_blacklist')
    op.drop_table('refresh_tokens')