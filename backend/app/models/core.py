from sqlalchemy import Column, String, Integer, JSON, Boolean, ForeignKey, Float, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from app.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    xp = Column(Integer, default=0)
    # Adding other columns if needed for completeness based on schema
    streak = Column(Integer, default=0)

class XPTracker(Base):
    __tablename__ = "xp_tracker"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    amount = Column(Integer, nullable=False)
    reason = Column(String(255))
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Lesson(Base):
    __tablename__ = "lessons"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module_id = Column(UUID(as_uuid=True))
    title = Column(String(255))
    # Other columns can be added as needed
