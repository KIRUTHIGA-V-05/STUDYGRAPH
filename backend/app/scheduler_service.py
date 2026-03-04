from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, timedelta

app = FastAPI(title="Scheduler Service - Member 3", version="1.0.0")


# ── Input Models ────────────────────────────────────────────────────────────────

class Lesson(BaseModel):
    lesson_id: str
    title: str
    difficulty: str  # "easy" | "medium" | "hard"

class ScheduleRequest(BaseModel):
    course_id: str
    lessons: List[Lesson]
    start_date: str           # "YYYY-MM-DD"
    study_days_per_week: int  # e.g. 5
    daily_study_minutes: int  # e.g. 120


# ── Output Models ───────────────────────────────────────────────────────────────

class ScheduledLesson(BaseModel):
    lesson_id: str
    title: str
    difficulty: str
    scheduled_date: str
    allocated_minutes: int

class ScheduleResponse(BaseModel):
    course_id: str
    total_lessons: int
    total_days_needed: int
    schedule: List[ScheduledLesson]


# ── Core Logic ──────────────────────────────────────────────────────────────────

DIFFICULTY_WEIGHT = {
    "easy": 1.0,
    "medium": 1.5,
    "hard": 2.0
}

STUDY_DAYS_MAP = {
    1: {0},           # Monday only
    2: {0, 3},        # Mon, Thu
    3: {0, 2, 4},     # Mon, Wed, Fri
    4: {0, 1, 3, 4},  # Mon, Tue, Thu, Fri
    5: {0, 1, 2, 3, 4},  # Mon–Fri
    6: {0, 1, 2, 3, 4, 5},  # Mon–Sat
    7: {0, 1, 2, 3, 4, 5, 6}  # Every day
}

def is_study_day(d: date, study_days_per_week: int) -> bool:
    allowed_weekdays = STUDY_DAYS_MAP.get(study_days_per_week, {0, 1, 2, 3, 4})
    return d.weekday() in allowed_weekdays

def get_allocated_minutes(difficulty: str, daily_study_minutes: int, lessons_today: int) -> int:
    weight = DIFFICULTY_WEIGHT.get(difficulty.lower(), 1.0)
    base = daily_study_minutes / max(lessons_today, 1)
    allocated = int(base * weight)
    return min(allocated, daily_study_minutes)  # never exceed daily limit

def allocate_lessons_per_day(
    lessons: List[Lesson],
    daily_study_minutes: int
) -> List[List[Lesson]]:
    """Groups lessons into day-buckets based on difficulty weights."""
    day_buckets = []
    current_bucket = []
    current_load = 0.0

    for lesson in lessons:
        weight = DIFFICULTY_WEIGHT.get(lesson.difficulty.lower(), 1.0)
        lesson_cost = weight * 30  # base 30 min per unit weight

        if current_load + lesson_cost > daily_study_minutes and current_bucket:
            day_buckets.append(current_bucket)
            current_bucket = [lesson]
            current_load = lesson_cost
        else:
            current_bucket.append(lesson)
            current_load += lesson_cost

    if current_bucket:
        day_buckets.append(current_bucket)

    return day_buckets


# ── API Endpoints ───────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"service": "Scheduler Service", "member": 3, "status": "running"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/schedule", response_model=ScheduleResponse)
def generate_schedule(request: ScheduleRequest):
    # Validate inputs
    if not request.lessons:
        raise HTTPException(status_code=400, detail="No lessons provided.")
    if not (1 <= request.study_days_per_week <= 7):
        raise HTTPException(status_code=400, detail="study_days_per_week must be between 1 and 7.")
    if request.daily_study_minutes < 15:
        raise HTTPException(status_code=400, detail="daily_study_minutes must be at least 15.")

    try:
        start = date.fromisoformat(request.start_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD.")

    # Group lessons into day buckets
    day_buckets = allocate_lessons_per_day(request.lessons, request.daily_study_minutes)

    scheduled = []
    current_date = start
    total_days_used = 0

    for bucket in day_buckets:
        # Find the next valid study day
        while not is_study_day(current_date, request.study_days_per_week):
            current_date += timedelta(days=1)

        lessons_today = len(bucket)

        for lesson in bucket:
            allocated = get_allocated_minutes(
                lesson.difficulty,
                request.daily_study_minutes,
                lessons_today
            )
            scheduled.append(ScheduledLesson(
                lesson_id=lesson.lesson_id,
                title=lesson.title,
                difficulty=lesson.difficulty,
                scheduled_date=current_date.isoformat(),
                allocated_minutes=allocated
            ))

        total_days_used += 1
        current_date += timedelta(days=1)

    return ScheduleResponse(
        course_id=request.course_id,
        total_lessons=len(request.lessons),
        total_days_needed=total_days_used,
        schedule=scheduled
    )