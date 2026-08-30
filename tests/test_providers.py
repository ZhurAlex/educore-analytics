from unittest.mock import AsyncMock, MagicMock, patch
from types import SimpleNamespace

import pytest

from app.providers import FallbackProvider, GeminiProvider, LLMProvider, LLMResponse, MistralProvider


class FakeProvider(LLMProvider):
    def __init__(self, response, error: Exception | None = None):
        self.response = response
        self.error = error

    async def generate(self, text, system=""):
        if self.error:
            raise self.error
        return self.response


DEFAULT_FALLBACK_RESPONSE = LLMResponse(
    text="Sorry, something went wrong and I couldn't generate a response. Please try again later.",
    provider_name="none",
    tokens_used=None,
)


@pytest.mark.parametrize(
    "providers, expected",
    [
        (
            [FakeProvider(LLMResponse(text="Successful response text", provider_name="FakeProvider", tokens_used=100))],
            LLMResponse(text="Successful response text", provider_name="FakeProvider", tokens_used=100),
        ),
        (
            [FakeProvider(None, error=ValueError("Test error"))],
            DEFAULT_FALLBACK_RESPONSE,
        ),
        (
            [FakeProvider(LLMResponse(text="", provider_name="FakeProvider", tokens_used=None))],
            DEFAULT_FALLBACK_RESPONSE,
        ),
        (
            [
                FakeProvider(None, error=ValueError("first failed")),
                FakeProvider(LLMResponse(text="From second", provider_name="Second", tokens_used=5)),
            ],
            LLMResponse(text="From second", provider_name="Second", tokens_used=5),
        ),
    ],
    ids=["success", "fail_with_error", "fail_with_empty_text", "falls_back_to_second_provider"],
)
async def test_fallback_provider_generate(providers, expected):
    assert await FallbackProvider(providers=providers).generate(text="Test prompt") == expected



@patch("google.genai.Client")
async def test_gemini_provider_generate(mock_client_class):
    fake_response = SimpleNamespace(
        text="Generated answer",
        usage_metadata=SimpleNamespace(total_token_count=42),
    )

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(return_value=fake_response)
    mock_client_class.return_value = mock_client

    provider = GeminiProvider(api_key="fake-key")
    result = await provider.generate("hello", system="be nice")

    assert result == LLMResponse(text="Generated answer", tokens_used=42, provider_name="GeminiProvider")

@patch("app.providers.Mistral")
async def test_mistral_provider_generate(mock_client_class):
    fake_response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="Mistral answer"))],
        usage=SimpleNamespace(total_tokens=50),
    )
    mock_client = MagicMock()
    mock_client.chat.complete_async = AsyncMock(return_value=fake_response)
    mock_client_class.return_value = mock_client

    provider = MistralProvider(api_key="fake-key")
    result = await provider.generate("hello", system="be nice")
    assert result == LLMResponse(text="Mistral answer", tokens_used=50, provider_name="MistralProvider")