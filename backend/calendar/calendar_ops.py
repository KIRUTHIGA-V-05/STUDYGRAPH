from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

CALENDAR_ID = "primary"
TIMEZONE    = "Asia/Kolkata"


def get_calendar_service(credentials: Credentials):
    return build("calendar", "v3", credentials=credentials, cache_discovery=False)


def create_calendar_event(
    credentials: Credentials,
    lesson_id: str,
    title: str,
    scheduled_date: str,
    allocated_minutes: int,
) -> str:
    service  = get_calendar_service(credentials)
    start_dt = datetime.fromisoformat(scheduled_date)
    end_dt   = start_dt + timedelta(minutes=allocated_minutes)

    event_body = {
        "summary": f"StudyGraph: {title}",
        "description": (
            f"Lesson ID: {lesson_id}\n"
            f"Estimated Duration: {allocated_minutes} minutes\n"
            f"Powered by StudyGraph - Autonomous Learning Planner"
        ),
        "start": {"dateTime": start_dt.isoformat(), "timeZone": TIMEZONE},
        "end":   {"dateTime": end_dt.isoformat(),   "timeZone": TIMEZONE},
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "popup", "minutes": 10},
                {"method": "email", "minutes": 30},
            ],
        },
        "colorId": "6",
        "extendedProperties": {
            "private": {
                "studygraph_lesson_id": lesson_id,
                "source": "studygraph",
            }
        },
    }

    try:
        created_event = (
            service.events()
            .insert(calendarId=CALENDAR_ID, body=event_body)
            .execute()
        )
        return created_event["id"]
    except HttpError as exc:
        logger.error(f"Google Calendar API error creating event: {exc}")
        raise


def delete_calendar_event(credentials: Credentials, event_id: str) -> None:
    service = get_calendar_service(credentials)
    try:
        service.events().delete(calendarId=CALENDAR_ID, eventId=event_id).execute()
    except HttpError as exc:
        if exc.resp.status == 404:
            logger.warning(f"Event {event_id} not found. Already deleted.")
            return
        logger.error(f"Google Calendar API error deleting event: {exc}")
        raise


def update_calendar_event(
    credentials: Credentials,
    event_id: str,
    new_date: str,
    allocated_minutes: int,
) -> str:
    service  = get_calendar_service(credentials)
    start_dt = datetime.fromisoformat(new_date)
    end_dt   = start_dt + timedelta(minutes=allocated_minutes)

    patch_body = {
        "start": {"dateTime": start_dt.isoformat(), "timeZone": TIMEZONE},
        "end":   {"dateTime": end_dt.isoformat(),   "timeZone": TIMEZONE},
    }

    try:
        updated = (
            service.events()
            .patch(calendarId=CALENDAR_ID, eventId=event_id, body=patch_body)
            .execute()
        )
        return updated["id"]
    except HttpError as exc:
        logger.error(f"Google Calendar API error updating event: {exc}")
        raise
