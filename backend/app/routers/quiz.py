from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.orm import Session
from uuid import UUID
from app.database import get_db
from app.schemas.quiz import (
    QuizQuestion as QuizQuestionSchema, QuizQuestionPublic, QuizGenerationRequest, 
    QuizSubmission, QuizResult as QuizResultSchema
)
from app.services.quiz_service import QuizService
from app.models.quiz import QuizQuestion as QuizQuestionModel, QuizResult as QuizResultModel

router = APIRouter(
    prefix="/quiz",
    tags=["Quiz Engine (Member 2)"]
)

def get_quiz_service():
    return QuizService()

@router.post("/generate", response_model=List[QuizQuestionSchema])
async def generate_quiz(
    request: QuizGenerationRequest, 
    service: QuizService = Depends(get_quiz_service),
    db: Session = Depends(get_db)
):
    """
    Generate and store MCQs for a lesson in the database.
    """
    try:
        # Expect lesson_id in request. If not present, we use a placeholder or fail.
        # Check if lesson_id is in request, otherwise default to a known UUID for testing if needed
        lesson_id_str = getattr(request, 'lesson_id', "00000000-0000-0000-0000-000000000000")
        lesson_id = UUID(lesson_id_str)
        
        generated_questions = service.generate_quiz(
            module_content=request.module_content, 
            num_questions=request.num_questions
        )
        
        # Save to DB
        db_questions = []
        for q in generated_questions:
            db_q = QuizQuestionModel(
                lesson_id=lesson_id,
                question_text=q.question, # Map schema 'question' to model 'question_text'
                options=q.options,
                correct_answer=q.correct_answer,
                explanation=q.explanation
            )
            db.add(db_q)
            db_questions.append(db_q)
        
        db.commit()
        for q in db_questions:
            db.refresh(q)
            
        return [
            QuizQuestionSchema(
                id=str(q.id),
                question=q.question_text,
                options=q.options,
                correct_answer=q.correct_answer,
                explanation=q.explanation
            ) for q in db_questions
        ]
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/{lesson_id}/questions", response_model=List[QuizQuestionPublic])
async def get_questions(lesson_id: str, db: Session = Depends(get_db)):
    """
    Get quiz questions for a lesson from the database without leaking answers.
    """
    try:
        l_id = UUID(lesson_id)
        questions = db.query(QuizQuestionModel).filter(QuizQuestionModel.lesson_id == l_id).all()
        
        if not questions:
            raise HTTPException(status_code=404, detail="Quiz not found for this lesson.")
        
        return [
            QuizQuestionPublic(id=str(q.id), question=q.question_text, options=q.options) 
            for q in questions
        ]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format for lesson_id")

from app.models.core import User, Lesson, XPTracker

@router.post("/evaluate", response_model=QuizResultSchema)
async def evaluate_quiz(
    submission: QuizSubmission, 
    service: QuizService = Depends(get_quiz_service),
    db: Session = Depends(get_db)
):
    """
    Submit answers, evaluate against DB questions, and store the result.
    Updates User XP and records in XPTracker.
    """
    try:
        lesson_id = UUID(submission.lesson_id)
        # For Phase 1, we use a mock user ID
        user_id = UUID("00000000-0000-0000-0000-000000000000")
        
        db_questions = db.query(QuizQuestionModel).filter(QuizQuestionModel.lesson_id == lesson_id).all()
        
        if not db_questions:
             raise HTTPException(status_code=404, detail="No matching quiz found for the submitted lesson ID.")
        
        # Convert DB models to schemas for the service to evaluate
        actual_questions = [
            QuizQuestionSchema(
                id=str(q.id),
                question=q.question_text,
                options=q.options,
                correct_answer=q.correct_answer,
                explanation=q.explanation
            ) for q in db_questions
        ]
        
        # Evaluate the submission
        result = service.evaluate_quiz(submission, actual_questions)
        
        # 1. Save quiz result to DB
        db_result = QuizResultModel(
            user_id=user_id,
            lesson_id=lesson_id,
            score=result.score,
            total_questions=result.total_questions
        )
        db.add(db_result)
        
        # 2. Record XP in tracker
        if result.xp_earned > 0:
            xp_entry = XPTracker(
                user_id=user_id,
                amount=result.xp_earned,
                reason=f"Quiz completed for lesson {lesson_id}"
            )
            db.add(xp_entry)
            
            # 3. Update User total XP
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.xp = (user.xp or 0) + result.xp_earned
        
        db.commit()
        db.refresh(db_result)
        
        return result
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid UUID or data format: {str(e)}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
