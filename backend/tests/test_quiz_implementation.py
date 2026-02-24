import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.quiz_service import QuizService
from app.schemas.quiz import QuizQuestion, QuizSubmission

client = TestClient(app)

@pytest.fixture
def sample_questions():
    return [
        QuizQuestion(
            id="1",
            question="What is 2+2?",
            options=["3", "4", "5", "6"],
            correct_answer="4",
            explanation="Basic addition."
        ),
        QuizQuestion(
            id="2",
            question="What is the capital of France?",
            options=["London", "Berlin", "Paris", "Madrid"],
            correct_answer="Paris",
            explanation="Paris is the capital."
        ),
        QuizQuestion(
            id="3",
            question="Is Python an interpreted language?",
            options=["Yes", "No", "Maybe", "I don't know"],
            correct_answer="Yes",
            explanation="Python is indeed interpreted."
        )
    ]

def test_xp_and_threshold_logic(sample_questions):
    service = QuizService()
    
    # Test case 1: Pass with 100% (3/3) -> Should get 30 XP
    sub_pass = QuizSubmission(
        lesson_id="test_lesson",
        answers={"1": "4", "2": "Paris", "3": "Yes"}
    )
    result_pass = service.evaluate_quiz(sub_pass, sample_questions)
    assert result_pass.passed is True
    assert result_pass.score == 3
    assert result_pass.xp_earned == 30

    # Test case 2: Fail with 33% (1/3) -> Threshold is 70% (2.1 questions) -> Should fail
    # XP calculation for failure: score * 2 = 1 * 2 = 2 XP
    sub_fail = QuizSubmission(
        lesson_id="test_lesson",
        answers={"1": "4", "2": "Berlin", "3": "No"}
    )
    result_fail = service.evaluate_quiz(sub_fail, sample_questions)
    assert result_fail.passed is False
    assert result_fail.score == 1
    assert result_fail.xp_earned == 2

def test_endpoints_existence():
    # Test root
    response = client.get("/")
    assert response.status_code == 200
    
    # Test GET questions (should fail with 404 first as no quiz is generated for this ID)
    response = client.get("/api/v1/quiz/non_existent_lesson/questions")
    assert response.status_code == 404

def test_public_question_schema(sample_questions):
    from app.routers.quiz import _temporary_lesson_store
    _temporary_lesson_store["demo_lesson_123"] = sample_questions
    
    response = client.get("/api/v1/quiz/demo_lesson_123/questions")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    # Ensure correct_answer and explanation are NOT in the response
    assert "correct_answer" not in data[0]
    assert "explanation" not in data[0]
    assert data[0]["question"] == "What is 2+2?"
