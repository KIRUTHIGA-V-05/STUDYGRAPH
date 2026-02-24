import os
import logging
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from tenacity import retry, stop_after_attempt, wait_exponential
from schemas import CoursePlan

load_dotenv()
logger = logging.getLogger(__name__)

def get_planner_model():
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.1,
        max_retries=2  
    )

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def generate_curriculum_async(topic: str, target_days: int, user_context: str) -> CoursePlan:
    llm = get_planner_model()
    structured_llm = llm.with_structured_output(CoursePlan)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are StudyGraph's elite Autonomous Curriculum Architect. 
        Your mandate is to deconstruct any requested topic into a highly optimized, universally logical learning progression.
        
        INSTRUCTIONS:
        1. MODULARITY: Deconstruct the topic into sequential Modules. Break Modules into bite-sized Lessons (20-90 mins).
        2. PACING: Distribute the lessons logically so the total estimated time fits reasonably within the requested {target_days} days.
        3. PROGRESSION: Enforce a strict prerequisite chain. Never introduce advanced synthesis before foundational definitions.
        
        UNIVERSAL DIFFICULTY SIZING (1-5 COGNITIVE SCALE):
        Do not base difficulty on the subject matter, but on the cognitive action required by the learner.
        
        - Level 1 (Remembering): Recognizing, recalling, defining terms, listing components.
        - Level 2 (Understanding): Explaining ideas, summarizing concepts, interpreting information.
        - Level 3 (Applying): Executing procedures, implementing rules, solving standard problems.
        - Level 4 (Analyzing): Differentiating, organizing, troubleshooting, comparing structures.
        - Level 5 (Evaluating & Creating): Designing novel systems, optimizing, handling edge-cases, advanced synthesis.
        
        ADAPTATION RULES:
        Analyze the 'User Context' provided. Dynamically adjust the curriculum depth and time estimation based on this persona.
        
        User Context: {user_context}
        """),
        ("human", "Generate a definitive {target_days}-day study plan to master: {topic}")
    ])

    chain = prompt | structured_llm
    
    logger.info(f"Initiating Groq LLM call for topic: {topic}")
    
    response = await chain.ainvoke({
        "topic": topic, 
        "target_days": target_days, 
        "user_context": user_context
    })
    
    return response