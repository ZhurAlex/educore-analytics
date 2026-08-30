from unittest.mock import AsyncMock, patch

import httpx
from fastapi.testclient import TestClient

from app.main import app
from app.providers import LLMResponse

client = TestClient(app)


@patch("app.routes.analyse_student", new_callable=AsyncMock)
@patch("app.routes.fetch_test_attempts", new_callable=AsyncMock)
def test_gap_analysis_returns_plain_text(mock_fetch, mock_analyse):
    mock_fetch.return_value = [{"id": 1}]
    mock_analyse.return_value = LLMResponse(text="Recommendation text", provider_name="X", tokens_used=1)

    response = client.get("/students/1/gap-analysis")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert response.text == "Recommendation text"


@patch("app.routes.analyse_student", new_callable=AsyncMock)
@patch("app.routes.fetch_test_attempts", new_callable=AsyncMock)
def test_gap_analysis_passes_subject_and_language(mock_fetch, mock_analyse):
    mock_fetch.return_value = [{"id": 1}]
    mock_analyse.return_value = LLMResponse(text="Recommendation text", provider_name="X", tokens_used=1)

    client.get("/students/1/gap-analysis", params={"subject": "math", "language": "English"})

    mock_fetch.assert_called_once_with(subject="math", test_id=None, student_id=1, school_class_id=None)
    mock_analyse.assert_called_once_with([{"id": 1}], subject="math", language="English")


@patch("app.routes.analyse_student", new_callable=AsyncMock)
@patch("app.routes.fetch_test_attempts", new_callable=AsyncMock)
def test_gap_analysis_no_results(mock_fetch, mock_analyse):
    mock_fetch.return_value = []

    response = client.get("/students/1/gap-analysis")

    assert response.status_code == 200
    assert response.text == "No results for this student"
    mock_analyse.assert_not_called()


@patch("app.routes.fetch_test_attempts", new_callable=AsyncMock)
def test_gap_analysis_propagates_educore_status_error(mock_fetch):
    request = httpx.Request("GET", "http://educore.test/api/test_attempts")
    mock_fetch.side_effect = httpx.HTTPStatusError(
        "Not found", request=request, response=httpx.Response(404, request=request)
    )

    response = client.get("/students/1/gap-analysis")

    assert response.status_code == 404


@patch("app.routes.fetch_test_attempts", new_callable=AsyncMock)
def test_gap_analysis_propagates_educore_connection_error(mock_fetch):
    request = httpx.Request("GET", "http://educore.test/api/test_attempts")
    mock_fetch.side_effect = httpx.RequestError("Connection refused", request=request)

    response = client.get("/students/1/gap-analysis")

    assert response.status_code == 502


@patch("app.routes.analyse_class", new_callable=AsyncMock)
@patch("app.routes.fetch_test_attempts", new_callable=AsyncMock)
def test_class_analysis_returns_plain_text(mock_fetch, mock_analyse):
    mock_fetch.return_value = [{"id": 1}]
    mock_analyse.return_value = LLMResponse(text="Class recommendation", provider_name="X", tokens_used=1)

    response = client.get("/class/1/class-analysis", params={"school_class_id": 5})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert response.text == "Class recommendation"


@patch("app.routes.analyse_class", new_callable=AsyncMock)
@patch("app.routes.fetch_test_attempts", new_callable=AsyncMock)
def test_class_analysis_passes_subject_and_language(mock_fetch, mock_analyse):
    mock_fetch.return_value = [{"id": 1}]
    mock_analyse.return_value = LLMResponse(text="Class recommendation", provider_name="X", tokens_used=1)

    client.get("/class/1/class-analysis", params={"school_class_id": 5, "subject": "math", "language": "English"})

    mock_fetch.assert_called_once_with(subject=None, test_id=1, student_id=None, school_class_id=5)
    mock_analyse.assert_called_once_with([{"id": 1}], subject="math", language="English")


@patch("app.routes.analyse_class", new_callable=AsyncMock)
@patch("app.routes.fetch_test_attempts", new_callable=AsyncMock)
def test_class_analysis_no_results(mock_fetch, mock_analyse):
    mock_fetch.return_value = []

    response = client.get("/class/1/class-analysis", params={"school_class_id": 5})

    assert response.status_code == 200
    assert response.text == "No results for this class"
    mock_analyse.assert_not_called()


@patch("app.routes.fetch_test_attempts", new_callable=AsyncMock)
def test_class_analysis_propagates_educore_status_error(mock_fetch):
    request = httpx.Request("GET", "http://educore.test/api/test_attempts")
    mock_fetch.side_effect = httpx.HTTPStatusError(
        "Not found", request=request, response=httpx.Response(404, request=request)
    )

    response = client.get("/class/1/class-analysis", params={"school_class_id": 5})

    assert response.status_code == 404


@patch("app.routes.fetch_test_attempts", new_callable=AsyncMock)
def test_class_analysis_propagates_educore_connection_error(mock_fetch):
    request = httpx.Request("GET", "http://educore.test/api/test_attempts")
    mock_fetch.side_effect = httpx.RequestError("Connection refused", request=request)

    response = client.get("/class/1/class-analysis", params={"school_class_id": 5})

    assert response.status_code == 502


def test_class_analysis_requires_school_class_id():
    response = client.get("/class/1/class-analysis")

    assert response.status_code == 422
