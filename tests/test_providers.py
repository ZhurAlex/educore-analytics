from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.providers import make_request_to_LLM


@patch("app.providers.ChatGoogleGenerativeAI")
@patch("app.providers.ChatMistralAI")
@patch("app.providers.ChatOpenAI")
async def test_make_request_to_LLM(mock_openai, mock_mistral, mock_gemini):
    gemini = mock_gemini.return_value.with_structured_output.return_value
    mistral = mock_mistral.return_value.with_structured_output.return_value
    openai = mock_openai.return_value.with_structured_output.return_value

    model = gemini.with_fallbacks.return_value
    model.ainvoke = AsyncMock(return_value="mocked response")

    response_model = SimpleNamespace()
    result = await make_request_to_LLM("test message", "test system prompt", response_model)
    assert result == "mocked response"
    mock_gemini.return_value.with_structured_output.assert_called_once_with(response_model)
    mock_mistral.return_value.with_structured_output.assert_called_once_with(response_model)
    mock_openai.return_value.with_structured_output.assert_called_once_with(response_model)
    gemini.with_fallbacks.assert_called_once_with([mistral, openai])
    model.ainvoke.assert_called_once()
