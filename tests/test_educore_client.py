from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.educore_client import fetch_classes, fetch_students, fetch_test_attempts, fetch_tests
from config.settings import EDUCORE_API_KEY, EDUCORE_HOST

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


@patch("httpx.AsyncClient.get", new_callable=AsyncMock)
async def test_fetch_classes(mock_get):
    mock_get.return_value = httpx.Response(
        200,
        json=[{"id": 1, "name": "7-A"}, {"id": 2, "name": "8-B"}],
        request=httpx.Request("GET", "http://educore.test/api/school_classes"),
    )

    result = await fetch_classes()

    assert result == [{"id": 1, "name": "7-A"}, {"id": 2, "name": "8-B"}]
    mock_get.assert_called_once_with(
        f"{EDUCORE_HOST}/api/school_classes",
        headers={"Authorization": f"Bearer {EDUCORE_API_KEY}"},
        params={},
    )


@patch("httpx.AsyncClient.get", new_callable=AsyncMock)
async def test_fetch_students(mock_get):
    mock_get.return_value = httpx.Response(
        200,
        json=[{"id": 1, "name": "John Doe"}],
        request=httpx.Request("GET", "http://educore.test/api/students"),
    )

    result = await fetch_students(class_id=1)

    assert result == [{"id": 1, "name": "John Doe"}]
    mock_get.assert_called_once_with(
        f"{EDUCORE_HOST}/api/students",
        headers={"Authorization": f"Bearer {EDUCORE_API_KEY}"},
        params={"school_class_id": 1},
    )


@patch("httpx.AsyncClient.get", new_callable=AsyncMock)
async def test_fetch_tests(mock_get):
    mock_get.return_value = httpx.Response(
        200,
        json=[{"id": 1, "title": "Present Simple", "subject": "english"}],
        request=httpx.Request("GET", "http://educore.test/api/tests"),
    )

    result = await fetch_tests(class_id=1)

    assert result == [{"id": 1, "title": "Present Simple", "subject": "english"}]
    mock_get.assert_called_once_with(
        f"{EDUCORE_HOST}/api/tests",
        headers={"Authorization": f"Bearer {EDUCORE_API_KEY}"},
        params={"school_class_id": 1},
    )
