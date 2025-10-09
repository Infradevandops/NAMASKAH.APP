#!/usr/bin/env python3
"""
SQLite to PostgreSQL Migration Script for namaskah
Safely migrates data from SQLite development database to PostgreSQL production
"""
import os
import sys
import logging
import sqlite3
import psycopg2
from datetime import datetime
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import Base
from models import (
    user_models, subscription_models, phone_number_models,
    verification_models, conversation_models, communication_models,
    enhanced_models
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SQLiteToPostgreSQLMigrator:
    """Handles migration from SQLite to PostgreSQL"""
    
    def __init__(self, sqlite_path: str, postgresql_url: str):
        self.sqlite_path = sqlite_path
        self.postgresql_url = postgresql_url
        
        # Validate inputs
        if not os.path.exists(sqlite_path):
            raise FileNotFoundError(f"SQLite database not found: {sqlite_path}")
        
        # Handle postgres:// vs postgresql:// URL schemes
        if postgresql_url.startswith("postgres://"):
            postgresql_url = postgresql_url.replace("postgres://", "postgresql://", 1)
        
        self.postgresql_url = postgresql_url
        
        # Create engines
        self.sqlite_engine = create_engine(f"sqlite:///{sqlite_path}")
        self.postgresql_engine = create_engine(postgresql_url)
        
        # Create session factories
        self.sqlite_session = sessionmaker(bind=self.sqlite_engine)
        self.postgresql_session = sessionmaker(bind=self.postgresql_engine)
        
        # Migration statistics
        self.migration_stats = {
            "tables_migrated": 0,
            "total_records": 0,
            "errors": [],
            "start_time": None,
            "end_time": None,
        }
    
    def validate_connections(self) -> bool:
        """Validate both database connections"""
        try:
            # Test SQLite connection
            with self.sqlite_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("✅ SQLite connection validated")
            
            # Test PostgreSQL connection
            with self.postgresql_engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                version = result.scalar()
                logger.info(f"✅ PostgreSQL connection validated: {version}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Connection validation failed: {e}")
            return False
    
    def backup_postgresql(self) -> bool:
        """Create backup of existing PostgreSQL data"""
        try:
            parsed = urlparse(self.postgresql_url)
            backup_file = f"postgresql_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
            
            # Use pg_dump to create backup
            cmd = [
                "pg_dump",
                f"--host={parsed.hostname}",
                f"--port={parsed.port or 5432}",
                f"--username={parsed.username}",
                f"--dbname={parsed.path.lstrip('/')}",
                f"--file={backup_file}",
                "--verbose",
                "--no-password"
            ]
            
            # Set password via environment
            env = os.environ.copy()
            env["PGPASSWORD"] = parsed.password
            
            import subprocess
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ PostgreSQL backup created: {backup_file}")
                return True
            else:
                logger.error(f"❌ Backup failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Backup creation failed: {e}")
            return False
    
    def create_postgresql_schema(self) -> bool:
        """Create PostgreSQL schema from SQLAlchemy models"""
        try:
            logger.info("🔧 Creating PostgreSQL schema...")
            
            # Drop existing tables (if any)
            Base.metadata.drop_all(bind=self.postgresql_engine)
            
            # Create all tables
            Base.metadata.create_all(bind=self.postgresql_engine)
            
            logger.info("✅ PostgreSQL schema created successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Schema creation failed: {e}")
            self.migration_stats["errors"].append(f"Schema creation: {e}")
            return False
    
    def get_table_migration_order(self) -> List[str]:
        """Get tables in dependency order for migration"""
        # Define migration order based on foreign key dependencies
        return [
            "users",
            "subscription_plan_configs",
            "user_subscriptions",
            "sessions",
            "api_keys",
            "phone_numbers",
            "user_numbers",
            "verification_requests",
            "verification_history",
            "conversations",
            "messages",
            "communication_logs",
            "payments",
            "usage_records",
            "subscription_analytics",
            "enhanced_conversations",
            "conversation_participants",
            "message_reactions",
            "message_threads",
            "conversation_analytics",
        ]
    
    def migrate_table_data(self, table_name: str) -> bool:
        """Migrate data for a specific table"""
        try:
            logger.info(f"📦 Migrating table: {table_name}")
            
            # Get data from SQLite
            with self.sqlite_engine.connect() as sqlite_conn:
                # Check if table exists in SQLite
                result = sqlite_conn.execute(text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name=:table_name
                """), {"table_name": table_name})
                
                if not result.fetchone():
                    logger.info(f"⏭️  Table {table_name} not found in SQLite, skipping")
                    return True
                
                # Get table data
                result = sqlite_conn.execute(text(f"SELECT * FROM {table_name}"))
                rows = result.fetchall()
                columns = result.keys()
                
                if not rows:
                    logger.info(f"⏭️  Table {table_name} is empty, skipping")
                    return True
                
                logger.info(f"📊 Found {len(rows)} records in {table_name}")
            
            # Insert data into PostgreSQL
            with self.postgresql_engine.connect() as pg_conn:
                # Prepare insert statement
                column_names = ", ".join(columns)
                placeholders = ", ".join([f":{col}" for col in columns])
                insert_sql = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"
                
                # Convert rows to dictionaries
                data_dicts = []
                for row in rows:
                    row_dict = {}
                    for i, col in enumerate(columns):
                        value = row[i]
                        # Handle SQLite boolean conversion
                        if isinstance(value, int) and col.endswith(('_active', '_verified', '_primary', '_available')):
                            value = bool(value)
                        row_dict[col] = value
                    data_dicts.append(row_dict)
                
                # Batch insert
                batch_size = 1000
                for i in range(0, len(data_dicts), batch_size):
                    batch = data_dicts[i:i + batch_size]
                    pg_conn.execute(text(insert_sql), batch)
                    pg_conn.commit()
                
                logger.info(f"✅ Migrated {len(rows)} records to {table_name}")
                self.migration_stats["total_records"] += len(rows)
                
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration failed for table {table_name}: {e}")
            self.migration_stats["errors"].append(f"Table {table_name}: {e}")
            return False
    
    def update_sequences(self) -> bool:
        """Update PostgreSQL sequences after data migration"""
        try:
            logger.info("🔧 Updating PostgreSQL sequences...")
            
            with self.postgresql_engine.connect() as conn:
                # Get all sequences
                result = conn.execute(text("""
                    SELECT schemaname, sequencename, tablename, columnname
                    FROM pg_sequences s
                    JOIN information_schema.columns c ON c.column_default LIKE '%' || s.sequencename || '%'
                    WHERE schemaname = 'public'
                """))
                
                sequences = result.fetchall()
                
                for seq in sequences:
                    schema, seq_name, table_name, column_name = seq
                    
                    # Get max value from table
                    max_result = conn.execute(text(f"SELECT COALESCE(MAX({column_name}), 0) FROM {table_name}"))
                    max_value = max_result.scalar()
                    
                    if max_value > 0:
                        # Update sequence
                        conn.execute(text(f"SELECT setval('{seq_name}', {max_value + 1})"))
                        logger.info(f"Updated sequence {seq_name} to {max_value + 1}")
                
                conn.commit()
                logger.info("✅ Sequences updated successfully")
                
            return True
            
        except Exception as e:
            logger.error(f"❌ Sequence update failed: {e}")
            self.migration_stats["errors"].append(f"Sequence update: {e}")
            return False
    
    def validate_migration(self) -> bool:
        """Validate migration by comparing record counts"""
        try:
            logger.info("🔍 Validating migration...")
            
            tables = self.get_table_migration_order()
            validation_results = {}
            
            for table_name in tables:
                # Count SQLite records
                with self.sqlite_engine.connect() as sqlite_conn:
                    try:
                        result = sqlite_conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                        sqlite_count = result.scalar()
                    except:
                        sqlite_count = 0
                
                # Count PostgreSQL records
                with self.postgresql_engine.connect() as pg_conn:
                    try:
                        result = pg_conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                        pg_count = result.scalar()
                    except:
                        pg_count = 0
                
                validation_results[table_name] = {
                    "sqlite_count": sqlite_count,
                    "postgresql_count": pg_count,
                    "match": sqlite_count == pg_count
                }
                
                if sqlite_count == pg_count:
                    logger.info(f"✅ {table_name}: {sqlite_count} records (match)")
                else:
                    logger.warning(f"⚠️  {table_name}: SQLite={sqlite_count}, PostgreSQL={pg_count} (mismatch)")
            
            # Overall validation
            total_mismatches = sum(1 for r in validation_results.values() if not r["match"])
            
            if total_mismatches == 0:
                logger.info("✅ Migration validation successful - all record counts match")
                return True
            else:
                logger.warning(f"⚠️  Migration validation found {total_mismatches} table(s) with mismatched counts")
                return False
                
        except Exception as e:
            logger.error(f"❌ Migration validation failed: {e}")
            return False
    
    def run_migration(self, create_backup: bool = True) -> bool:
        """Run the complete migration process"""
        self.migration_stats["start_time"] = datetime.now()
        
        try:
            logger.info("🚀 Starting SQLite to PostgreSQL migration...")
            
            # Step 1: Validate connections
            if not self.validate_connections():
                return False
            
            # Step 2: Create backup (optional)
            if create_backup:
                if not self.backup_postgresql():
                    logger.warning("⚠️  Backup failed, continuing without backup")
            
            # Step 3: Create PostgreSQL schema
            if not self.create_postgresql_schema():
                return False
            
            # Step 4: Migrate table data
            tables = self.get_table_migration_order()
            for table_name in tables:
                if not self.migrate_table_data(table_name):
                    logger.error(f"❌ Migration failed at table: {table_name}")
                    return False
                self.migration_stats["tables_migrated"] += 1
            
            # Step 5: Update sequences
            if not self.update_sequences():
                logger.warning("⚠️  Sequence update failed, but migration can continue")
            
            # Step 6: Validate migration
            validation_success = self.validate_migration()
            
            self.migration_stats["end_time"] = datetime.now()
            duration = self.migration_stats["end_time"] - self.migration_stats["start_time"]
            
            # Print migration summary
            logger.info("📊 Migration Summary:")
            logger.info(f"   Duration: {duration}")
            logger.info(f"   Tables migrated: {self.migration_stats['tables_migrated']}")
            logger.info(f"   Total records: {self.migration_stats['total_records']}")
            logger.info(f"   Errors: {len(self.migration_stats['errors'])}")
            
            if self.migration_stats["errors"]:
                logger.warning("⚠️  Migration completed with errors:")
                for error in self.migration_stats["errors"]:
                    logger.warning(f"   - {error}")
            
            if validation_success:
                logger.info("✅ Migration completed successfully!")
                return True
            else:
                logger.warning("⚠️  Migration completed but validation found issues")
                return False
                
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            self.migration_stats["errors"].append(f"General migration error: {e}")
            return False


def main():
    """Main migration script"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate SQLite database to PostgreSQL")
    parser.add_argument("--sqlite-path", default="namaskah.db", help="Path to SQLite database")
    parser.add_argument("--postgresql-url", help="PostgreSQL connection URL")
    parser.add_argument("--no-backup", action="store_true", help="Skip PostgreSQL backup")
    parser.add_argument("--dry-run", action="store_true", help="Validate connections only")
    
    args = parser.parse_args()
    
    # Get PostgreSQL URL from environment if not provided
    postgresql_url = args.postgresql_url or os.getenv("DATABASE_URL")
    if not postgresql_url:
        logger.error("❌ PostgreSQL URL must be provided via --postgresql-url or DATABASE_URL environment variable")
        sys.exit(1)
    
    try:
        migrator = SQLiteToPostgreSQLMigrator(args.sqlite_path, postgresql_url)
        
        if args.dry_run:
            logger.info("🔍 Running connection validation only...")
            if migrator.validate_connections():
                logger.info("✅ Dry run successful - connections validated")
                sys.exit(0)
            else:
                logger.error("❌ Dry run failed - connection validation failed")
                sys.exit(1)
        
        # Run full migration
        success = migrator.run_migration(create_backup=not args.no_backup)
        
        if success:
            logger.info("🎉 Migration completed successfully!")
            sys.exit(0)
        else:
            logger.error("❌ Migration failed!")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Migration script failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()