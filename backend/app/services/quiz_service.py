import os
import json
import uuid
from typing import List, Optional
from google import genai
from dotenv import load_dotenv

from app.schemas.quiz import QuizQuestion, QuizSubmission, QuizResult, QuestionEvaluation

# Load environment variables
load_dotenv()

class QuizService:
    def __init__(self):
        # Initialize the new Google Gen AI Client
        api_key = os.environ.get("GEMINI_API_KEY")
        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemini-flash-latest"

    def generate_quiz(self, module_content: str, num_questions: int = 5) -> List[QuizQuestion]:
        """
        Generates MCQs using the new google-genai SDK.
        """
        prompt = f"""
        You are an expert educational content creator. Based on the following module content, 
        generate {num_questions} multiple-choice questions (MCQs).
        
        Requirements:
        1. Each question must have exactly 4 options.
        2. Provide the correct answer exactly as it appears in the options.
        3. Provide a brief explanation for why the answer is correct.
        4. Your output must be a valid JSON list of objects.
        
        Example JSON format:
        [
          {{
            "question": "What is the capital of France?",
            "options": ["London", "Paris", "Berlin", "Madrid"],
            "correct_answer": "Paris",
            "explanation": "Paris is the capital of France."
          }}
        ]
        
        Module Content:
        {module_content}
        """
        
        try:
            # Using the new SDK's generate_content
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt
            )
            
            raw_text = response.text.strip()
            
            # Robust JSON extraction
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[-1].split("```")[0]
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1]
            
            json_data = json.loads(raw_text.strip())
            
            questions = []
            for item in json_data:
                questions.append(QuizQuestion(
                    id=str(uuid.uuid4()),
                    question=item["question"],
                    options=item["options"],
                    correct_answer=item["correct_answer"],
                    explanation=item["explanation"]
                ))
            return questions
            
        except Exception as e:
            print(f"Error generating quiz: {str(e)}")
            raise ValueError(f"Failed to generate quiz: {str(e)}")

    def evaluate_quiz(self, submission: QuizSubmission, actual_questions: List[QuizQuestion], pass_percentage: float = 0.7) -> QuizResult:
        """
        Evaluates a user's quiz submission against the actual questions.
        Threshold set to 70% per Phase 1 Documentation.
        """
        evaluations = []
        score = 0
        total_questions = len(actual_questions)
        
        question_map = {q.id: q for q in actual_questions}
        
        for q_id, user_answer in submission.answers.items():
            actual_q = question_map.get(q_id)
            if not actual_q:
                continue
                
            is_correct = (user_answer.strip().lower() == actual_q.correct_answer.strip().lower())
            if is_correct:
                score += 1
                
            evaluations.append(QuestionEvaluation(
                question_id=q_id,
                is_correct=is_correct,
                correct_answer=actual_q.correct_answer,
                explanation=actual_q.explanation
            ))
            
        passed = score >= (total_questions * pass_percentage)
        
        # XP Logic: 10 XP per correct answer if passed, 2 XP per correct if failed
        xp_earned = (score * 10) if passed else (score * 2)
        
        return QuizResult(
            score=score,
            total_questions=total_questions,
            evaluations=evaluations,
            passed=passed,
            xp_earned=xp_earned
        )
