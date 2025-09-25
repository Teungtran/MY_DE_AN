from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Text, DateTime, Numeric, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine

Base = declarative_base()
def get_db_uri():
    """Get database URI from config"""
    server="DESKTOP-LU731VP\\SQLEXPRESS"
    database="CUSTOMER_SERVICE"
    return f"mssql+pyodbc://{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"


# Create engine
engine = create_engine(get_db_uri())

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class CustomerInfo(Base):
    """Customer information model"""
    __tablename__ = "Customer_info"

    user_id = Column(String(50), primary_key=True)
    customer_name = Column(String(100), nullable=False)
    address = Column(String(255))
    preferences = Column(Text)  # NVARCHAR(MAX)
    age = Column(Integer)
    customer_phone = Column(String(20), unique=True)
    password = Column(String(255), nullable=False)
    email = Column(String(100))
    role = Column(String(50))
    orders = relationship("Order", back_populates="customer")
    bookings = relationship("Booking", back_populates="customer")
    tickets = relationship("Ticket", back_populates="customer")

class Item(Base):
    """Item/product model"""
    __tablename__ = "Item"
    
    item_id = Column(Integer, primary_key=True, autoincrement=True)
    device_name = Column(String(100), unique=True, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    category = Column(String(50))
    in_store = Column(Integer)
    
    # Relationships
    orders = relationship("Order", back_populates="item")

class Order(Base):
    """Order model"""
    __tablename__ = "Order"

    order_id = Column(String(20), primary_key=True)
    device_name = Column(String(100), ForeignKey("Item.device_name"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(18, 2), nullable=False, default=0)
    payment = Column(String(50), default='cash on delivery')
    shipping = Column(Boolean, default=True)
    time_reservation = Column(DateTime)
    address = Column(String(255))
    customer_name = Column(String(100))
    customer_phone = Column(String(20))
    status = Column(String(20))
    user_id = Column(String(50), ForeignKey("Customer_info.user_id"))
    
    __table_args__ = (
        CheckConstraint("quantity > 0", name="check_quantity_positive"),
        CheckConstraint("status IN ('Processing', 'Shipped', 'Canceled', 'Returned', 'Received')", name="check_order_status"),
    )
    
    # Relationships
    customer = relationship("CustomerInfo", back_populates="orders")
    item = relationship("Item", back_populates="orders")

class Booking(Base):
    """Booking appointment model"""
    __tablename__ = "Booking"

    booking_id = Column(String(20), primary_key=True)
    customer_name = Column(String(100))
    customer_phone = Column(String(20))
    reason = Column(String(255), nullable=False)
    time = Column(DateTime, nullable=False)
    note = Column(String(255))
    status = Column(String(20))
    user_id = Column(String(50), ForeignKey("Customer_info.user_id"))
    
    __table_args__ = (
        CheckConstraint("status IN ('Scheduled', 'Canceled', 'Finished')", name="check_booking_status"),
    )
    
    # Relationship
    customer = relationship("CustomerInfo", back_populates="bookings")

class Ticket(Base):
    """IT support ticket model"""
    __tablename__ = "ticket"

    ticket_id = Column(String(50), primary_key=True)
    content = Column(Text)  # NVARCHAR(MAX)
    description = Column(Text)  # NVARCHAR(MAX)
    customer_name = Column(String(100))
    customer_phone = Column(String(20))
    time = Column(DateTime)
    status = Column(String(20))
    user_id = Column(String(50), ForeignKey("Customer_info.user_id"))
    
    __table_args__ = (
        CheckConstraint("status IN ('Pending', 'Resolving', 'Canceled', 'Finished')", name="check_ticket_status"),
    )
    
    # Relationship
    customer = relationship("CustomerInfo", back_populates="tickets") 