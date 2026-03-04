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
        .filter(Course.user_id == current_user.user_id)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have an active course. Complete or archive it before creating a new one.",
        )

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{settings.PLANNER_SERVICE_URL}/api/v1/planner/generate",
                json={
                    "topic": body.topic,
                    "target_days": body.duration_days,
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
        title=plan["topic"],
        description=f"Auto-generated course for: {plan['topic']}",
        duration_days=plan["target_days"],
    )
    db.add(course)
    db.flush()

    for mod_index, mod_data in enumerate(plan["modules"]):
        module = Module(
            course_id=course.id,
            title=mod_data["title"],
            order=mod_index + 1,
            difficulty_weight=None,
        )
        db.add(module)
        db.flush()

        for les_index, les_data in enumerate(mod_data["lessons"]):
            lesson = Lesson(
                module_id=module.id,
                title=les_data["title"],
                content_type="text",
                estimated_minutes=les_data.get("estimated_minutes", 30),
                order=les_index + 1,
                status="pending",
            )
            db.add(lesson)

    db.commit()
    db.refresh(course)

    total_lessons = sum(len(m.lessons) for m in course.modules)

    return PlannerResponse(
        course_id=course.id,
        title=course.title,
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
        title=course.title,
        total_modules=len(course.modules),
        total_lessons=total_lessons,
        modules=course.modules,
    )
