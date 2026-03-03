from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone, date
import uuid

from database import get_db
from dependencies import get_current_user
from models import Course, Module, Lesson, LessonSchedule, User, ProgressLog, XPTracker
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

    all_schedules = (
        db.query(LessonSchedule)
        .join(Lesson, LessonSchedule.lesson_id == Lesson.id)
        .join(Module, Lesson.module_id == Module.id)
        .filter(Module.course_id == course_id)
        .all()
    )

    total = len(all_schedules)
    completed = sum(1 for s in all_schedules if s.status == "completed")
    percentage = round((completed / total) * 100, 2) if total > 0 else 0.0

    user = db.query(User).filter(User.id == current_user.user_id).first()

    return ProgressResponse(
        course_id=course_id,
        completed_lessons=completed,
        total_lessons=total,
        completion_percentage=percentage,
        current_streak=user.streak if user else 0,
        total_xp=user.xp if user else 0,
        last_activity=user.last_activity if user else None,
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

    from models import Base
    from sqlalchemy import text
    quiz_passed = db.execute(
        text(
            "SELECT id FROM quiz_results "
            "WHERE lesson_id = :lid AND score >= (SELECT COUNT(*) * 0.7 FROM quiz_questions WHERE lesson_id = :lid) "
            "ORDER BY completed_at DESC LIMIT 1"
        ),
        {"lid": str(body.lesson_id)},
    ).fetchone()

    if not quiz_passed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must pass the quiz before marking this lesson as complete.",
        )

    schedule = db.query(LessonSchedule).filter(LessonSchedule.lesson_id == body.lesson_id).first()
    if schedule:
        schedule.status = "completed"
        schedule.completed_at = datetime.now(timezone.utc)

    user = db.query(User).filter(User.id == current_user.user_id).first()
    if user:
        today = date.today()
        if user.last_activity and user.last_activity.date() == today:
            pass
        elif user.last_activity and (today - user.last_activity.date()).days == 1:
            user.streak = (user.streak or 0) + 1
        else:
            user.streak = 1
        user.last_activity = datetime.now(timezone.utc)

    db.add(ProgressLog(
        user_id=current_user.user_id,
        lesson_id=body.lesson_id,
        action="lesson_completed",
    ))

    db.commit()
    return {"message": "Lesson marked as complete.", "lesson_id": str(body.lesson_id)}
