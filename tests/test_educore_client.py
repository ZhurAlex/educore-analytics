from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.educore_client import fetch_test_attempts

FAKE_TEST_ATTEMPTS_RESPONSE = [
    {
        "id": 1,
        "status": "completed",
        "score": 1.0,
        "started_at": "2026-01-01T00:00:00.000Z",
        "student": {"id": 1, "name": "Test Student"},
        "test": {"id": 1, "title": "Present Simple", "subject": "english"},
        "responses": [],
    }
]


@patch("httpx.AsyncClient.get", new_callable=AsyncMock)
async def test_fetch_test_attempts(mock_get):
    mock_get.return_value = httpx.Response(
        200,
        json=FAKE_TEST_ATTEMPTS_RESPONSE,
        request=httpx.Request("GET", "http://educore.test/api/test_attempts"),
    )

    result = await fetch_test_attempts(subject="english")

    assert result == FAKE_TEST_ATTEMPTS_RESPONSE


@patch("httpx.AsyncClient.get", new_callable=AsyncMock)
async def test_fetch_test_attempts_raises_on_error_status(mock_get):
    mock_get.return_value = httpx.Response(
        400,
        json={"error": "bad request"},
        request=httpx.Request("GET", "http://educore.test/api/test_attempts"),
    )

    with pytest.raises(httpx.HTTPStatusError):
        await fetch_test_attempts(subject="english")
