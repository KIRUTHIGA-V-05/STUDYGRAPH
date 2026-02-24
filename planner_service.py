from fastapi import FastAPI, HTTPException
from pydantic import ValidationError
from schemas import PlanRequest, CoursePlan
from llm_engine import generate_curriculum_async
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="StudyGraph - Planner Service (Member 1)",
    version="1.0.0",
    description="Autonomous curriculum generation microservice powered by Groq & LangChain."
)

@app.post("/api/v1/planner/generate", response_model=CoursePlan)
async def create_plan(request: PlanRequest):
    try:
        logger.info(f"Generating {request.target_days}-day plan for topic: {request.topic}")
        
        plan = await generate_curriculum_async(
            topic=request.topic,
            target_days=request.target_days,
            user_context=request.user_context
        )
        
        logger.info(f"Successfully generated plan for {request.topic} with {len(plan.modules)} modules.")
        return plan
        
    except ValidationError as ve:
        logger.warning(f"Validation Error in LLM Output: {ve}")
        raise HTTPException(status_code=422, detail="LLM generated an invalid curriculum structure. Please retry.")
        
    except Exception as e:
        logger.error(f"Critical Planner Agent Failure: {str(e)}")
        raise HTTPException(status_code=503, detail="Curriculum generation service is currently unavailable.")

