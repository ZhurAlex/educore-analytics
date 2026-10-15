from dataclasses import dataclass

from pydantic import BaseModel, Field

from common.models import Exercise


class Mistake(BaseModel):
    topic: str = Field(
        description="Short, general label of the skill being tested, always in English regardless of the "
        "response language — no question-specific wording, used to search an English-language textbook database"
    )
    description: str = Field(
        description="Detailed explanation for the teacher, in the requested response language, with concrete examples"
    )


class Mistakes(BaseModel):
    mistakes: list[Mistake]


class RecommendedExercise(BaseModel):
    index: int = Field(
        description="The number of the mistake this recommendation addresses, matching 'Mistake N' in the input"
    )
    best_exercise_id: int | None = Field(
        None, description="id of the single best-matching exercise, or null if none of the candidates are a good fit"
    )
    other_exercise_ids: list[int] = Field(
        description="ids of the other candidate exercises, for the teacher to optionally look at"
    )


class RecommendedExercises(BaseModel):
    recommendations: list[RecommendedExercise]


@dataclass
class MistakeWithExercises:
    index: int
    mistake: Mistake
    exercises: list[Exercise]


@dataclass
class FinalRecommendation:
    description: str
    best_exercise: Exercise | None
    other_exercises: list[Exercise]
