from unittest.mock import AsyncMock, patch

import httpx
from fastapi.testclient import TestClient

from app.main import app
from app.providers import LLMResponse

client = TestClient(app)


@patch("app.routes.fetch_classes", new_callable=AsyncMock)
def test_root_route_returns_classes(mock_fetch):
    mock_fetch.return_value = [{"id": 1, "name": "1-A"}]

    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "1-A" in response.text


@patch("app.routes.fetch_students", new_callable=AsyncMock)
def test_students_list_returns_students(mock_fetch):
    mock_fetch.return_value = [{"id": 1, "name": "John Doe"}]

    response = client.get("/class/1/students", params={"subject": "english", "language": "English"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "John Doe" in response.text


@patch("app.routes.fetch_tests", new_callable=AsyncMock)
def test_tests_list_returns_tests(mock_fetch):
    mock_fetch.return_value = [{"id": 1, "title": "Test 1", "subject": "english"}]

    response = client.get("/class/1/tests", params={"subject": "english", "language": "English"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Test 1" in response.text


def test_analysis_configuration_route():
    response = client.get("/classes/1")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "/class/1/tests" in response.text


@patch("app.routes.analyse_student", new_callable=AsyncMock)
@patch("app.routes.fetch_test_attempts", new_callable=AsyncMock)
def test_gap_analysis_returns_html_text(mock_fetch, mock_analyse):
    mock_fetch.return_value = [{"id": 1}]
    mock_analyse.return_value = LLMResponse(text="Recommendation text", provider_name="X", tokens_used=1)

    response = client.get("/students/1/gap-analysis")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Recommendation text" in response.text


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
    assert "No results for this student" in response.text
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
def test_class_analysis_returns_html_text(mock_fetch, mock_analyse):
    mock_fetch.return_value = [{"id": 1}]
    mock_analyse.return_value = LLMResponse(text="Class recommendation", provider_name="X", tokens_used=1)

    response = client.get("/class/1/class-analysis", params={"school_class_id": 5})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Class recommendation" in response.text


@patch("app.routes.analyse_class", new_callable=AsyncMock)
@patch("app.routes.fetch_test_attempts", new_callable=AsyncMock)
def test_class_analysis_passes_subject_and_language(mock_fetch, mock_analyse):
    mock_fetch.return_value = [{"id": 1}]
    mock_analyse.return_value = LLMResponse(text="Class recommendation", provider_name="X", tokens_used=1)

    client.get("/class/1/class-analysis", params={"school_class_id": 5, "subject": "math", "language": "English"})

    mock_fetch.assert_called_once_with(subject="math", test_id=1, student_id=None, school_class_id=5)
    mock_analyse.assert_called_once_with([{"id": 1}], subject="math", language="English")


@patch("app.routes.analyse_class", new_callable=AsyncMock)
@patch("app.routes.fetch_test_attempts", new_callable=AsyncMock)
def test_class_analysis_no_results(mock_fetch, mock_analyse):
    mock_fetch.return_value = []

    response = client.get("/class/1/class-analysis", params={"school_class_id": 5})

    assert response.status_code == 200
    assert "No results for this class" in response.text
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
