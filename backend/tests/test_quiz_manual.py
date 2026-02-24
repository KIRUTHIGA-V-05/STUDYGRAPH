import sys
import os

# Add the backend directory to python path for testing
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.schemas.quiz import QuizSubmission
from app.services.quiz_service import QuizService

def manual_test():
    from dotenv import load_dotenv
    # Load environment variables from .env file
    load_dotenv()
    
    print("Initializing QuizService with new google-genai SDK...")
    try:
        service = QuizService()
    except Exception as e:
        print(f"Failed to initialize QuizService: {e}")
        return
    
    # Needs GEMINI_API_KEY exported in env
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Warning: GEMINI_API_KEY environment variable not set. This will likely fail.")
    else:
        print("GEMINI_API_KEY found.")

    sample_content = """
    Operating Systems (OS) act as an intermediary between computer users and computer hardware. 
    The core kernel is the central component of most operating systems; it is a computer program 
    that manages I/O requests from software and translates them into data processing instructions 
    for the central processing unit and other electronic components.
    Memory management is the process of controlling and coordinating computer memory, assigning 
    portions called blocks to various running programs to optimize overall system performance.
    """

    print("\n--- Testing generate_quiz ---")
    try:
        questions = service.generate_quiz(module_content=sample_content, num_questions=2)
        print(f"Successfully generated {len(questions)} questions:")
        for q in questions:
            print(f"- Q: {q.question}")
            print(f"  Options: {q.options}")
            print(f"  Correct: {q.correct_answer}")
            print(f"  Explanation: {q.explanation}")
            print("")
    except Exception as e:
        print(f"Failed to generate quiz: {e}")
        return

    print("\n--- Testing evaluate_quiz ---")
    try:
        # Create a mock submission using the generated questions
        submission = QuizSubmission(
            lesson_id="demo_lesson_123",
            answers={
               questions[0].id: questions[0].correct_answer, # Correct
               questions[1].id: "Wrong Answer Stubs"         # Incorrect
            }
        )
        
        # 70% threshold (1.4 out of 2) -> 1/2 = 50% -> Should FAIL
        result = service.evaluate_quiz(submission, questions, pass_percentage=0.7)
        print(f"Evaluation resulted in score: {result.score} / {result.total_questions}")
        print(f"Passed: {result.passed} (Expected: False for 50%)")
        print(f"XP Earned: {result.xp_earned}")
        for eval in result.evaluations:
            status = "CORRECT" if eval.is_correct else "INCORRECT"
            print(f"- Question ID: {eval.question_id} -> {status}")
            
    except Exception as e:
        print(f"Failed to evaluate quiz: {e}")


if __name__ == "__main__":
    manual_test()
