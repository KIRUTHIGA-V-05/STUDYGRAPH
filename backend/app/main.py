from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import quiz
from app.models import core, quiz as quiz_models # Import models to register them

app = FastAPI(
    title="StudyGraph API",
    description="Autonomous Learning Planner - Phase 1 Backend",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(quiz.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to StudyGraph API. Visit /docs for documentation."}
