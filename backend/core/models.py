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

    id                       = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email                    = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password          = Column(String(255), nullable=False)
    full_name                = Column(String(255))
    timezone                 = Column(String(50), default="UTC")
    study_days               = Column(JSON, nullable=True)
    daily_duration_minutes   = Column(Integer, nullable=True)
    preferred_learning_style = Column(String(50), nullable=True)
    xp                       = Column(Integer, default=0)
    streak                   = Column(Integer, default=0)

    courses       = relationship("Course", back_populates="user")
    xp_entries    = relationship("XPTracker", back_populates="user")
    progress_logs = relationship("ProgressLog", back_populates="user")


class Course(Base):
    __tablename__ = "courses"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id       = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title         = Column(String(255), nullable=False)
    description   = Column(Text, nullable=True)
    duration_days = Column(Integer, nullable=False)
    created_at    = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user    = relationship("User", back_populates="courses")
    modules = relationship("Module", back_populates="course", order_by="Module.order")


class Module(Base):
    __tablename__ = "modules"

    id                = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id         = Column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False)
    title             = Column(String(255), nullable=False)
    order             = Column(Integer, nullable=False)
    difficulty_weight = Column(Float, nullable=True)

    course  = relationship("Course", back_populates="modules")
    lessons = relationship("Lesson", back_populates="module", order_by="Lesson.order")


class Lesson(Base):
    __tablename__ = "lessons"

    id                = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module_id         = Column(UUID(as_uuid=True), ForeignKey("modules.id"), nullable=False)
    title             = Column(String(255), nullable=False)
    content_type      = Column(String(50), nullable=True)
    estimated_minutes = Column(Integer, default=30)
    order             = Column(Integer, nullable=False)
    status            = Column(String(20), default="pending")

    module         = relationship("Module", back_populates="lessons")
    calendar_event = relationship("CalendarEvent", back_populates="lesson", uselist=False)


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lesson_id      = Column(UUID(as_uuid=True), ForeignKey("lessons.id"), nullable=False)
    question_text  = Column(Text, nullable=False)
    options        = Column(JSON, nullable=False)
    correct_answer = Column(String(255), nullable=False)
    explanation    = Column(Text, nullable=True)


class QuizResult(Base):
    __tablename__ = "quiz_results"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id         = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    lesson_id       = Column(UUID(as_uuid=True), ForeignKey("lessons.id"), nullable=False)
    score           = Column(Integer, nullable=False)
    total_questions = Column(Integer, nullable=False)
    completed_at    = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id         = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    lesson_id       = Column(UUID(as_uuid=True), ForeignKey("lessons.id"), unique=True, nullable=False)
    google_event_id = Column(String(255), nullable=True)
    start_time      = Column(DateTime, nullable=True)
    end_time        = Column(DateTime, nullable=True)

    lesson = relationship("Lesson", back_populates="calendar_event")


class ProgressLog(Base):
    __tablename__ = "progress_logs"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id          = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    lesson_id        = Column(UUID(as_uuid=True), ForeignKey("lessons.id"), nullable=False)
    activity_type    = Column(String(50), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    timestamp        = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="progress_logs")


class XPTracker(Base):
    __tablename__ = "xp_tracker"

    id        = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id   = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    amount    = Column(Integer, nullable=False)
    reason    = Column(String(255), nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="xp_entries")


class BurnoutMetric(Base):
    __tablename__ = "burnout_metrics"

    id                = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id           = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    daily_score       = Column(Float, nullable=True)
    missed_days_count = Column(Integer, nullable=True)
    avg_quiz_score    = Column(Float, nullable=True)
    timestamp         = Column(DateTime, default=lambda: datetime.now(timezone.utc))
