"""
Database utility to check if device_name exists in SQLite database.
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from pathlib import Path
from typing import Optional
from app.utils.logger.logger import get_logger

logger = get_logger(__name__)


def get_db_uri():
    """Get SQLite database connection string - same as AUTH service"""
    db_path = os.getenv("SQLITE_DB_PATH")
    
    if db_path:
        return f"sqlite:///{db_path}"
    else:
        # Use shared location in BACKEND directory
        backend_dir = Path(__file__).parent.parent.parent.parent  # Navigate to BACKEND/
        shared_db = backend_dir / "shared_data" / "auth.db"
        shared_db.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{shared_db}"


# Create engine for database queries
engine = create_engine(
    get_db_uri(),
    connect_args={
        "check_same_thread": False,
        "timeout": 20.0,
    },
    pool_pre_ping=True,
    echo=False,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def check_device_exists(device_name: str) -> bool:
    """
    Check if a device_name exists in the item table.
    
    Args:
        device_name: The device name to check
        
    Returns:
        True if device exists, False otherwise
    """
    try:
        db = SessionLocal()
        try:
            # Query to check if device_name exists
            query = text("SELECT COUNT(*) FROM item WHERE device_name = :device_name")
            result = db.execute(query, {"device_name": device_name})
            count = result.scalar()
            
            exists = count > 0
            if exists:
                logger.info(f"Device '{device_name}' found in database")
            else:
                logger.info(f"Device '{device_name}' not found in database")
            
            return exists
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error checking device existence: {e}", exc_info=True)
        # Return False on error to allow processing to continue
        return False


def get_device_info(device_name: str) -> Optional[dict]:
    """
    Get device information from the item table.
    
    Args:
        device_name: The device name to look up
        
    Returns:
        Dictionary with device info or None if not found
    """
    try:
        db = SessionLocal()
        try:
            query = text("""
                SELECT item_id, device_name, price, category, in_store 
                FROM item 
                WHERE device_name = :device_name
            """)
            result = db.execute(query, {"device_name": device_name})
            row = result.fetchone()
            
            if row:
                return {
                    "item_id": row[0],
                    "device_name": row[1],
                    "price": float(row[2]) if row[2] else None,
                    "category": row[3],
                    "in_store": row[4]
                }
            return None
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error getting device info: {e}", exc_info=True)
        return None
