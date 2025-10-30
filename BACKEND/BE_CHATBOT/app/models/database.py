from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Text, DateTime, Numeric, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
import enum

Base = declarative_base()

# -------------------------
# Database connection (SQLite)
# -------------------------

def get_db_uri():
    # Use a local SQLite database file shared within BE_CHATBOT service
    # In Docker, this will be on a shared volume at /app/data
    # Locally, use a shared path in BACKEND directory
    import os
    from pathlib import Path
    
    # Get the database path from environment variable
    db_path = os.getenv("SQLITE_DB_PATH")
    
    if db_path:
        # Use environment variable (Docker or custom path)
        return f"sqlite:///{db_path}"
    else:
        # Default: Use shared location in BACKEND directory for local development
        backend_dir = Path(__file__).parent.parent.parent.parent  # Navigate to BACKEND/
        shared_db = backend_dir / "shared_data" / "auth.db"
        shared_db.parent.mkdir(parents=True, exist_ok=True)  # Create directory if needed
        return f"sqlite:///{shared_db}"

engine = create_engine(
    get_db_uri(),
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------------
# Status Enums
# -------------------------

class OrderStatusEnum(str, enum.Enum):
    Processing = "Processing"
    Shipped = "Shipped"
    Canceled = "Canceled"
    Returned = "Returned"
    Received = "Received"

class BookingStatusEnum(str, enum.Enum):
    Scheduled = "Scheduled"
    Canceled = "Canceled"
    Finished = "Finished"

class TicketStatusEnum(str, enum.Enum):
    Pending = "Pending"
    Resolving = "Resolving"
    Canceled = "Canceled"
    Finished = "Finished"

# -------------------------
# Models
# -------------------------

class CustomerInfo(Base):
    """Customer information model"""
    __tablename__ = "customer_info"

    user_id = Column(String(50), primary_key=True)
    customer_name = Column(String(100), nullable=False)
    address = Column(String(255))
    age = Column(Integer)
    customer_phone = Column(String(20), unique=True)
    password = Column(String(255), nullable=False)
    email = Column(Text, nullable=False)
    role = Column(Text, nullable=False)
    
    # Relationships
    orders = relationship("Order", back_populates="customer")
    bookings = relationship("Booking", back_populates="customer")
    tickets = relationship("Ticket", back_populates="customer")


class Item(Base):
    """Item/product model"""
    __tablename__ = "item"
    
    item_id = Column(Integer, primary_key=True, autoincrement=True)
    device_name = Column(String(100), unique=True, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    category = Column(String(50))
    in_store = Column(Integer)
    
    # Relationships
    orders = relationship("Order", back_populates="item")


class Order(Base):
    """Order model"""
    __tablename__ = "orders"

    order_id = Column(String(20), primary_key=True)
    device_name = Column(String(100), ForeignKey("item.device_name"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(18, 2), nullable=False, default=0)
    payment = Column(String(50), default='cash on delivery')
    shipping = Column(Boolean, default=True)
    time_reservation = Column(DateTime)
    address = Column(String(255))
    customer_name = Column(String(100))
    customer_phone = Column(String(20))
    status = Column(String(20))
    __table_args__ = (
        CheckConstraint(
            "status IN ('Processing', 'Shipped', 'Canceled', 'Returned', 'Received')",
            name="check_order_status",
        ),
    )
    user_id = Column(String(50), ForeignKey("customer_info.user_id"))
    
    # Relationships
    customer = relationship("CustomerInfo", back_populates="orders")
    item = relationship("Item", back_populates="orders")


class Booking(Base):
    """Booking appointment model"""
    __tablename__ = "booking"

    booking_id = Column(String(20), primary_key=True)
    customer_name = Column(String(100))
    customer_phone = Column(String(20))
    reason = Column(String(255), nullable=False)
    time = Column(DateTime, nullable=False)
    note = Column(String(255))
    status = Column(String(20))
    __table_args__ = (
        CheckConstraint(
            "status IN ('Scheduled', 'Canceled', 'Finished')",
            name="check_booking_status",
        ),
    )
    user_id = Column(String(50), ForeignKey("customer_info.user_id"))
    
    # Relationship
    customer = relationship("CustomerInfo", back_populates="bookings")


class Ticket(Base):
    """IT support ticket model"""
    __tablename__ = "ticket"

    ticket_id = Column(String(50), primary_key=True)
    content = Column(Text)
    description = Column(Text)
    customer_name = Column(String(100))
    customer_phone = Column(String(20))
    time = Column(DateTime)
    status = Column(String(20))
    __table_args__ = (
        CheckConstraint(
            "status IN ('Pending', 'Resolving', 'Canceled', 'Finished')",
            name="check_ticket_status",
        ),
    )
    user_id = Column(String(50), ForeignKey("customer_info.user_id"))
    
    # Relationship
    customer = relationship("CustomerInfo", back_populates="tickets")

# Ensure tables exist on startup
Base.metadata.create_all(bind=engine)
