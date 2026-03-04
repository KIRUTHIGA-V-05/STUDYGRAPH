from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import logging
from google_auth import exchange_code_for_credentials
from calendar_ops import create_calendar_event, delete_calendar_event

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="StudyGraph - Calendar Service",
    version="1.0.0",
    description="Google Calendar integration microservice for StudyGraph.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LessonEventRequest(BaseModel):
    lesson_id: str
    title: str
    scheduled_date: str
    allocated_minutes: int


class SyncRequest(BaseModel):
    google_auth_code: str
    lessons: List[LessonEventRequest]


class EventCreated(BaseModel):
    lesson_id: str
    event_id: str


class SyncResponse(BaseModel):
    events_created: int
    events: List[EventCreated]


@app.post("/sync", response_model=SyncResponse)
async def sync_calendar(body: SyncRequest):
    try:
        credentials = exchange_code_for_credentials(body.google_auth_code)
    except Exception as exc:
        logger.error(f"OAuth token exchange failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to exchange Google auth code. Ensure the code is valid and not expired.",
        )

    events_created = []
    failed = []

    for lesson in body.lessons:
        try:
            event_id = create_calendar_event(
                credentials=credentials,
                lesson_id=lesson.lesson_id,
                title=lesson.title,
                scheduled_date=lesson.scheduled_date,
                allocated_minutes=lesson.allocated_minutes,
            )
            events_created.append(EventCreated(lesson_id=lesson.lesson_id, event_id=event_id))
            logger.info(f"Created calendar event {event_id} for lesson {lesson.lesson_id}")
        except Exception as exc:
            logger.warning(f"Failed to create event for lesson {lesson.lesson_id}: {exc}")
            failed.append(lesson.lesson_id)

    if failed:
        logger.warning(f"Failed to create events for {len(failed)} lessons: {failed}")

    return SyncResponse(
        events_created=len(events_created),
        events=events_created,
    )


@app.delete("/event/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(event_id: str, google_auth_code: str):
    try:
        credentials = exchange_code_for_credentials(google_auth_code)
    except Exception as exc:
        logger.error(f"OAuth token exchange failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to exchange Google auth code.",
        )

    try:
        delete_calendar_event(credentials=credentials, event_id=event_id)
        logger.info(f"Deleted calendar event {event_id}")
    except Exception as exc:
        logger.error(f"Failed to delete event {event_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete calendar event: {str(exc)}",
        )


@app.get("/health")
def health():
    return {"status": "operational", "service": "calendar-service"}
