from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timezone, date
import uuid

from database import get_db
from dependencies import get_current_user
from models import Course, Module, Lesson, User, ProgressLog
from schemas import ProgressResponse, MarkCompleteRequest, TokenData

router = APIRouter()


@router.get("/{course_id}", response_model=ProgressResponse)
def get_progress(
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

    all_lessons = (
        db.query(Lesson)
        .join(Module)
        .filter(Module.course_id == course_id)
        .all()
    )

    total      = len(all_lessons)
    completed  = sum(1 for l in all_lessons if l.status == "completed")
    percentage = round((completed / total) * 100, 2) if total > 0 else 0.0

    user = db.query(User).filter(User.id == current_user.user_id).first()

    return ProgressResponse(
        course_id=course_id,
        completed_lessons=completed,
        total_lessons=total,
        completion_percentage=percentage,
        current_streak=user.streak if user else 0,
        total_xp=user.xp if user else 0,
        last_activity=None,
    )


@router.post("/complete", status_code=status.HTTP_200_OK)
def mark_lesson_complete(
    body: MarkCompleteRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lesson = (
        db.query(Lesson)
        .join(Module, Lesson.module_id == Module.id)
        .join(Course, Module.course_id == Course.id)
        .filter(Lesson.id == body.lesson_id, Course.user_id == current_user.user_id)
        .first()
    )
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found.")

    quiz_passed = db.execute(
        text(
            "SELECT id FROM quiz_results "
            "WHERE lesson_id = :lid AND user_id = :uid "
            "ORDER BY completed_at DESC LIMIT 1"
        ),
        {"lid": str(body.lesson_id), "uid": str(current_user.user_id)},
    ).fetchone()

    if not quiz_passed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must pass the quiz before marking this lesson as complete.",
        )

    lesson.status = "completed"

    user = db.query(User).filter(User.id == current_user.user_id).first()
    if user:
        last = db.execute(
            text(
                "SELECT timestamp FROM progress_logs "
                "WHERE user_id = :uid ORDER BY timestamp DESC LIMIT 1"
            ),
            {"uid": str(current_user.user_id)},
        ).fetchone()
        today = date.today()
        if last:
            last_date = last.timestamp.date()
            if last_date == today:
                pass
            elif (today - last_date).days == 1:
                user.streak = (user.streak or 0) + 1
            else:
                user.streak = 1
        else:
            user.streak = 1

    db.add(ProgressLog(
        user_id=current_user.user_id,
        lesson_id=body.lesson_id,
        activity_type="lesson_completed",
        duration_seconds=None,
    ))

    db.commit()
    return {"message": "Lesson marked as complete.", "lesson_id": str(body.lesson_id)}
