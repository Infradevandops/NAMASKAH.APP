"""PostgreSQL migration and optimization

Revision ID: 007_postgresql_migration
Revises: 006_add_data_retention_policies
Create Date: 2024-12-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007_postgresql_migration'
down_revision = '006_add_data_retention_policies'
branch_labels = None
depends_on = None


def upgrade():
    """Upgrade to PostgreSQL with optimizations"""
    
    # Add PostgreSQL-specific indexes for better performance
    try:
        # Composite indexes for common query patterns
        op.create_index(
            'idx_users_email_active',
            'users',
            ['email', 'is_active'],
            postgresql_using='btree'
        )
        
        op.create_index(
            'idx_users_subscription_status',
            'users',
            ['subscription_plan', 'is_active', 'created_at'],
            postgresql_using='btree'
        )
        
        # Subscription-related indexes
        op.create_index(
            'idx_user_subscriptions_status_billing',
            'user_subscriptions',
            ['status', 'next_billing_date'],
            postgresql_using='btree'
        )
        
        op.create_index(
            'idx_user_subscriptions_user_active',
            'user_subscriptions',
            ['user_id', 'status'],
            postgresql_using='btree'
        )
        
        # Payment-related indexes
        op.create_index(
            'idx_payments_user_status_date',
            'payments',
            ['user_id', 'status', 'created_at'],
            postgresql_using='btree'
        )
        
        op.create_index(
            'idx_payments_subscription_period',
            'payments',
            ['subscription_id', 'billing_period_start', 'billing_period_end'],
            postgresql_using='btree'
        )
        
        # Usage tracking indexes
        op.create_index(
            'idx_usage_records_user_type_period',
            'usage_records',
            ['user_id', 'usage_type', 'billing_period_start'],
            postgresql_using='btree'
        )
        
        op.create_index(
            'idx_usage_records_subscription_timestamp',
            'usage_records',
            ['subscription_id', 'usage_timestamp'],
            postgresql_using='btree'
        )
        
        # Verification-related indexes
        op.create_index(
            'idx_verification_requests_user_status_created',
            'verification_requests',
            ['user_id', 'status', 'created_at'],
            postgresql_using='btree'
        )
        
        # Phone number indexes
        op.create_index(
            'idx_phone_numbers_country_available',
            'phone_numbers',
            ['country_code', 'is_available', 'tier'],
            postgresql_using='btree'
        )
        
        # Session management indexes
        op.create_index(
            'idx_sessions_user_active_expires',
            'sessions',
            ['user_id', 'is_active', 'expires_at'],
            postgresql_using='btree'
        )
        
        # API key indexes
        op.create_index(
            'idx_api_keys_user_active_expires',
            'api_keys',
            ['user_id', 'is_active', 'expires_at'],
            postgresql_using='btree'
        )
        
        # Partial indexes for active records only (PostgreSQL specific)
        op.create_index(
            'idx_users_active_only',
            'users',
            ['id', 'email', 'created_at'],
            postgresql_where=sa.text('is_active = true'),
            postgresql_using='btree'
        )
        
        op.create_index(
            'idx_subscriptions_active_only',
            'user_subscriptions',
            ['user_id', 'plan_id', 'next_billing_date'],
            postgresql_where=sa.text("status = 'active'"),
            postgresql_using='btree'
        )
        
        op.create_index(
            'idx_phone_numbers_available_only',
            'phone_numbers',
            ['country_code', 'tier', 'created_at'],
            postgresql_where=sa.text('is_available = true'),
            postgresql_using='btree'
        )
        
        # Full-text search indexes for better search performance
        op.execute("""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_fulltext_search 
            ON users USING gin(to_tsvector('english', 
                COALESCE(full_name, '') || ' ' || 
                COALESCE(email, '') || ' ' || 
                COALESCE(username, '')
            ))
        """)
        
        # Create materialized view for subscription analytics
        op.execute("""
            CREATE MATERIALIZED VIEW IF NOT EXISTS subscription_analytics_daily AS
            SELECT 
                date_trunc('day', created_at) as date,
                subscription_plan,
                COUNT(*) as new_subscriptions,
                SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_subscriptions,
                SUM(CASE WHEN cancelled_at IS NOT NULL THEN 1 ELSE 0 END) as cancelled_subscriptions,
                AVG(current_price) as avg_revenue_per_user
            FROM user_subscriptions
            GROUP BY date_trunc('day', created_at), subscription_plan
            ORDER BY date DESC;
        """)
        
        # Create index on materialized view
        op.create_index(
            'idx_subscription_analytics_daily_date',
            'subscription_analytics_daily',
            ['date', 'subscription_plan'],
            postgresql_using='btree'
        )
        
        # Create function to refresh analytics
        op.execute("""
            CREATE OR REPLACE FUNCTION refresh_subscription_analytics()
            RETURNS void AS $$
            BEGIN
                REFRESH MATERIALIZED VIEW CONCURRENTLY subscription_analytics_daily;
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        # Create trigger to auto-refresh analytics (optional)
        op.execute("""
            CREATE OR REPLACE FUNCTION trigger_refresh_analytics()
            RETURNS trigger AS $$
            BEGIN
                -- Refresh analytics in background (non-blocking)
                PERFORM pg_notify('refresh_analytics', 'subscription_change');
                RETURN COALESCE(NEW, OLD);
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        op.execute("""
            DROP TRIGGER IF EXISTS subscription_analytics_refresh ON user_subscriptions;
            CREATE TRIGGER subscription_analytics_refresh
                AFTER INSERT OR UPDATE OR DELETE ON user_subscriptions
                FOR EACH ROW EXECUTE FUNCTION trigger_refresh_analytics();
        """)
        
    except Exception as e:
        # Skip PostgreSQL-specific features for other databases
        print(f"Skipping PostgreSQL-specific optimizations: {e}")
        pass


def downgrade():
    """Downgrade from PostgreSQL optimizations"""
    
    try:
        # Drop triggers and functions
        op.execute("DROP TRIGGER IF EXISTS subscription_analytics_refresh ON user_subscriptions")
        op.execute("DROP FUNCTION IF EXISTS trigger_refresh_analytics()")
        op.execute("DROP FUNCTION IF EXISTS refresh_subscription_analytics()")
        
        # Drop materialized view
        op.execute("DROP MATERIALIZED VIEW IF EXISTS subscription_analytics_daily")
        
        # Drop full-text search indexes
        op.drop_index('idx_users_fulltext_search', 'users')
        
        # Drop partial indexes
        op.drop_index('idx_phone_numbers_available_only', 'phone_numbers')
        op.drop_index('idx_subscriptions_active_only', 'user_subscriptions')
        op.drop_index('idx_users_active_only', 'users')
        
        # Drop composite indexes
        op.drop_index('idx_api_keys_user_active_expires', 'api_keys')
        op.drop_index('idx_sessions_user_active_expires', 'sessions')
        op.drop_index('idx_phone_numbers_country_available', 'phone_numbers')
        op.drop_index('idx_verification_requests_user_status_created', 'verification_requests')
        op.drop_index('idx_usage_records_subscription_timestamp', 'usage_records')
        op.drop_index('idx_usage_records_user_type_period', 'usage_records')
        op.drop_index('idx_payments_subscription_period', 'payments')
        op.drop_index('idx_payments_user_status_date', 'payments')
        op.drop_index('idx_user_subscriptions_user_active', 'user_subscriptions')
        op.drop_index('idx_user_subscriptions_status_billing', 'user_subscriptions')
        op.drop_index('idx_users_subscription_status', 'users')
        op.drop_index('idx_users_email_active', 'users')
        
    except Exception as e:
        print(f"Error during downgrade: {e}")
        pass