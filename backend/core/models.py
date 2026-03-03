from sqlalchemy import (
    Column, String, Integer, Float, Boolean,
    ForeignKey, DateTime, Text, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from database import Base


class User(Base):
    __tablename__ = "users"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email           = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name       = Column(String(255))
    timezone        = Column(String(100), default="UTC")
    xp              = Column(Integer, default=0)
    streak          = Column(Integer, default=0)
    last_activity   = Column(DateTime, nullable=True)
    created_at      = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    courses = relationship("Course", back_populates="user")


class Course(Base):
    __tablename__ = "courses"

    id                  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id             = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    topic               = Column(String(255), nullable=False)
    target_days         = Column(Integer, nullable=False)
    days_per_week       = Column(Integer, nullable=False)
    daily_study_minutes = Column(Integer, nullable=False)
    status              = Column(String(50), default="active")
    created_at          = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user    = relationship("User", back_populates="courses")
    modules = relationship("Module", back_populates="course", order_by="Module.order_index")


class Module(Base):
    __tablename__ = "modules"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id       = Column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False)
    module_ref_id   = Column(String(50))
    title           = Column(String(255), nullable=False)
    description     = Column(Text)
    order_index     = Column(Integer, nullable=False)
    quiz_checkpoint = Column(Boolean, default=True)

    course  = relationship("Course", back_populates="modules")
    lessons = relationship("Lesson", back_populates="module", order_by="Lesson.order_index")


class Lesson(Base):
    __tablename__ = "lessons"

    id                = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module_id         = Column(UUID(as_uuid=True), ForeignKey("modules.id"), nullable=False)
    lesson_ref_id     = Column(String(50))
    title             = Column(String(255), nullable=False)
    difficulty        = Column(Integer, default=1)
    estimated_minutes = Column(Integer, default=30)
    order_index       = Column(Integer, nullable=False)

    module   = relationship("Module", back_populates="lessons")
    schedule = relationship("LessonSchedule", back_populates="lesson", uselist=False)


class LessonSchedule(Base):
    __tablename__ = "lesson_schedule"

    id                = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lesson_id         = Column(UUID(as_uuid=True), ForeignKey("lessons.id"), unique=True, nullable=False)
    scheduled_date    = Column(String(20), nullable=False)
    allocated_minutes = Column(Integer, nullable=False)
    status            = Column(String(50), default="pending")
    completed_at      = Column(DateTime, nullable=True)

    lesson = relationship("Lesson", back_populates="schedule")


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lesson_id       = Column(UUID(as_uuid=True), ForeignKey("lessons.id"), unique=True)
    google_event_id = Column(String(255))
    created_at      = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class XPTracker(Base):
    __tablename__ = "xp_tracker"

    id        = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id   = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    amount    = Column(Integer, nullable=False)
    reason    = Column(String(255))
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ProgressLog(Base):
    __tablename__ = "progress_logs"

    id        = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id   = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("lessons.id"))
    action    = Column(String(100))
    logged_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
