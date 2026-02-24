from pydantic import BaseModel, Field, model_validator
from typing import List

class Lesson(BaseModel):
    lesson_id: str = Field(description="Unique identifier for the lesson (e.g., l1, l2)")
    title: str = Field(min_length=3, max_length=100, description="Title of the lesson")
    difficulty: int = Field(ge=1, le=5, description="Cognitive difficulty on a 1-5 scale (1=Remembering, 5=Creating/Synthesis)")
    estimated_minutes: int = Field(ge=10, le=180, description="Estimated time to complete in minutes")

class Module(BaseModel):
    module_id: str = Field(description="Unique identifier for the module (e.g., m1, m2)")
    title: str = Field(min_length=3, description="Title of the module")
    description: str = Field(description="Brief description of what the module covers")
    lessons: List[Lesson] = Field(min_length=1, description="List of lessons in this module")
    quiz_checkpoint: bool = Field(default=True, description="Always true. A quiz follows every module.")

class CoursePlan(BaseModel):
    topic: str
    target_days: int
    modules: List[Module]

    @model_validator(mode='after')
    def validate_workload(self) -> 'CoursePlan':
        total_minutes = sum(
            lesson.estimated_minutes 
            for module in self.modules 
            for lesson in module.lessons
        )
        total_hours = total_minutes / 60
        max_reasonable_hours = self.target_days * 6 # Prevents scheduling more than 6 hours per day on average
        
        if total_hours > max_reasonable_hours:
            raise ValueError(f"LLM generated unrealistic workload: {total_hours} hours for {self.target_days} days.")
        return self

class PlanRequest(BaseModel):
    topic: str = Field(min_length=2, max_length=100)
    target_days: int = Field(ge=1, le=90)
    user_context: str = Field(default="Undergraduate Student")