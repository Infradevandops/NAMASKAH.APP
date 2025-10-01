#!/usr/bin/env python3
"""
PostgreSQL Configuration for CumApp
Production-ready database configuration with connection pooling and optimization
"""
import os
import logging
from typing import Dict, Any, Optional
from urllib.parse import urlparse
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


class PostgreSQLConfig:
    """PostgreSQL configuration manager"""
    
    def __init__(self):
        self.database_url = self._get_database_url()
        self.pool_config = self._get_pool_config()
        self.engine_config = self._get_engine_config()
    
    def _get_database_url(self) -> str:
        """Get PostgreSQL database URL from environment"""
        database_url = os.getenv("DATABASE_URL")
        
        if not database_url:
            # Construct from individual components
            host = os.getenv("POSTGRES_HOST", "localhost")
            port = os.getenv("POSTGRES_PORT", "5432")
            database = os.getenv("POSTGRES_DB", "cumapp_production")
            username = os.getenv("POSTGRES_USER", "cumapp_user")
            password = os.getenv("POSTGRES_PASSWORD")
            
            if not password:
                raise ValueError("PostgreSQL password must be provided via POSTGRES_PASSWORD or DATABASE_URL")
            
            database_url = f"postgresql://{username}:{password}@{host}:{port}/{database}"
        
        # Handle postgres:// vs postgresql:// URL schemes
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        
        return database_url
    
    def _get_pool_config(self) -> Dict[str, Any]:
        """Get connection pool configuration"""
        return {
            "poolclass": QueuePool,
            "pool_size": int(os.getenv("DB_POOL_SIZE", "20")),
            "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "30")),
            "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "3600")),  # 1 hour
            "pool_pre_ping": True,  # Validate connections before use
            "pool_reset_on_return": "commit",  # Reset connections on return
        }
    
    def _get_engine_config(self) -> Dict[str, Any]:
        """Get SQLAlchemy engine configuration"""
        return {
            "echo": os.getenv("SQL_DEBUG", "false").lower() == "true",
            "echo_pool": os.getenv("SQL_DEBUG_POOL", "false").lower() == "true",
            "future": True,  # Use SQLAlchemy 2.0 style
            "connect_args": {
                "connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", "30")),
                "command_timeout": int(os.getenv("DB_COMMAND_TIMEOUT", "60")),
                "server_settings": {
                    "application_name": "cumapp",
                    "jit": "off",  # Disable JIT for better performance on small queries
                }
            }
        }
    
    def create_engine(self) -> Engine:
        """Create configured PostgreSQL engine"""
        config = {**self.pool_config, **self.engine_config}
        engine = create_engine(self.database_url, **config)
        
        # Add event listeners for monitoring and optimization
        self._add_event_listeners(engine)
        
        return engine
    
    def _add_event_listeners(self, engine: Engine) -> None:
        """Add event listeners for monitoring and optimization"""
        
        @event.listens_for(engine, "connect")
        def set_postgresql_pragmas(dbapi_connection, connection_record):
            """Set PostgreSQL connection parameters for optimization"""
            with dbapi_connection.cursor() as cursor:
                # Set connection-level optimizations
                cursor.execute("SET statement_timeout = '300s'")  # 5 minutes
                cursor.execute("SET lock_timeout = '30s'")
                cursor.execute("SET idle_in_transaction_session_timeout = '60s'")
                cursor.execute("SET tcp_keepalives_idle = '300'")
                cursor.execute("SET tcp_keepalives_interval = '30'")
                cursor.execute("SET tcp_keepalives_count = '3'")
                
                # Set work memory for complex queries
                cursor.execute("SET work_mem = '32MB'")
                cursor.execute("SET maintenance_work_mem = '256MB'")
                
                # Enable parallel query execution
                cursor.execute("SET max_parallel_workers_per_gather = '2'")
                
                logger.debug("PostgreSQL connection optimizations applied")
        
        @event.listens_for(engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """Log connection checkout for monitoring"""
            logger.debug(f"Connection checked out from pool. Pool size: {engine.pool.size()}")
        
        @event.listens_for(engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            """Log connection checkin for monitoring"""
            logger.debug("Connection returned to pool")
    
    def get_session_factory(self, engine: Engine) -> sessionmaker:
        """Create session factory with optimized settings"""
        return sessionmaker(
            bind=engine,
            autocommit=False,
            autoflush=False,  # Manual flush for better control
            expire_on_commit=False,  # Keep objects accessible after commit
        )
    
    def validate_connection(self, engine: Engine) -> bool:
        """Validate PostgreSQL connection and configuration"""
        try:
            with engine.connect() as conn:
                # Test basic connectivity
                result = conn.execute("SELECT version()")
                version = result.scalar()
                logger.info(f"Connected to PostgreSQL: {version}")
                
                # Check if we have required extensions
                result = conn.execute("""
                    SELECT extname FROM pg_extension 
                    WHERE extname IN ('pg_stat_statements', 'pg_trgm')
                """)
                extensions = [row[0] for row in result]
                
                if 'pg_stat_statements' not in extensions:
                    logger.warning("pg_stat_statements extension not found - query monitoring limited")
                
                if 'pg_trgm' not in extensions:
                    logger.warning("pg_trgm extension not found - full-text search performance may be limited")
                
                # Check database configuration
                result = conn.execute("""
                    SELECT name, setting, unit 
                    FROM pg_settings 
                    WHERE name IN (
                        'shared_buffers', 'effective_cache_size', 
                        'maintenance_work_mem', 'checkpoint_completion_target',
                        'wal_buffers', 'default_statistics_target'
                    )
                """)
                
                settings = {row[0]: (row[1], row[2]) for row in result}
                logger.info(f"PostgreSQL configuration: {settings}")
                
                return True
                
        except Exception as e:
            logger.error(f"PostgreSQL connection validation failed: {e}")
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get database connection information (safe for logging)"""
        parsed = urlparse(self.database_url)
        return {
            "host": parsed.hostname,
            "port": parsed.port,
            "database": parsed.path.lstrip('/'),
            "username": parsed.username,
            "pool_size": self.pool_config["pool_size"],
            "max_overflow": self.pool_config["max_overflow"],
            "pool_recycle": self.pool_config["pool_recycle"],
        }


class PostgreSQLHealthCheck:
    """PostgreSQL health monitoring"""
    
    def __init__(self, engine: Engine):
        self.engine = engine
    
    def check_connection_pool(self) -> Dict[str, Any]:
        """Check connection pool status"""
        pool = self.engine.pool
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid(),
        }
    
    def check_database_performance(self) -> Dict[str, Any]:
        """Check database performance metrics"""
        try:
            with self.engine.connect() as conn:
                # Check active connections
                result = conn.execute("""
                    SELECT count(*) as active_connections
                    FROM pg_stat_activity 
                    WHERE state = 'active' AND datname = current_database()
                """)
                active_connections = result.scalar()
                
                # Check slow queries (if pg_stat_statements is available)
                try:
                    result = conn.execute("""
                        SELECT count(*) as slow_queries
                        FROM pg_stat_statements 
                        WHERE mean_exec_time > 1000  -- queries taking > 1 second
                    """)
                    slow_queries = result.scalar()
                except:
                    slow_queries = None
                
                # Check database size
                result = conn.execute("""
                    SELECT pg_size_pretty(pg_database_size(current_database())) as db_size
                """)
                db_size = result.scalar()
                
                # Check table sizes
                result = conn.execute("""
                    SELECT 
                        schemaname,
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                    LIMIT 5
                """)
                largest_tables = [dict(row) for row in result]
                
                return {
                    "active_connections": active_connections,
                    "slow_queries": slow_queries,
                    "database_size": db_size,
                    "largest_tables": largest_tables,
                    "pool_status": self.check_connection_pool(),
                }
                
        except Exception as e:
            logger.error(f"Database performance check failed: {e}")
            return {"error": str(e)}
    
    def check_replication_status(self) -> Optional[Dict[str, Any]]:
        """Check replication status (if applicable)"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute("""
                    SELECT 
                        client_addr,
                        state,
                        sent_lsn,
                        write_lsn,
                        flush_lsn,
                        replay_lsn,
                        sync_state
                    FROM pg_stat_replication
                """)
                
                replicas = [dict(row) for row in result]
                return {"replicas": replicas} if replicas else None
                
        except Exception as e:
            logger.error(f"Replication status check failed: {e}")
            return None


# Global configuration instance
postgresql_config = PostgreSQLConfig()