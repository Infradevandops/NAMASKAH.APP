#!/usr/bin/env python3
"""
Database migration validation for Namaskah.App
Ensures safe database operations and migration integrity
"""
import logging
from typing import Dict, List, Tuple
from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError

from core.database import engine, Base

logger = logging.getLogger(__name__)


def validate_database_connection() -> Tuple[bool, str]:
    """
    Test database connection and basic operations
    
    Returns:
        Tuple of (is_connected, error_message)
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            test_value = result.fetchone()[0]
            if test_value == 1:
                return True, "Database connection successful"
            else:
                return False, "Database connection test failed"
    except Exception as e:
        return False, f"Database connection failed: {str(e)}"


def check_migration_safety() -> Dict[str, any]:
    """
    Check if database is ready for safe migrations
    
    Returns:
        Dictionary with safety check results
    """
    safety_report = {
        "connection": False,
        "schema_exists": False,
        "tables_count": 0,
        "foreign_keys_valid": True,
        "indexes_valid": True,
        "warnings": [],
        "errors": []
    }
    
    try:
        # Test connection
        is_connected, conn_msg = validate_database_connection()
        safety_report["connection"] = is_connected
        
        if not is_connected:
            safety_report["errors"].append(conn_msg)
            return safety_report
        
        # Check existing schema
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        safety_report["tables_count"] = len(existing_tables)
        safety_report["schema_exists"] = len(existing_tables) > 0
        
        # Check for potential conflicts
        metadata_tables = list(Base.metadata.tables.keys())
        conflicting_tables = set(existing_tables) & set(metadata_tables)
        
        if conflicting_tables:
            safety_report["warnings"].append(
                f"Tables already exist: {', '.join(conflicting_tables)}"
            )
        
        # Validate foreign key constraints
        fk_issues = validate_foreign_keys(inspector, existing_tables)
        if fk_issues:
            safety_report["foreign_keys_valid"] = False
            safety_report["errors"].extend(fk_issues)
        
        # Check for index conflicts
        index_issues = check_index_conflicts(inspector, existing_tables)
        if index_issues:
            safety_report["indexes_valid"] = False
            safety_report["warnings"].extend(index_issues)
            
    except Exception as e:
        safety_report["errors"].append(f"Migration safety check failed: {str(e)}")
    
    return safety_report


def validate_foreign_keys(inspector, existing_tables: List[str]) -> List[str]:
    """Validate foreign key constraints"""
    issues = []
    
    try:
        for table_name in existing_tables:
            foreign_keys = inspector.get_foreign_keys(table_name)
            for fk in foreign_keys:
                referred_table = fk['referred_table']
                if referred_table not in existing_tables:
                    issues.append(
                        f"Foreign key in {table_name} refers to missing table {referred_table}"
                    )
    except Exception as e:
        issues.append(f"Foreign key validation failed: {str(e)}")
    
    return issues


def check_index_conflicts(inspector, existing_tables: List[str]) -> List[str]:
    """Check for potential index conflicts"""
    warnings = []
    
    try:
        for table_name in existing_tables:
            indexes = inspector.get_indexes(table_name)
            index_names = [idx['name'] for idx in indexes if idx['name']]
            
            # Check for duplicate index names
            if len(index_names) != len(set(index_names)):
                warnings.append(f"Duplicate index names found in table {table_name}")
                
    except Exception as e:
        warnings.append(f"Index conflict check failed: {str(e)}")
    
    return warnings


def safe_create_tables() -> Tuple[bool, List[str]]:
    """
    Safely create database tables with validation
    
    Returns:
        Tuple of (success, list_of_messages)
    """
    messages = []
    
    try:
        # Pre-migration validation
        logger.info("Running pre-migration safety checks...")
        safety_report = check_migration_safety()
        
        if safety_report["errors"]:
            return False, safety_report["errors"]
        
        if safety_report["warnings"]:
            for warning in safety_report["warnings"]:
                logger.warning(warning)
                messages.append(f"WARNING: {warning}")
        
        # Check existing tables
        inspector = inspect(engine)
        existing_tables = set(inspector.get_table_names())
        expected_tables = set(Base.metadata.tables.keys())
        
        if existing_tables == expected_tables:
            messages.append("All tables already exist - skipping creation")
            logger.info("✅ Database already initialized - all tables present")
            return True, messages
        
        # Create tables with checkfirst=True to avoid conflicts
        logger.info("Creating missing database tables...")
        try:
            Base.metadata.create_all(bind=engine, checkfirst=True)
        except SQLAlchemyError as e:
            # If we get an index conflict, try to continue
            if "already exists" in str(e).lower():
                logger.warning(f"Index conflict detected but continuing: {e}")
                messages.append(f"WARNING: {str(e)}")
            else:
                raise e
        
        # Post-creation validation
        logger.info("Validating table creation...")
        final_tables = set(inspector.get_table_names())
        
        # Check if we have all required tables
        missing_tables = expected_tables - final_tables
        if missing_tables:
            # Try to create missing tables individually
            for table_name in missing_tables:
                try:
                    table = Base.metadata.tables[table_name]
                    table.create(bind=engine, checkfirst=True)
                    logger.info(f"Created missing table: {table_name}")
                except Exception as e:
                    logger.error(f"Failed to create table {table_name}: {e}")
                    return False, [f"Failed to create table {table_name}: {str(e)}"]
        
        # Final validation - refresh inspector
        inspector = inspect(engine)
        final_tables = set(inspector.get_table_names())
        still_missing = expected_tables - final_tables
        
        if still_missing:
            return False, [f"Failed to create tables: {', '.join(still_missing)}"]
        
        created_count = len(final_tables - existing_tables)
        if created_count > 0:
            messages.append(f"Successfully created {created_count} new tables")
        
        messages.append(f"Database ready with {len(final_tables)} tables")
        logger.info(f"✅ Database initialization completed - {len(final_tables)} tables available")
        
        return True, messages
        
    except SQLAlchemyError as e:
        error_msg = f"Database creation failed: {str(e)}"
        logger.error(error_msg)
        return False, [error_msg]
    except Exception as e:
        error_msg = f"Unexpected error during table creation: {str(e)}"
        logger.error(error_msg)
        return False, [error_msg]


def get_database_health() -> Dict[str, any]:
    """Get comprehensive database health status"""
    
    health = {
        "connection": False,
        "tables": 0,
        "indexes": 0,
        "foreign_keys": 0,
        "issues": [],
        "last_check": None
    }
    
    try:
        # Connection test
        is_connected, _ = validate_database_connection()
        health["connection"] = is_connected
        
        if is_connected:
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            health["tables"] = len(tables)
            
            # Count indexes and foreign keys
            total_indexes = 0
            total_fks = 0
            
            for table in tables:
                indexes = inspector.get_indexes(table)
                fks = inspector.get_foreign_keys(table)
                total_indexes += len(indexes)
                total_fks += len(fks)
            
            health["indexes"] = total_indexes
            health["foreign_keys"] = total_fks
            
            # Run safety checks
            safety = check_migration_safety()
            health["issues"] = safety.get("errors", []) + safety.get("warnings", [])
        
        from datetime import datetime
        health["last_check"] = datetime.utcnow().isoformat()
        
    except Exception as e:
        health["issues"].append(f"Health check failed: {str(e)}")
    
    return health