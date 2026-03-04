from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, date
import uuid

from database import get_db
from dependencies import get_current_user
from models import Course, Module, Lesson, CalendarEvent
from schemas import SchedulerRequest, SchedulerResponse, ScheduledLessonOut, TodayResponse, TodayLessonOut, TokenData

router = APIRouter()


def build_schedule(
    lessons: list,
    start_date: date,
    days_per_week: int,
    daily_study_minutes: int,
) -> list:
    study_days = list(range(days_per_week))
    result = []
    current_date = start_date
    minutes_used_today = 0
    index = 0

    while index < len(lessons):
        if current_date.weekday() in study_days:
            available = daily_study_minutes - minutes_used_today
            while index < len(lessons) and available > 0:
                lesson = lessons[index]
                weight = lesson.difficulty_weight if hasattr(lesson, "difficulty_weight") else 1.0
                allocated = min(int((lesson.estimated_minutes or 30) * (weight or 1.0)), available)
                allocated = max(allocated, 10)
                result.append({
                    "lesson": lesson,
                    "scheduled_date": current_date.isoformat(),
                    "allocated_minutes": allocated,
                })
                available -= allocated
                minutes_used_today += allocated
                index += 1
        current_date += timedelta(days=1)
        minutes_used_today = 0

    return result


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
        .order_by(Module.order, Lesson.order)
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid start_date format. Use YYYY-MM-DD.",
        )

    scheduled = build_schedule(
        lessons=lessons,
        start_date=start,
        days_per_week=body.days_per_week,
        daily_study_minutes=body.daily_study_minutes,
    )

    db.commit()

    end_date = scheduled[-1]["scheduled_date"] if scheduled else body.start_date

    return SchedulerResponse(
        course_id=body.course_id,
        total_scheduled=len(scheduled),
        end_date=end_date,
        scheduled_lessons=[
            ScheduledLessonOut(
                lesson_id=e["lesson"].id,
                lesson_title=e["lesson"].title,
                scheduled_date=e["scheduled_date"],
                allocated_minutes=e["allocated_minutes"],
            )
            for e in scheduled
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

    lessons = (
        db.query(Lesson)
        .join(Module)
        .filter(Module.course_id == course_id, Lesson.status == "pending")
        .order_by(Module.order, Lesson.order)
        .limit(5)
        .all()
    )

    return TodayResponse(
        date=date.today().isoformat(),
        lessons=[
            TodayLessonOut(
                lesson_id=l.id,
                title=l.title,
                estimated_minutes=l.estimated_minutes,
                status=l.status,
            )
            for l in lessons
        ],
    )
