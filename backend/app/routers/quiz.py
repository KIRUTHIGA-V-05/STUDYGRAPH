from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict
from app.schemas.quiz import (
    QuizQuestion, QuizQuestionPublic, QuizGenerationRequest, 
    QuizSubmission, QuizResult
)
from app.services.quiz_service import QuizService

router = APIRouter(
    prefix="/quiz",
    tags=["Quiz Engine (Member 2)"]
)

# For a real application, actual_questions would be stored in the database.
# Map lesson_id -> List[QuizQuestion]
_temporary_lesson_store: Dict[str, List[QuizQuestion]] = {}

def get_quiz_service():
    return QuizService()

@router.post("/generate", response_model=List[QuizQuestion])
async def generate_quiz(request: QuizGenerationRequest, service: QuizService = Depends(get_quiz_service)):
    """
    (Internal/Dev) Generate and store MCQs for a simulated lesson.
    In production, Member 1 (Planner) or Member 5 (Integrator) would trigger this.
    """
    try:
        questions = service.generate_quiz(
            module_content=request.module_content, 
            num_questions=request.num_questions
        )
        
        # Use a mock lesson_id for demonstration since we aren't integrated with Member 6's DB yet
        mock_lesson_id = "demo_lesson_123"
        _temporary_lesson_store[mock_lesson_id] = questions
            
        return questions
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error during quiz generation.")

@router.get("/{lesson_id}/questions", response_model=List[QuizQuestionPublic])
async def get_questions(lesson_id: str):
    """
    Get quiz questions for a lesson without leaking answers.
    """
    if lesson_id not in _temporary_lesson_store:
        raise HTTPException(status_code=404, detail="Quiz not found for this lesson.")
    
    questions = _temporary_lesson_store[lesson_id]
    # Return questions without correct answers and explanations
    return [
        QuizQuestionPublic(id=q.id, question=q.question, options=q.options) 
        for q in questions
    ]

@router.post("/evaluate", response_model=QuizResult)
async def evaluate_quiz(submission: QuizSubmission, service: QuizService = Depends(get_quiz_service)):
    """
    Submit answers and receive score and XP.
    """
    lesson_id = submission.lesson_id
    if lesson_id not in _temporary_lesson_store:
         raise HTTPException(status_code=404, detail="No matching quiz found for the submitted lesson ID.")
    
    actual_questions = _temporary_lesson_store[lesson_id]
    
    # Evaluate the submission
    result = service.evaluate_quiz(submission, actual_questions)
    
    # TODO: In a real scenario, call Member 6's DB service to persist the result
    # and Member 5's progress service to mark lesson completion if result.passed is True.
    
    return result
