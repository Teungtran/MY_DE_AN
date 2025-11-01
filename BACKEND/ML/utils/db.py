from sqlalchemy import Column, String, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os
from pathlib import Path
from typing import Generator

Base = declarative_base()

def get_db_uri():
    """Get SQLite database connection string"""
    # Get the database path from environment variable
    db_path = os.getenv("SQLITE_DB_PATH")
    
    if db_path:
        # Use environment variable (Docker or custom path)
        return f"sqlite:///{db_path}"
    else:
        # Default: Use shared location in BACKEND directory for local development
        backend_dir = Path(__file__).parent.parent.parent  # Navigate to BACKEND/
        shared_db = backend_dir / "shared_data" / "auth.db"
        shared_db.parent.mkdir(parents=True, exist_ok=True)  # Create directory if needed
        return f"sqlite:///{shared_db}"

engine = create_engine(
    get_db_uri(),
    connect_args={
        "check_same_thread": False,  # Needed for SQLite with threaded apps like FastAPI/Uvicorn
        "timeout": 20.0,  # Increase timeout for Docker volume mounts
    },
    pool_pre_ping=True,  # Verify connections before using
    echo=False,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------------
# Models (only CustomerInfo needed for RBAC)
# -------------------------

class CustomerInfo(Base):
    __tablename__ = "customer_info"

    user_id = Column(String(50), primary_key=True)
    customer_name = Column(String(100), nullable=False)
    address = Column(String(255))
    age = Column(Integer)
    customer_phone = Column(String(20), unique=True)
    password = Column(Text, nullable=False)
    email = Column(Text, nullable=False)
    role = Column(Text, nullable=False)

