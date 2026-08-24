from abc import ABC, abstractmethod
from google import genai
from mistralai.client import Mistral
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class LLMResponse:
    text: str
    provider_name: str
    tokens_used: int | None = None


class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, text: str, system: str = "") -> LLMResponse: ...

class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gemini-3.1-flash-lite"):
        self.client = genai.Client(api_key=api_key)
        self.model = model

    async def generate(self, text: str, system: str = "" ):
        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=text,
            config = genai.types.GenerateContentConfig(system_instruction = system)
        )
        return LLMResponse(
            text=response.text,
            tokens_used=response.usage_metadata.total_token_count,
            provider_name=type(self).__name__
        )

class MistralProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "mistral-small-latest"):
        self.client = Mistral(api_key=api_key)
        self.model = model

    async def generate(self, text: str, system: str = ""):
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": text})
        
        response = await self.client.chat.complete_async(
            model=self.model,
            messages=messages
        )
        return LLMResponse(
            text=response.choices[0].message.content,
            tokens_used=response.usage.total_tokens,
            provider_name=type(self).__name__
        )

class FallbackProvider(LLMProvider):
    def __init__(self, providers: list[LLMProvider]):
        self.providers = providers

    async def generate(self, text: str, system: str = ""):
        for provider in self.providers:
            try:
                result = await provider.generate(text, system)
                if not result.text:
                    raise ValueError("Text from provider was None!")
            except Exception as e:
                logger.warning(f"{type(provider).__name__} has failed: {e}")
            else:
                logger.info(f"{type(provider).__name__} has successfully responded")
                return result
        return LLMResponse(
            text="Sorry, something went wrong and I couldn't generate a response. Please try again later.",
            provider_name="none",
            tokens_used=None
        )