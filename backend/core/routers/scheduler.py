from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, date
import uuid

from database import get_db
from dependencies import get_current_user
from models import Course, Module, Lesson, LessonSchedule
from schemas import SchedulerRequest, SchedulerResponse, ScheduledLessonOut, TodayResponse, TodayLessonOut, TokenData

router = APIRouter()


def calculate_schedule(
    lessons: list,
    start_date: date,
    days_per_week: int,
    daily_study_minutes: int,
) -> list:
    study_days_of_week = list(range(days_per_week))
    scheduled = []
    current_date = start_date
    day_minutes_used = 0
    lesson_index = 0

    while lesson_index < len(lessons):
        if current_date.weekday() in study_days_of_week:
            available = daily_study_minutes - day_minutes_used

            while lesson_index < len(lessons) and available > 0:
                lesson = lessons[lesson_index]
                difficulty_weight = 1 + (lesson.difficulty - 1) * 0.2
                allocated = min(int(lesson.estimated_minutes * difficulty_weight), available)
                allocated = max(allocated, 10)

                scheduled.append({
                    "lesson": lesson,
                    "scheduled_date": current_date.isoformat(),
                    "allocated_minutes": allocated,
                })
                available -= allocated
                day_minutes_used += allocated
                lesson_index += 1

        current_date += timedelta(days=1)
        day_minutes_used = 0

    return scheduled


@router.post("/assign", response_model=SchedulerResponse, status_code=status.HTTP_201_CREATED)
def assign_schedule(
    body: SchedulerRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    course = (
        db.query(Course)
        .filter(Course.id == body.course_id, Course.user_id == current_user.user_id)
        .first()
    )
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found.")

    lessons = (
        db.query(Lesson)
        .join(Module)
        .filter(Module.course_id == body.course_id)
        .order_by(Module.order_index, Lesson.order_index)
        .all()
    )

    if not lessons:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No lessons found. Generate a plan first.",
        )

    try:
        start = date.fromisoformat(body.start_date)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid start_date format. Use YYYY-MM-DD.")

    scheduled_entries = calculate_schedule(
        lessons=lessons,
        start_date=start,
        days_per_week=body.days_per_week,
        daily_study_minutes=body.daily_study_minutes,
    )

    for entry in scheduled_entries:
        existing = db.query(LessonSchedule).filter(LessonSchedule.lesson_id == entry["lesson"].id).first()
        if existing:
            existing.scheduled_date = entry["scheduled_date"]
            existing.allocated_minutes = entry["allocated_minutes"]
            existing.status = "pending"
        else:
            schedule = LessonSchedule(
                lesson_id=entry["lesson"].id,
                scheduled_date=entry["scheduled_date"],
                allocated_minutes=entry["allocated_minutes"],
            )
            db.add(schedule)

    db.commit()

    end_date = scheduled_entries[-1]["scheduled_date"] if scheduled_entries else body.start_date

    return SchedulerResponse(
        course_id=body.course_id,
        total_scheduled=len(scheduled_entries),
        end_date=end_date,
        scheduled_lessons=[
            ScheduledLessonOut(
                lesson_id=e["lesson"].id,
                lesson_title=e["lesson"].title,
                scheduled_date=e["scheduled_date"],
                allocated_minutes=e["allocated_minutes"],
                status="pending",
            )
            for e in scheduled_entries
        ],
    )


@router.get("/today/{course_id}", response_model=TodayResponse)
def get_todays_lessons(
    course_id: uuid.UUID,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    course = (
        db.query(Course)
        .filter(Course.id == course_id, Course.user_id == current_user.user_id)
        .first()
    )
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found.")

    today_str = date.today().isoformat()

    results = (
        db.query(Lesson, LessonSchedule)
        .join(LessonSchedule, Lesson.id == LessonSchedule.lesson_id)
        .join(Module, Lesson.module_id == Module.id)
        .filter(Module.course_id == course_id, LessonSchedule.scheduled_date == today_str)
        .order_by(Lesson.order_index)
        .all()
    )

    return TodayResponse(
        date=today_str,
        lessons=[
            TodayLessonOut(
                lesson_id=lesson.id,
                title=lesson.title,
                difficulty=lesson.difficulty,
                allocated_minutes=schedule.allocated_minutes,
                status=schedule.status,
            )
            for lesson, schedule in results
        ],
    )
