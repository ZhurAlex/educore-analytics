from app.formatting import format_class_responses, format_student_responses
from app.prompts import CLASS_GAP_ANALYSIS_PROMPT, STUDENT_GAP_ANALYSIS_PROMPT
from app.providers import make_request_to_LLM
from app.models import Mistakes, Mistake
from app.retrieval import get_exercises

async def analyse_student(responses, subject: str = "english", language: str = "English"):
    formatted_responses = format_student_responses(responses)
    system_prompt = STUDENT_GAP_ANALYSIS_PROMPT.format(subject=subject, language=language)
    reply = await make_request_to_LLM(formatted_responses, system_prompt, Mistakes)
    reply_with_exercises = await get_exercises(reply)
    return reply_with_exercises


async def analyse_class(responses, subject: str = "english", language: str = "English"):
    formatted_responses = format_class_responses(responses)
    system_prompt = CLASS_GAP_ANALYSIS_PROMPT.format(subject=subject, language=language)
    reply = await make_request_to_LLM(formatted_responses, system_prompt, Mistakes)
    reply_with_exercises = await get_exercises(reply)
    return reply_with_exercises
