#!/usr/bin/env python3
"""
Database Cleanup and Maintenance Script for CumApp Communication Platform
Handles data retention, archiving, and cleanup operations
"""
import asyncio
import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv
from sqlalchemy import create_engine, func, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/namaskah_app")


class DatabaseCleanupManager:
    """Manages database cleanup and retention operations"""

    def __init__(self, database_url: str):
        """
        Initialize the cleanup manager

        Args:
            database_url: Database connection URL
        """
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    def get_db_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()

    async def run_cleanup_job(
        self, job_type: str, table_name: str, dry_run: bool = False
    ) -> Dict:
        """
        Run a cleanup job

        Args:
            job_type: Type of cleanup (archive, delete, full_cleanup)
            table_name: Target table name
            dry_run: If True, only simulate the operation

        Returns:
            Dict with cleanup results
        """
        job_id = str(uuid.uuid4())

        with self.get_db_session() as db:
            try:
                # Create cleanup job record
                job_data = {
                    "id": job_id,
                    "job_type": job_type,
                    "table_name": table_name,
                    "status": "running",
                    "started_at": datetime.utcnow(),
                }

                if not dry_run:
                    db.execute(
                        text(
                            """
                        INSERT INTO cleanup_jobs (id, job_type, table_name, status, started_at, created_at)
                        VALUES (:id, :job_type, :table_name, :status, :started_at, :created_at)
                    """
                        ),
                        {**job_data, "created_at": datetime.utcnow()},
                    )

                # Get retention policy for table
                policy = self._get_retention_policy(db, table_name)
                if not policy:
                    raise ValueError(
                        f"No retention policy found for table: {table_name}"
                    )

                results = {
                    "job_id": job_id,
                    "table_name": table_name,
                    "job_type": job_type,
                }

                if job_type == "archive":
                    results.update(
                        await self._archive_records(db, table_name, policy, dry_run)
                    )
                elif job_type == "delete":
                    results.update(
                        await self._delete_expired_records(db, table_name, dry_run)
                    )
                elif job_type == "full_cleanup":
                    archive_results = await self._archive_records(
                        db, table_name, policy, dry_run
                    )
                    delete_results = await self._delete_expired_records(
                        db, table_name, dry_run
                    )
                    results.update(
                        {
                            "records_archived": archive_results.get(
                                "records_archived", 0
                            ),
                            "records_deleted": delete_results.get("records_deleted", 0),
                            "records_processed": archive_results.get(
                                "records_processed", 0
                            )
                            + delete_results.get("records_processed", 0),
                        }
                    )

                # Update job status
                if not dry_run:
                    db.execute(
                        text(
                            """
                        UPDATE cleanup_jobs 
                        SET status = 'completed', 
                            completed_at = :completed_at,
                            records_processed = :records_processed,
                            records_archived = :records_archived,
                            records_deleted = :records_deleted
                        WHERE id = :job_id
                    """
                        ),
                        {
                            "job_id": job_id,
                            "completed_at": datetime.utcnow(),
                            "records_processed": results.get("records_processed", 0),
                            "records_archived": results.get("records_archived", 0),
                            "records_deleted": results.get("records_deleted", 0),
                        },
                    )
                    db.commit()

                logger.info(f"Cleanup job {job_id} completed successfully: {results}")
                return results

            except Exception as e:
                logger.error(f"Cleanup job {job_id} failed: {e}")

                if not dry_run:
                    db.execute(
                        text(
                            """
                        UPDATE cleanup_jobs 
                        SET status = 'failed', 
                            completed_at = :completed_at,
                            error_message = :error_message
                        WHERE id = :job_id
                    """
                        ),
                        {
                            "job_id": job_id,
                            "completed_at": datetime.utcnow(),
                            "error_message": str(e),
                        },
                    )
                    db.commit()

                raise

    def _get_retention_policy(self, db: Session, table_name: str) -> Optional[Dict]:
        """Get retention policy for a table"""
        result = db.execute(
            text(
                """
            SELECT retention_days, archive_after_days, delete_after_days, conditions
            FROM data_retention_policies
            WHERE table_name = :table_name AND is_active = true
            LIMIT 1
        """
            ),
            {"table_name": table_name},
        ).fetchone()

        if result:
            return {
                "retention_days": result[0],
                "archive_after_days": result[1],
                "delete_after_days": result[2],
                "conditions": result[3] or {},
            }
        return None

    async def _archive_records(
        self, db: Session, table_name: str, policy: Dict, dry_run: bool = False
    ) -> Dict:
        """Archive old records based on retention policy"""
        archive_after_days = policy.get("archive_after_days")
        if not archive_after_days:
            return {"records_processed": 0, "records_archived": 0}

        archive_date = datetime.utcnow() - timedelta(days=archive_after_days)
        retention_days = policy.get("retention_days", archive_after_days * 2)

        # Build query based on table structure
        if table_name in [
            "verification_requests",
            "communication_messages",
            "voice_calls",
            "verification_messages",
            "payments",
            "usage_records",
        ]:

            # Check if table has retention columns
            has_retention_columns = self._table_has_retention_columns(db, table_name)

            if has_retention_columns:
                if dry_run:
                    # Count records that would be archived
                    result = db.execute(
                        text(
                            f"""
                        SELECT COUNT(*) 
                        FROM {table_name}
                        WHERE created_at < :archive_date 
                        AND (is_archived = false OR is_archived IS NULL)
                    """
                        ),
                        {"archive_date": archive_date},
                    ).fetchone()

                    records_count = result[0] if result else 0
                    return {
                        "records_processed": records_count,
                        "records_archived": records_count,
                    }
                else:
                    # Actually archive the records
                    retention_until = datetime.utcnow() + timedelta(days=retention_days)

                    result = db.execute(
                        text(
                            f"""
                        UPDATE {table_name}
                        SET is_archived = true,
                            retention_until = :retention_until
                        WHERE created_at < :archive_date 
                        AND (is_archived = false OR is_archived IS NULL)
                    """
                        ),
                        {
                            "archive_date": archive_date,
                            "retention_until": retention_until,
                        },
                    )

                    records_archived = result.rowcount
                    return {
                        "records_processed": records_archived,
                        "records_archived": records_archived,
                    }

        return {"records_processed": 0, "records_archived": 0}

    async def _delete_expired_records(
        self, db: Session, table_name: str, dry_run: bool = False
    ) -> Dict:
        """Delete expired records based on retention policy"""

        # Check if table has retention columns
        has_retention_columns = self._table_has_retention_columns(db, table_name)

        if not has_retention_columns:
            return {"records_processed": 0, "records_deleted": 0}

        if dry_run:
            # Count records that would be deleted
            result = db.execute(
                text(
                    f"""
                SELECT COUNT(*) 
                FROM {table_name}
                WHERE retention_until IS NOT NULL 
                AND retention_until < :current_time
                AND is_archived = true
            """
                ),
                {"current_time": datetime.utcnow()},
            ).fetchone()

            records_count = result[0] if result else 0
            return {
                "records_processed": records_count,
                "records_deleted": records_count,
            }
        else:
            # Actually delete the records
            result = db.execute(
                text(
                    f"""
                DELETE FROM {table_name}
                WHERE retention_until IS NOT NULL 
                AND retention_until < :current_time
                AND is_archived = true
            """
                ),
                {"current_time": datetime.utcnow()},
            )

            records_deleted = result.rowcount
            return {
                "records_processed": records_deleted,
                "records_deleted": records_deleted,
            }

    def _table_has_retention_columns(self, db: Session, table_name: str) -> bool:
        """Check if table has retention columns"""
        try:
            result = db.execute(
                text(
                    f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = :table_name 
                AND column_name IN ('retention_until', 'is_archived')
            """
                ),
                {"table_name": table_name},
            ).fetchall()

            return len(result) >= 2
        except Exception:
            return False

    async def run_full_cleanup(self, dry_run: bool = False) -> Dict:
        """Run full cleanup for all tables with retention policies"""

        with self.get_db_session() as db:
            # Get all active retention policies
            policies = db.execute(
                text(
                    """
                SELECT table_name 
                FROM data_retention_policies 
                WHERE is_active = true
            """
                )
            ).fetchall()

            results = {
                "total_tables": len(policies),
                "tables_processed": 0,
                "total_archived": 0,
                "total_deleted": 0,
                "errors": [],
            }

            for policy in policies:
                table_name = policy[0]

                try:
                    cleanup_result = await self.run_cleanup_job(
                        "full_cleanup", table_name, dry_run
                    )
                    results["tables_processed"] += 1
                    results["total_archived"] += cleanup_result.get(
                        "records_archived", 0
                    )
                    results["total_deleted"] += cleanup_result.get("records_deleted", 0)

                    logger.info(f"Cleaned up table {table_name}: {cleanup_result}")

                except Exception as e:
                    error_msg = f"Failed to cleanup table {table_name}: {e}"
                    results["errors"].append(error_msg)
                    logger.error(error_msg)

            return results

    async def get_cleanup_statistics(self) -> Dict:
        """Get cleanup statistics and recommendations"""

        with self.get_db_session() as db:
            stats = {
                "tables": {},
                "total_records_to_archive": 0,
                "total_records_to_delete": 0,
                "storage_savings_estimate": 0,
            }

            # Get policies and analyze each table
            policies = db.execute(
                text(
                    """
                SELECT table_name, retention_days, archive_after_days, delete_after_days
                FROM data_retention_policies 
                WHERE is_active = true
            """
                )
            ).fetchall()

            for policy in policies:
                table_name, retention_days, archive_after_days, delete_after_days = (
                    policy
                )

                try:
                    table_stats = await self._analyze_table_cleanup_needs(
                        db, table_name, archive_after_days
                    )
                    stats["tables"][table_name] = table_stats
                    stats["total_records_to_archive"] += table_stats.get(
                        "records_to_archive", 0
                    )
                    stats["total_records_to_delete"] += table_stats.get(
                        "records_to_delete", 0
                    )

                except Exception as e:
                    logger.warning(f"Could not analyze table {table_name}: {e}")

            return stats

    async def _analyze_table_cleanup_needs(
        self, db: Session, table_name: str, archive_after_days: Optional[int]
    ) -> Dict:
        """Analyze cleanup needs for a specific table"""

        if not self._table_has_retention_columns(db, table_name):
            return {"records_to_archive": 0, "records_to_delete": 0}

        archive_date = datetime.utcnow() - timedelta(days=archive_after_days or 90)

        # Count records to archive
        archive_result = db.execute(
            text(
                f"""
            SELECT COUNT(*) 
            FROM {table_name}
            WHERE created_at < :archive_date 
            AND (is_archived = false OR is_archived IS NULL)
        """
            ),
            {"archive_date": archive_date},
        ).fetchone()

        # Count records to delete
        delete_result = db.execute(
            text(
                f"""
            SELECT COUNT(*) 
            FROM {table_name}
            WHERE retention_until IS NOT NULL 
            AND retention_until < :current_time
            AND is_archived = true
        """
            ),
            {"current_time": datetime.utcnow()},
        ).fetchone()

        return {
            "records_to_archive": archive_result[0] if archive_result else 0,
            "records_to_delete": delete_result[0] if delete_result else 0,
        }


async def main():
    """Main function for running cleanup operations"""
    import argparse

    parser = argparse.ArgumentParser(description="Database cleanup and maintenance")
    parser.add_argument(
        "--operation",
        choices=["archive", "delete", "full_cleanup", "stats"],
        default="stats",
        help="Cleanup operation to perform",
    )
    parser.add_argument("--table", help="Specific table to clean up")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate operation without making changes",
    )
    parser.add_argument(
        "--database-url", help="Database URL (overrides environment variable)"
    )

    args = parser.parse_args()

    database_url = args.database_url or DATABASE_URL
    cleanup_manager = DatabaseCleanupManager(database_url)

    try:
        if args.operation == "stats":
            stats = await cleanup_manager.get_cleanup_statistics()
            print("\n=== Database Cleanup Statistics ===")
            print(f"Total records to archive: {stats['total_records_to_archive']}")
            print(f"Total records to delete: {stats['total_records_to_delete']}")
            print("\nPer-table breakdown:")
            for table, table_stats in stats["tables"].items():
                print(
                    f"  {table}: {table_stats['records_to_archive']} to archive, {table_stats['records_to_delete']} to delete"
                )

        elif args.operation == "full_cleanup":
            print(
                f"\n=== Running Full Cleanup {'(DRY RUN)' if args.dry_run else ''} ==="
            )
            results = await cleanup_manager.run_full_cleanup(dry_run=args.dry_run)
            print(
                f"Tables processed: {results['tables_processed']}/{results['total_tables']}"
            )
            print(f"Total records archived: {results['total_archived']}")
            print(f"Total records deleted: {results['total_deleted']}")
            if results["errors"]:
                print(f"Errors: {len(results['errors'])}")
                for error in results["errors"]:
                    print(f"  - {error}")

        elif args.table:
            print(
                f"\n=== Running {args.operation} on {args.table} {'(DRY RUN)' if args.dry_run else ''} ==="
            )
            results = await cleanup_manager.run_cleanup_job(
                args.operation, args.table, dry_run=args.dry_run
            )
            print(f"Job ID: {results['job_id']}")
            print(f"Records processed: {results.get('records_processed', 0)}")
            print(f"Records archived: {results.get('records_archived', 0)}")
            print(f"Records deleted: {results.get('records_deleted', 0)}")

        else:
            print("Error: --table is required for archive/delete operations")
            return 1

    except Exception as e:
        logger.error(f"Cleanup operation failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))
