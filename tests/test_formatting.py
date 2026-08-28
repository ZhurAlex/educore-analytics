import pytest

from app.formatting import format_student_response, response_status
from tests.formatting_cases import STUDENT_RESPONSE_CASE_IDS, STUDENT_RESPONSE_CASES


@pytest.mark.parametrize(
    "points, max_points, status",
    [
        (5, 5, "correct"),
        (0, 5, "incorrect"),
        (3, 5, "partially correct"),
    ],
)
def test_response_status(points, max_points, status):
    assert response_status(points, max_points) == status


@pytest.mark.parametrize("question, result", STUDENT_RESPONSE_CASES, ids=STUDENT_RESPONSE_CASE_IDS)
def test_format_student_response(question, result):
    assert format_student_response(question) == result
