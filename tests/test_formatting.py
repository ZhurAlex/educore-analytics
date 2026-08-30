import pytest

from app.formatting import (
    attempts_to_dict,
    calculate_wrong_answers,
    format_class_attempt,
    format_class_responses,
    format_student_attempt,
    format_student_response,
    format_student_responses,
    response_status,
)
from tests.fixtures.formatting_cases import (
    ATTEMPTS_TO_DICT_CASE_IDS,
    ATTEMPTS_TO_DICT_CASES,
    CALCULATE_WRONG_ANSWERS_CASE_IDS,
    CALCULATE_WRONG_ANSWERS_CASES,
    FORMAT_CLASS_ATTEMPT_CASE_IDS,
    FORMAT_CLASS_ATTEMPT_CASES,
    FORMAT_CLASS_RESPONSES_CASE_IDS,
    FORMAT_CLASS_RESPONSES_CASES,
    STUDENT_ATTEMPT_CASE_IDS,
    STUDENT_ATTEMPT_CASES,
    STUDENT_RESPONSE_CASE_IDS,
    STUDENT_RESPONSE_CASES,
    STUDENT_RESPONSES_CASE_IDS,
    STUDENT_RESPONSES_CASES,
)


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


@pytest.mark.parametrize("attempt, result", STUDENT_ATTEMPT_CASES, ids=STUDENT_ATTEMPT_CASE_IDS)
def test_format_student_attempt(attempt, result):
    assert format_student_attempt(attempt) == result


@pytest.mark.parametrize("attempts, result", STUDENT_RESPONSES_CASES, ids=STUDENT_RESPONSES_CASE_IDS)
def test_format_student_responses(attempts, result):
    assert format_student_responses(attempts) == result


@pytest.mark.parametrize(
    "question, responses, result", CALCULATE_WRONG_ANSWERS_CASES, ids=CALCULATE_WRONG_ANSWERS_CASE_IDS
)
def test_calculate_wrong_answers(question, responses, result):
    assert calculate_wrong_answers(question, responses) == result


@pytest.mark.parametrize("attempts, result", ATTEMPTS_TO_DICT_CASES, ids=ATTEMPTS_TO_DICT_CASE_IDS)
def test_attempts_to_dict(attempts, result):
    assert attempts_to_dict(attempts) == result


@pytest.mark.parametrize("question, result", FORMAT_CLASS_ATTEMPT_CASES, ids=FORMAT_CLASS_ATTEMPT_CASE_IDS)
def test_format_class_attempt(question, result):
    assert format_class_attempt(question) == result


@pytest.mark.parametrize("attempts, result", FORMAT_CLASS_RESPONSES_CASES, ids=FORMAT_CLASS_RESPONSES_CASE_IDS)
def test_format_class_responses(attempts, result):
    assert format_class_responses(attempts) == result
