from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import httpx
import uuid

from database import get_db
from dependencies import get_current_user
from config import settings
from models import Course, Module, Lesson, LessonSchedule, CalendarEvent
from schemas import CalendarSyncRequest, CalendarSyncResponse, TokenData

router = APIRouter()


@router.post("/sync", response_model=CalendarSyncResponse)
async def sync_calendar(
    body: CalendarSyncRequest,
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

    scheduled = (
        db.query(Lesson, LessonSchedule)
        .join(LessonSchedule, Lesson.id == LessonSchedule.lesson_id)
        .join(Module, Lesson.module_id == Module.id)
        .filter(Module.course_id == body.course_id)
        .order_by(LessonSchedule.scheduled_date)
        .all()
    )

    if not scheduled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No scheduled lessons found. Run the scheduler first.",
        )

    if not body.google_auth_code:
        return CalendarSyncResponse(synced=False, events_created=0)

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{settings.CALENDAR_SERVICE_URL}/sync",
                json={
                    "google_auth_code": body.google_auth_code,
                    "lessons": [
                        {
                            "lesson_id": str(lesson.id),
                            "title": lesson.title,
                            "scheduled_date": schedule.scheduled_date,
                            "allocated_minutes": schedule.allocated_minutes,
                        }
                        for lesson, schedule in scheduled
                    ],
                },
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=f"Calendar service error: {exc.response.text}",
            )
        except httpx.RequestError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Calendar service is unavailable. Ensure Member 4 service is running on port 8003.",
            )

    sync_result = response.json()

    for event in sync_result.get("events", []):
        existing = (
            db.query(CalendarEvent)
            .filter(CalendarEvent.lesson_id == uuid.UUID(event["lesson_id"]))
            .first()
        )
        if existing:
            existing.google_event_id = event["event_id"]
        else:
            db.add(CalendarEvent(
                lesson_id=uuid.UUID(event["lesson_id"]),
                google_event_id=event["event_id"],
            ))

    db.commit()
    return CalendarSyncResponse(synced=True, events_created=sync_result.get("events_created", 0))


@router.delete("/event/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    lesson_id: uuid.UUID,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = db.query(CalendarEvent).filter(CalendarEvent.lesson_id == lesson_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calendar event not found.")

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            await client.delete(f"{settings.CALENDAR_SERVICE_URL}/event/{event.google_event_id}")
        except httpx.RequestError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Calendar service is unavailable.",
            )

    db.delete(event)
    db.commit()
