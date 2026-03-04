from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import httpx
from datetime import date
import uuid

from database import get_db
from dependencies import get_current_user
from config import settings
from models import Course, Module, Lesson
from schemas import SchedulerRequest, SchedulerResponse, ScheduledLessonOut, TodayResponse, TodayLessonOut, TokenData

router = APIRouter()


def difficulty_from_weight(weight) -> str:
    if weight is None:
        return "medium"
    if weight <= 1.0:
        return "easy"
    elif weight <= 1.5:
        return "medium"
    else:
        return "hard"


@router.post("/assign", response_model=SchedulerResponse, status_code=status.HTTP_201_CREATED)
async def assign_schedule(
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
        db.query(Lesson, Module)
        .join(Module, Lesson.module_id == Module.id)
        .filter(Module.course_id == body.course_id)
        .order_by(Module.order, Lesson.order)
        .all()
    )

    if not lessons:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No lessons found. Generate a plan first.",
        )

    lessons_payload = [
        {
            "lesson_id": str(lesson.id),
            "title": lesson.title,
            "difficulty": difficulty_from_weight(module.difficulty_weight),
        }
        for lesson, module in lessons
    ]

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{settings.SCHEDULER_SERVICE_URL}/schedule",
                json={
                    "course_id": str(body.course_id),
                    "lessons": lessons_payload,
                    "start_date": body.start_date,
                    "study_days_per_week": body.days_per_week,
                    "daily_study_minutes": body.daily_study_minutes,
                },
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=f"Scheduler service error: {exc.response.text}",
            )
        except httpx.RequestError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Scheduler service is unavailable. Ensure Member 3 service is running on port 8004.",
            )

    result = response.json()
    scheduled = result.get("schedule", [])
    end_date = scheduled[-1]["scheduled_date"] if scheduled else body.start_date

    return SchedulerResponse(
        course_id=body.course_id,
        total_scheduled=len(scheduled),
        end_date=end_date,
        scheduled_lessons=[
            ScheduledLessonOut(
                lesson_id=s["lesson_id"],
                lesson_title=s["title"],
                scheduled_date=s["scheduled_date"],
                allocated_minutes=s["allocated_minutes"],
            )
            for s in scheduled
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
