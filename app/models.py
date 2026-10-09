from pydantic import BaseModel, Field

class Mistake(BaseModel):
    topic: str = Field(description="Short, general label of the skill being tested — no question-specific wording, suitable for searching textbook exercises")
    description: str = Field(description="Detailed explanation for the teacher, with concrete examples")
  
class Mistakes(BaseModel):
    mistakes: list[Mistake]