"""SQLAlchemy models.

Class datetimes are stored as ISO-8601 strings normalized to IST
(Asia/Kolkata), e.g. "2026-10-20T10:00:00+05:30", per the brief's
timezone requirement.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint

from .config import IST
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class FitnessClass(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    # ISO-8601 string in IST; stored as text so SQLite keeps the offset.
    date_time = Column(String(40), nullable=False)
    instructor = Column(String(100), nullable=False)
    total_slots = Column(Integer, nullable=False)
    available_slots = Column(Integer, nullable=False)


class Booking(Base):
    __tablename__ = "bookings"
    # A user can book the same class only once.
    __table_args__ = (UniqueConstraint("user_id", "class_id", name="uq_user_class"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False, index=True)
    client_name = Column(String(100), nullable=False)
    client_email = Column(String(255), nullable=False)
    booked_at = Column(
        DateTime, default=lambda: datetime.now(ZoneInfo(IST)), nullable=False
    )
