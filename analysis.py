from formatting import format_class_responses, format_student_responses
from prompts import CLASS_GAP_ANALYSIS_PROMPT, STUDENT_GAP_ANALYSIS_PROMPT
from providers import FallbackProvider, GeminiProvider, MistralProvider
from settings import GEMINI_API_KEY, MISTRAL_API_KEY

provider = FallbackProvider([GeminiProvider(GEMINI_API_KEY), MistralProvider(MISTRAL_API_KEY)])


async def analyse_student(responses, subject: str = "english", language: str = "English"):
    formatted_responses = format_student_responses(responses)
    system_prompt = STUDENT_GAP_ANALYSIS_PROMPT.format(subject=subject, language=language)
    reply = await provider.generate(formatted_responses, system_prompt)
    return reply


async def analyse_class(responses, subject: str = "english", language: str = "English"):
    formatted_responses = format_class_responses(responses)
    system_prompt = CLASS_GAP_ANALYSIS_PROMPT.format(subject=subject, language=language)
    reply = await provider.generate(formatted_responses, system_prompt)
    return reply
