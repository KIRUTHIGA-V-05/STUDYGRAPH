from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict
from datetime import datetime
import uuid


class TokenData(BaseModel):
    user_id: uuid.UUID


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    timezone: str


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: Optional[str]
    timezone: str
    xp: int
    streak: int

    class Config:
        from_attributes = True


class PlannerRequest(BaseModel):
    topic: str
    duration_days: int
    days_per_week: int
    daily_study_minutes: int
    user_context: str = "Undergraduate Student"


class LessonOut(BaseModel):
    id: uuid.UUID
    title: str
    estimated_minutes: int
    order: int
    status: str

    class Config:
        from_attributes = True


class ModuleOut(BaseModel):
    id: uuid.UUID
    title: str
    order: int
    difficulty_weight: Optional[float]
    lessons: List[LessonOut]

    class Config:
        from_attributes = True


class PlannerResponse(BaseModel):
    course_id: uuid.UUID
    title: str
    total_modules: int
    total_lessons: int
    modules: List[ModuleOut]


class SchedulerRequest(BaseModel):
    course_id: uuid.UUID
    start_date: str
    days_per_week: int
    daily_study_minutes: int
    timezone: str


class ScheduledLessonOut(BaseModel):
    lesson_id: uuid.UUID
    lesson_title: str
    scheduled_date: str
    allocated_minutes: int


class SchedulerResponse(BaseModel):
    course_id: uuid.UUID
    total_scheduled: int
    end_date: str
    scheduled_lessons: List[ScheduledLessonOut]


class TodayLessonOut(BaseModel):
    lesson_id: uuid.UUID
    title: str
    estimated_minutes: int
    status: str


class TodayResponse(BaseModel):
    date: str
    lessons: List[TodayLessonOut]


class QuizGenerateRequest(BaseModel):
    lesson_id: uuid.UUID
    module_content: str
    num_questions: int = 5


class QuizSubmitRequest(BaseModel):
    lesson_id: uuid.UUID
    answers: Dict[str, str]


class QuestionEvaluation(BaseModel):
    question_id: str
    is_correct: bool
    correct_answer: str
    explanation: str


class QuizResultResponse(BaseModel):
    score: int
    total_questions: int
    evaluations: List[QuestionEvaluation]
    passed: bool
    xp_earned: int


class CalendarSyncRequest(BaseModel):
    course_id: uuid.UUID
    google_auth_code: str = ""


class CalendarSyncResponse(BaseModel):
    synced: bool
    events_created: int


class ProgressResponse(BaseModel):
    course_id: uuid.UUID
    completed_lessons: int
    total_lessons: int
    completion_percentage: float
    current_streak: int
    total_xp: int
    last_activity: Optional[datetime]


class MarkCompleteRequest(BaseModel):
    lesson_id: uuid.UUID
