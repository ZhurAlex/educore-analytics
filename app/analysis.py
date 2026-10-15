from app.formatting import format_class_responses, format_mistake_with_exercises, format_student_responses
from app.models import FinalRecommendation, Mistakes, MistakeWithExercises, RecommendedExercise, RecommendedExercises
from app.prompts import CLASS_GAP_ANALYSIS_PROMPT, FIND_RECOMMENDED_EXERCISES_PROMPT, STUDENT_GAP_ANALYSIS_PROMPT
from app.providers import make_request_to_LLM
from app.retrieval import get_exercises
from common.models import Exercise


def build_mistake_lookup(mistakes_with_exercises: list[MistakeWithExercises]) -> dict[int, MistakeWithExercises]:
    return {item.index: item for item in mistakes_with_exercises}


def build_exercise_lookup(mistakes_with_exercises: list[MistakeWithExercises]) -> dict[int, Exercise]:
    return {exercise.id: exercise for item in mistakes_with_exercises for exercise in item.exercises}


def build_final_recommendation(
    rec: RecommendedExercise,
    mistake_lookup: dict[int, MistakeWithExercises],
    exercise_lookup: dict[int, Exercise],
) -> FinalRecommendation:
    mistake = mistake_lookup.get(rec.index)
    description = mistake.mistake.description if mistake else "No description available"
    candidate_ids = {exercise.id for exercise in mistake.exercises} if mistake else set()
    best_exercise = (
        exercise_lookup.get(rec.best_exercise_id)
        if rec.best_exercise_id is not None and rec.best_exercise_id in candidate_ids
        else None
    )
    other_exercises = [
        exercise_lookup[eid] for eid in rec.other_exercise_ids if eid in candidate_ids and eid in exercise_lookup
    ]
    return FinalRecommendation(description=description, best_exercise=best_exercise, other_exercises=other_exercises)


def build_final_recommendations(
    # recommended_exercises: ids of recommended exercises for each mistake (both best and other candidates)
    mistakes_with_recommended_exercises: RecommendedExercises,
    # mistakes_with_exercises: the actual exercises for each mistake (from the database)
    mistakes_with_exercises: list[MistakeWithExercises],
) -> list[FinalRecommendation]:
    # dictionary with mistake index as key and MistakeWithExercises as value, for easy lookup
    mistake_lookup = build_mistake_lookup(mistakes_with_exercises)
    # dictionary with exercise id as key and Exercise as value, for easy lookup
    exercise_lookup = build_exercise_lookup(mistakes_with_exercises)
    return [
        build_final_recommendation(rec, mistake_lookup, exercise_lookup)
        for rec in mistakes_with_recommended_exercises.recommendations
    ]


async def process_analysis(formatted_responses, system_prompt):
    # list of mistakes identified by the LLM
    mistakes = await make_request_to_LLM(formatted_responses, system_prompt, Mistakes)
    # candidate exercises for each mistake, retrieved from the database
    mistakes_with_exercises = await get_exercises(mistakes)
    if not mistakes_with_exercises:
        return []
    # recommended exercises, picked by the LLM from the retrieved candidates
    mistakes_with_recommended_exercises = await make_request_to_LLM(
        format_mistake_with_exercises(mistakes_with_exercises), FIND_RECOMMENDED_EXERCISES_PROMPT, RecommendedExercises
    )
    return build_final_recommendations(mistakes_with_recommended_exercises, mistakes_with_exercises)


async def analyse_student(responses, subject: str = "english", language: str = "English"):
    formatted_responses = format_student_responses(responses)
    system_prompt = STUDENT_GAP_ANALYSIS_PROMPT.format(subject=subject, language=language)
    return await process_analysis(formatted_responses, system_prompt)


async def analyse_class(responses, subject: str = "english", language: str = "English"):
    formatted_responses = format_class_responses(responses)
    system_prompt = CLASS_GAP_ANALYSIS_PROMPT.format(subject=subject, language=language)
    return await process_analysis(formatted_responses, system_prompt)
