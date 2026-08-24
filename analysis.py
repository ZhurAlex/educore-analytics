from settings import GEMINI_API_KEY, MISTRAL_API_KEY
from providers import GeminiProvider, MistralProvider, FallbackProvider
from formatting import format_responses

provider = FallbackProvider([GeminiProvider(GEMINI_API_KEY), MistralProvider(MISTRAL_API_KEY)])

def analyse(responses):
    formatted_responses = format_responses(responses)
    
    return formatted_responses