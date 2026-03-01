from sqlalchemy import Column, String, Integer, JSON, Boolean, ForeignKey, Float, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from app.database import Base
from app.models.core import User, Lesson  # Added to resolve FKs

class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("lessons.id"))
    question_text = Column(Text, nullable=False)
    options = Column(JSON, nullable=False)  # List[str]
    correct_answer = Column(String(255), nullable=False)
    explanation = Column(Text)

class QuizResult(Base):
    __tablename__ = "quiz_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("lessons.id"))
    score = Column(Integer, nullable=False)
    total_questions = Column(Integer, nullable=False)
    completed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
