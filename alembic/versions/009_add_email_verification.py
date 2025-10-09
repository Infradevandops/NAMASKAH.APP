"""Add email verification tables

Revision ID: 009_add_email_verification
Revises: 008_add_refresh_tokens
Create Date: 2025-01-09 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '009_add_email_verification'
down_revision = '008_add_refresh_tokens'
branch_labels = None
depends_on = None

def upgrade():
    # Create email_verification_tokens table
    op.create_table('email_verification_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('token', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.Column('is_used', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token')
    )
    
    # Add email verification fields to users table
    op.add_column('users', sa.Column('email_verified_at', sa.DateTime(), nullable=True))
    
    # Create indexes for performance
    op.create_index('ix_email_verification_tokens_token', 'email_verification_tokens', ['token'])
    op.create_index('ix_email_verification_tokens_user_id', 'email_verification_tokens', ['user_id'])
    op.create_index('ix_email_verification_tokens_email', 'email_verification_tokens', ['email'])

def downgrade():
    # Drop indexes
    op.drop_index('ix_email_verification_tokens_email', table_name='email_verification_tokens')
    op.drop_index('ix_email_verification_tokens_user_id', table_name='email_verification_tokens')
    op.drop_index('ix_email_verification_tokens_token', table_name='email_verification_tokens')
    
    # Remove column from users table
    op.drop_column('users', 'email_verified_at')
    
    # Drop table
    op.drop_table('email_verification_tokens')