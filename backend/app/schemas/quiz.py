from pydantic import BaseModel, Field
from typing import List, Dict

class QuizQuestion(BaseModel):
    id: str = Field(..., description="Unique ID for the question")
    question: str = Field(..., description="The MCQ question text")
    options: List[str] = Field(..., description="List of 4 options")
    correct_answer: str = Field(..., description="The exact text of the correct option")
    explanation: str = Field(..., description="Explanation of why the answer is correct")

class QuizQuestionPublic(BaseModel):
    id: str
    question: str
    options: List[str]

class QuizGenerationRequest(BaseModel):
    lesson_id: str = Field(..., description="ID of the lesson to generate quiz for")
    module_content: str = Field(..., description="The text content or lesson notes to generate questions from")
    num_questions: int = Field(default=5, description="Number of questions to generate")

class QuizSubmission(BaseModel):
    lesson_id: str = Field(..., description="ID of the lesson this quiz belongs to")
    answers: Dict[str, str] = Field(..., description="Mapping of question ID to the user's selected answer")

class QuestionEvaluation(BaseModel):
    question_id: str
    is_correct: bool
    correct_answer: str
    explanation: str

class QuizResult(BaseModel):
    score: int = Field(..., description="Number of correct answers")
    total_questions: int = Field(..., description="Total number of evaluated questions")
    evaluations: List[QuestionEvaluation] = Field(..., description="Detailed feedback per question")
    passed: bool = Field(..., description="Whether the user passed the minimum threshold")
    xp_earned: int = Field(default=0, description="XP earned based on performance")
