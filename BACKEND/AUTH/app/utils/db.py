from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Text, DateTime, Numeric, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from app.config.base_config import SQLConfig

Base = declarative_base()

def get_db_uri():
    config = SQLConfig()
    DATABASE_URL = f"postgresql+psycopg2://{config.user}:{config.password}@{config.host}:{config.port}/{config.database}?sslmode=require"
    return DATABASE_URL

engine = create_engine(get_db_uri(), poolclass=NullPool)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------------
# Models
# -------------------------

class CustomerInfo(Base):
    __tablename__ = "customer_info"

    user_id = Column(String(50), primary_key=True)
    customer_name = Column(String(100), nullable=False)
    address = Column(String(255))
    age = Column(Integer)
    customer_phone = Column(String(20), unique=True)
    password = Column(String(255), nullable=False)
    email = Column(String(100))
    role = Column(String(50))
    # Relationships
    orders = relationship("Order", back_populates="customer")
    bookings = relationship("Booking", back_populates="customer")
    tickets = relationship("Ticket", back_populates="customer")


class Item(Base):
    __tablename__ = "item"

    item_id = Column(Integer, primary_key=True, autoincrement=True)
    device_name = Column(String(100), unique=True, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    category = Column(String(50))
    in_store = Column(Integer)

    # Relationships
    orders = relationship("Order", back_populates="item")


class Order(Base):
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
    user_id = Column(String(50), ForeignKey("customer_info.user_id"))

    __table_args__ = (
        CheckConstraint("quantity > 0", name="check_quantity_positive"),
        CheckConstraint(
            "status IN ('Processing', 'Shipped', 'Canceled', 'Returned', 'Received')",
            name="check_order_status"
        ),
    )

    # Relationships
    customer = relationship("CustomerInfo", back_populates="orders")
    item = relationship("Item", back_populates="orders")


class Booking(Base):
    __tablename__ = "booking"

    booking_id = Column(String(20), primary_key=True)
    customer_name = Column(String(100))
    customer_phone = Column(String(20))
    reason = Column(String(255), nullable=False)
    time = Column(DateTime, nullable=False)
    note = Column(String(255))
    status = Column(String(20))
    user_id = Column(String(50), ForeignKey("customer_info.user_id"))

    __table_args__ = (
        CheckConstraint(
            "status IN ('Scheduled', 'Canceled', 'Finished')",
            name="check_booking_status"
        ),
    )

    customer = relationship("CustomerInfo", back_populates="bookings")


class Ticket(Base):
    __tablename__ = "ticket"

    ticket_id = Column(String(50), primary_key=True)
    content = Column(Text)
    description = Column(Text)
    customer_name = Column(String(100))
    customer_phone = Column(String(20))
    time = Column(DateTime)
    status = Column(String(20))
    user_id = Column(String(50), ForeignKey("customer_info.user_id"))

    __table_args__ = (
        CheckConstraint(
            "status IN ('Pending', 'Resolving', 'Canceled', 'Finished')",
            name="check_ticket_status"
        ),
    )

    customer = relationship("CustomerInfo", back_populates="tickets")
