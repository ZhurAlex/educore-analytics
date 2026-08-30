from unittest.mock import AsyncMock, patch

from app.analysis import analyse_class, analyse_student
from app.providers import LLMResponse


@patch("app.analysis.provider.generate", new_callable=AsyncMock)
@patch("app.analysis.format_student_responses")
async def test_analyse_student(mock_format, mock_generate):
    mock_format.return_value = "formatted history text"
    mock_generate.return_value = LLMResponse(text="Student recommendation", provider_name="X", tokens_used=1)

    result = await analyse_student(responses="Student responses", subject="math", language="English")

    mock_generate.assert_called_once()
    assert result.text == "Student recommendation"

@patch("app.analysis.provider.generate", new_callable=AsyncMock)
@patch("app.analysis.format_class_responses")
async def test_analyse_class(mock_format, mock_generate):
    mock_format.return_value = "formatted class text"
    mock_generate.return_value = LLMResponse(text="Class recommendation", provider_name="X", tokens_used=1)

    result = await analyse_class(responses="Class responses", subject="math", language="English")

    mock_generate.assert_called_once()
    assert result.text == "Class recommendation"