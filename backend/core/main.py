from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from database import engine, Base
from middleware.error_handler import register_exception_handlers
from routers import auth, planner, scheduler, quiz, calendar, progress
from config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="StudyGraph API",
    version="1.0.0",
    description="Autonomous Learning Planner - Backend Core (Member 5)",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(auth.router,      prefix="/api/v1/auth",      tags=["Authentication"])
app.include_router(planner.router,   prefix="/api/v1/planner",   tags=["Planner"])
app.include_router(scheduler.router, prefix="/api/v1/scheduler", tags=["Scheduler"])
app.include_router(quiz.router,      prefix="/api/v1/quiz",      tags=["Quiz"])
app.include_router(calendar.router,  prefix="/api/v1/calendar",  tags=["Calendar"])
app.include_router(progress.router,  prefix="/api/v1/progress",  tags=["Progress"])


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "operational", "version": "1.0.0"}
