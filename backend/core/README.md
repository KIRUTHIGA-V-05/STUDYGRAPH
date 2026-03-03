# StudyGraph Backend Core - Member 5

## What this is
This is the API Gateway and integration layer. The frontend talks ONLY to this service.
This service calls Member 1 (Planner) and Member 2 (Quiz) internally.

## Port Map
| Service        | Member | Port |
|----------------|--------|------|
| This service   | 5      | 8000 |
| Planner        | 1      | 8001 |
| Quiz Engine    | 2      | 8002 |
| Calendar       | 4      | 8003 |

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Fill in your DATABASE_URL and SECRET_KEY in .env
uvicorn main:app --reload --port 8000
```

## Docs
http://localhost:8000/docs

## Critical Notes for Teammates

### Member 6 (Database)
The models.py file defines all tables. Column names are:
- users: hashed_password (NOT password_hash), xp (NOT total_xp), streak (NOT current_streak)
- These match exactly what Member 2 already built

### Member 1 (Planner)
Your service must run on port 8001.
Endpoint called: POST /api/v1/planner/generate
Expected request: { "topic": str, "target_days": int, "user_context": str }
Expected response: { "topic": str, "target_days": int, "modules": [...] }

### Member 2 (Quiz)
Your service must run on port 8002.
Endpoints called:
- POST /api/v1/quiz/generate
- GET  /api/v1/quiz/{lesson_id}/questions
- POST /api/v1/quiz/evaluate

Submission format: { "lesson_id": "uuid-string", "answers": { "question_id": "answer_text" } }

### Member 4 (Calendar)
Your service must run on port 8003.
Endpoint called: POST /sync
(Calendar sync is optional in Phase 1 - if google_auth_code is empty, sync is skipped gracefully)

### Member 7 (Frontend)
All API calls go to http://localhost:8000
Auth header: Authorization: Bearer <token>
Store token in localStorage as studygraph_token
Store course_id in localStorage as studygraph_course_id (UUID string)
