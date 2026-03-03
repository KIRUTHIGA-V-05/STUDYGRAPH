from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import httpx
import uuid

from database import get_db
from dependencies import get_current_user
from config import settings
from models import Course, Module, Lesson
from schemas import PlannerRequest, PlannerResponse, TokenData

router = APIRouter()


@router.post("/generate", response_model=PlannerResponse, status_code=status.HTTP_201_CREATED)
async def generate_plan(
    body: PlannerRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = (
        db.query(Course)
        .filter(Course.user_id == current_user.user_id, Course.status == "active")
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have an active course. Complete or archive it first.",
        )

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{settings.PLANNER_SERVICE_URL}/api/v1/planner/generate",
                json={
                    "topic": body.topic,
                    "target_days": body.target_days,
                    "user_context": body.user_context,
                },
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=f"Planner service error: {exc.response.text}",
            )
        except httpx.RequestError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Planner service is unavailable. Ensure Member 1 service is running on port 8001.",
            )

    plan = response.json()

    course = Course(
        user_id=current_user.user_id,
        topic=plan["topic"],
        target_days=plan["target_days"],
        days_per_week=body.days_per_week,
        daily_study_minutes=body.daily_study_minutes,
    )
    db.add(course)
    db.flush()

    for mod_index, mod_data in enumerate(plan["modules"]):
        module = Module(
            course_id=course.id,
            module_ref_id=mod_data.get("module_id"),
            title=mod_data["title"],
            description=mod_data.get("description", ""),
            order_index=mod_index + 1,
            quiz_checkpoint=mod_data.get("quiz_checkpoint", True),
        )
        db.add(module)
        db.flush()

        for les_index, les_data in enumerate(mod_data["lessons"]):
            lesson = Lesson(
                module_id=module.id,
                lesson_ref_id=les_data.get("lesson_id"),
                title=les_data["title"],
                difficulty=les_data.get("difficulty", 1),
                estimated_minutes=les_data.get("estimated_minutes", 30),
                order_index=les_index + 1,
            )
            db.add(lesson)

    db.commit()
    db.refresh(course)

    total_lessons = sum(len(m.lessons) for m in course.modules)

    return PlannerResponse(
        course_id=course.id,
        topic=course.topic,
        total_modules=len(course.modules),
        total_lessons=total_lessons,
        modules=course.modules,
    )


@router.get("/{course_id}", response_model=PlannerResponse)
def get_plan(
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

    total_lessons = sum(len(m.lessons) for m in course.modules)

    return PlannerResponse(
        course_id=course.id,
        topic=course.topic,
        total_modules=len(course.modules),
        total_lessons=total_lessons,
        modules=course.modules,
    )


@router.patch("/{course_id}/archive", status_code=status.HTTP_200_OK)
def archive_course(
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

    course.status = "archived"
    db.commit()
    return {"message": "Course archived.", "course_id": str(course_id)}
