from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import httpx
import uuid

from database import get_db
from dependencies import get_current_user
from config import settings
from models import Course, Module, Lesson, LessonSchedule, User, XPTracker
from schemas import QuizGenerateRequest, QuizSubmitRequest, QuizResultResponse, TokenData

router = APIRouter()


def verify_lesson_belongs_to_user(lesson_id: uuid.UUID, user_id: uuid.UUID, db: Session):
    result = (
        db.query(Lesson)
        .join(Module, Lesson.module_id == Module.id)
        .join(Course, Module.course_id == Course.id)
        .filter(Lesson.id == lesson_id, Course.user_id == user_id)
        .first()
    )
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found.")
    return result


@router.post("/generate", status_code=status.HTTP_201_CREATED)
async def generate_quiz(
    body: QuizGenerateRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    verify_lesson_belongs_to_user(body.lesson_id, current_user.user_id, db)

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{settings.QUIZ_SERVICE_URL}/api/v1/quiz/generate",
                json={
                    "lesson_id": str(body.lesson_id),
                    "module_content": body.module_content,
                    "num_questions": body.num_questions,
                },
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=f"Quiz service error: {exc.response.text}",
            )
        except httpx.RequestError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Quiz service is unavailable. Ensure Member 2 service is running on port 8002.",
            )

    return response.json()


@router.get("/{lesson_id}/questions")
async def get_questions(
    lesson_id: uuid.UUID,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    verify_lesson_belongs_to_user(lesson_id, current_user.user_id, db)

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{settings.QUIZ_SERVICE_URL}/api/v1/quiz/{str(lesson_id)}/questions"
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=f"Quiz service error: {exc.response.text}",
            )
        except httpx.RequestError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Quiz service is unavailable. Ensure Member 2 service is running on port 8002.",
            )

    return response.json()


@router.post("/evaluate", response_model=QuizResultResponse)
async def evaluate_quiz(
    body: QuizSubmitRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    verify_lesson_belongs_to_user(body.lesson_id, current_user.user_id, db)

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{settings.QUIZ_SERVICE_URL}/api/v1/quiz/evaluate",
                json={
                    "lesson_id": str(body.lesson_id),
                    "answers": body.answers,
                },
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=f"Quiz service error: {exc.response.text}",
            )
        except httpx.RequestError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Quiz service is unavailable. Ensure Member 2 service is running on port 8002.",
            )

    result_data = response.json()

    if result_data.get("xp_earned", 0) > 0:
        xp_log = XPTracker(
            user_id=current_user.user_id,
            amount=result_data["xp_earned"],
            reason=f"Quiz completed for lesson {body.lesson_id}",
        )
        db.add(xp_log)

        user = db.query(User).filter(User.id == current_user.user_id).first()
        if user:
            user.xp = (user.xp or 0) + result_data["xp_earned"]

        db.commit()

    return QuizResultResponse(**result_data)
