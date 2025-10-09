#!/usr/bin/env python3
"""
Database Management Utility for namaskah Communication Platform
Handles migrations, indexing, optimization, and maintenance operations
"""
import asyncio
import logging
import os
import subprocess
import sys
from datetime import datetime
from typing import Dict, List, Optional

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/namaskah_app")


class DatabaseManager:
    """Comprehensive database management utility"""

    def __init__(self, database_url: str):
        """
        Initialize the database manager

        Args:
            database_url: Database connection URL
        """
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    def run_migrations(self, target_revision: Optional[str] = None) -> bool:
        """
        Run Alembic migrations

        Args:
            target_revision: Specific revision to migrate to (None for latest)

        Returns:
            bool: True if successful
        """
        try:
            cmd = ["alembic", "upgrade"]
            if target_revision:
                cmd.append(target_revision)
            else:
                cmd.append("head")

            logger.info(f"Running migrations: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info("Migrations completed successfully")
                logger.info(result.stdout)
                return True
            else:
                logger.error(f"Migration failed: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Failed to run migrations: {e}")
            return False

    def create_migration(self, message: str, auto_generate: bool = True) -> bool:
        """
        Create a new Alembic migration

        Args:
            message: Migration message
            auto_generate: Whether to auto-generate migration content

        Returns:
            bool: True if successful
        """
        try:
            cmd = ["alembic", "revision"]
            if auto_generate:
                cmd.append("--autogenerate")
            cmd.extend(["-m", message])

            logger.info(f"Creating migration: {message}")
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info("Migration created successfully")
                logger.info(result.stdout)
                return True
            else:
                logger.error(f"Migration creation failed: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Failed to create migration: {e}")
            return False

    def get_migration_status(self) -> Dict:
        """
        Get current migration status

        Returns:
            Dict with migration information
        """
        try:
            # Get current revision
            result = subprocess.run(
                ["alembic", "current"], capture_output=True, text=True
            )
            current_revision = (
                result.stdout.strip() if result.returncode == 0 else "unknown"
            )

            # Get migration history
            result = subprocess.run(
                ["alembic", "history"], capture_output=True, text=True
            )
            history = result.stdout if result.returncode == 0 else "unavailable"

            return {
                "current_revision": current_revision,
                "history": history,
                "status": (
                    "up_to_date" if current_revision != "unknown" else "needs_migration"
                ),
            }

        except Exception as e:
            logger.error(f"Failed to get migration status: {e}")
            return {"status": "error", "error": str(e)}

    def analyze_database_performance(self) -> Dict:
        """
        Analyze database performance and suggest optimizations

        Returns:
            Dict with performance analysis
        """
        with self.SessionLocal() as db:
            try:
                analysis = {
                    "table_sizes": {},
                    "index_usage": {},
                    "slow_queries": [],
                    "recommendations": [],
                }

                # Get table sizes
                table_size_query = """
                    SELECT 
                        schemaname,
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                        pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                """

                try:
                    result = db.execute(text(table_size_query)).fetchall()
                    for row in result:
                        analysis["table_sizes"][row[1]] = {
                            "size": row[2],
                            "size_bytes": row[3],
                        }
                except Exception:
                    # Fallback for non-PostgreSQL databases
                    pass

                # Get index usage statistics
                index_usage_query = """
                    SELECT 
                        schemaname,
                        tablename,
                        indexname,
                        idx_tup_read,
                        idx_tup_fetch
                    FROM pg_stat_user_indexes
                    WHERE schemaname = 'public'
                    ORDER BY idx_tup_read DESC
                """

                try:
                    result = db.execute(text(index_usage_query)).fetchall()
                    for row in result:
                        table_name = row[1]
                        if table_name not in analysis["index_usage"]:
                            analysis["index_usage"][table_name] = []

                        analysis["index_usage"][table_name].append(
                            {"index_name": row[2], "reads": row[3], "fetches": row[4]}
                        )
                except Exception:
                    # Fallback for non-PostgreSQL databases
                    pass

                # Generate recommendations
                analysis["recommendations"] = (
                    self._generate_performance_recommendations(analysis)
                )

                return analysis

            except Exception as e:
                logger.error(f"Failed to analyze database performance: {e}")
                return {"error": str(e)}

    def _generate_performance_recommendations(self, analysis: Dict) -> List[str]:
        """Generate performance recommendations based on analysis"""
        recommendations = []

        # Check for large tables without proper indexing
        for table_name, size_info in analysis["table_sizes"].items():
            if size_info["size_bytes"] > 100 * 1024 * 1024:  # > 100MB
                recommendations.append(
                    f"Large table '{table_name}' ({size_info['size']}) - consider partitioning or archiving old data"
                )

        # Check for unused indexes
        for table_name, indexes in analysis["index_usage"].items():
            for index in indexes:
                if index["reads"] == 0:
                    recommendations.append(
                        f"Unused index '{index['index_name']}' on table '{table_name}' - consider dropping"
                    )

        return recommendations

    def optimize_database(
        self, vacuum_analyze: bool = True, reindex: bool = False
    ) -> Dict:
        """
        Optimize database performance

        Args:
            vacuum_analyze: Whether to run VACUUM ANALYZE
            reindex: Whether to reindex tables

        Returns:
            Dict with optimization results
        """
        results = {"vacuum_analyze": False, "reindex": False, "errors": []}

        with self.SessionLocal() as db:
            try:
                if vacuum_analyze:
                    logger.info("Running VACUUM ANALYZE...")
                    db.execute(text("VACUUM ANALYZE"))
                    results["vacuum_analyze"] = True
                    logger.info("VACUUM ANALYZE completed")

                if reindex:
                    logger.info("Reindexing database...")
                    # Get all tables
                    inspector = inspect(self.engine)
                    tables = inspector.get_table_names()

                    for table in tables:
                        try:
                            db.execute(text(f"REINDEX TABLE {table}"))
                            logger.info(f"Reindexed table: {table}")
                        except Exception as e:
                            error_msg = f"Failed to reindex table {table}: {e}"
                            results["errors"].append(error_msg)
                            logger.warning(error_msg)

                    results["reindex"] = True

                db.commit()

            except Exception as e:
                error_msg = f"Database optimization failed: {e}"
                results["errors"].append(error_msg)
                logger.error(error_msg)

        return results

    def backup_database(self, backup_path: str, compress: bool = True) -> bool:
        """
        Create database backup

        Args:
            backup_path: Path for backup file
            compress: Whether to compress the backup

        Returns:
            bool: True if successful
        """
        try:
            # Extract database connection info
            from urllib.parse import urlparse

            parsed = urlparse(self.database_url)

            cmd = [
                "pg_dump",
                "-h",
                parsed.hostname or "localhost",
                "-p",
                str(parsed.port or 5432),
                "-U",
                parsed.username or "postgres",
                "-d",
                parsed.path.lstrip("/") if parsed.path else "namaskah",
                "-f",
                backup_path,
            ]

            if compress:
                cmd.extend(["-Z", "9"])  # Maximum compression

            logger.info(f"Creating database backup: {backup_path}")

            # Set password via environment variable
            env = os.environ.copy()
            if parsed.password:
                env["PGPASSWORD"] = parsed.password

            result = subprocess.run(cmd, env=env, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info("Database backup completed successfully")
                return True
            else:
                logger.error(f"Database backup failed: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Failed to create database backup: {e}")
            return False

    def restore_database(self, backup_path: str, drop_existing: bool = False) -> bool:
        """
        Restore database from backup

        Args:
            backup_path: Path to backup file
            drop_existing: Whether to drop existing database first

        Returns:
            bool: True if successful
        """
        try:
            # Extract database connection info
            from urllib.parse import urlparse

            parsed = urlparse(self.database_url)

            if drop_existing:
                logger.warning("Dropping existing database...")
                # This is dangerous - implement with caution

            cmd = [
                "pg_restore",
                "-h",
                parsed.hostname or "localhost",
                "-p",
                str(parsed.port or 5432),
                "-U",
                parsed.username or "postgres",
                "-d",
                parsed.path.lstrip("/") if parsed.path else "namaskah",
                "-v",
                backup_path,
            ]

            logger.info(f"Restoring database from: {backup_path}")

            # Set password via environment variable
            env = os.environ.copy()
            if parsed.password:
                env["PGPASSWORD"] = parsed.password

            result = subprocess.run(cmd, env=env, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info("Database restore completed successfully")
                return True
            else:
                logger.error(f"Database restore failed: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Failed to restore database: {e}")
            return False

    def check_database_health(self) -> Dict:
        """
        Check database health and connectivity

        Returns:
            Dict with health status
        """
        health_status = {
            "connected": False,
            "migration_status": "unknown",
            "table_count": 0,
            "issues": [],
        }

        try:
            # Test connection
            with self.SessionLocal() as db:
                db.execute(text("SELECT 1"))
                health_status["connected"] = True

                # Count tables
                inspector = inspect(self.engine)
                tables = inspector.get_table_names()
                health_status["table_count"] = len(tables)

                # Check migration status
                migration_status = self.get_migration_status()
                health_status["migration_status"] = migration_status["status"]

                # Check for common issues
                if health_status["table_count"] == 0:
                    health_status["issues"].append(
                        "No tables found - database may not be initialized"
                    )

                if migration_status["status"] == "needs_migration":
                    health_status["issues"].append("Database migrations are pending")

        except Exception as e:
            health_status["issues"].append(f"Database connection failed: {e}")

        return health_status


async def main():
    """Main function for database management operations"""
    import argparse

    parser = argparse.ArgumentParser(description="Database management utility")
    parser.add_argument(
        "command",
        choices=[
            "migrate",
            "create-migration",
            "status",
            "analyze",
            "optimize",
            "backup",
            "restore",
            "health",
        ],
        help="Management command to run",
    )

    parser.add_argument("--message", help="Migration message (for create-migration)")
    parser.add_argument("--revision", help="Target revision (for migrate)")
    parser.add_argument("--backup-path", help="Backup file path (for backup/restore)")
    parser.add_argument(
        "--vacuum", action="store_true", help="Run VACUUM ANALYZE (for optimize)"
    )
    parser.add_argument(
        "--reindex", action="store_true", help="Reindex tables (for optimize)"
    )
    parser.add_argument(
        "--drop-existing",
        action="store_true",
        help="Drop existing database (for restore)",
    )
    parser.add_argument(
        "--database-url", help="Database URL (overrides environment variable)"
    )

    args = parser.parse_args()

    database_url = args.database_url or DATABASE_URL
    db_manager = DatabaseManager(database_url)

    try:
        if args.command == "migrate":
            success = db_manager.run_migrations(args.revision)
            return 0 if success else 1

        elif args.command == "create-migration":
            if not args.message:
                print("Error: --message is required for create-migration")
                return 1
            success = db_manager.create_migration(args.message)
            return 0 if success else 1

        elif args.command == "status":
            status = db_manager.get_migration_status()
            print(f"Current revision: {status['current_revision']}")
            print(f"Status: {status['status']}")
            if "error" in status:
                print(f"Error: {status['error']}")

        elif args.command == "analyze":
            analysis = db_manager.analyze_database_performance()
            print("\n=== Database Performance Analysis ===")

            if "error" in analysis:
                print(f"Error: {analysis['error']}")
                return 1

            print("\nTable Sizes:")
            for table, info in analysis["table_sizes"].items():
                print(f"  {table}: {info['size']}")

            print(f"\nRecommendations ({len(analysis['recommendations'])}):")
            for rec in analysis["recommendations"]:
                print(f"  - {rec}")

        elif args.command == "optimize":
            results = db_manager.optimize_database(
                vacuum_analyze=args.vacuum, reindex=args.reindex
            )
            print("=== Database Optimization Results ===")
            print(f"VACUUM ANALYZE: {'✓' if results['vacuum_analyze'] else '✗'}")
            print(f"REINDEX: {'✓' if results['reindex'] else '✗'}")

            if results["errors"]:
                print(f"\nErrors ({len(results['errors'])}):")
                for error in results["errors"]:
                    print(f"  - {error}")

        elif args.command == "backup":
            if not args.backup_path:
                print("Error: --backup-path is required for backup")
                return 1
            success = db_manager.backup_database(args.backup_path)
            return 0 if success else 1

        elif args.command == "restore":
            if not args.backup_path:
                print("Error: --backup-path is required for restore")
                return 1
            success = db_manager.restore_database(args.backup_path, args.drop_existing)
            return 0 if success else 1

        elif args.command == "health":
            health = db_manager.check_database_health()
            print("=== Database Health Check ===")
            print(f"Connected: {'✓' if health['connected'] else '✗'}")
            print(f"Migration Status: {health['migration_status']}")
            print(f"Table Count: {health['table_count']}")

            if health["issues"]:
                print(f"\nIssues ({len(health['issues'])}):")
                for issue in health["issues"]:
                    print(f"  - {issue}")
            else:
                print("\n✓ No issues detected")

    except Exception as e:
        logger.error(f"Command failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))
