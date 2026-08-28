STUDENT_RESPONSE_CASES = [
    (
        {"question": "Test question", "answer": "Test answer", "points_awarded": 5, "max_points": 5},
        "Question: Test question\nStudent's answer: Test answer\nResult: correct",
    ),
    (
        {
            "question": "Test question",
            "answer": "Test answer",
            "points_awarded": 5,
            "max_points": 3,
            "answer_type": "long_text",
            "feedback": "Test feedback",
        },
        "\n".join(
            [
                "Question: Test question",
                "Student's answer: Test answer",
                "Grader's note: Test feedback",
                "Result: partially correct",
            ]
        ),
    ),
    (
        {
            "question": "Test question",
            "answer": "Test answer",
            "points_awarded": 0,
            "max_points": 5,
            "answer_type": "short_text",
            "correct_answer": "Test correct answer",
        },
        "\n".join(
            [
                "Question: Test question",
                "Student's answer: Test answer",
                "Correct answer: Test correct answer",
                "Result: incorrect",
            ]
        ),
    ),
]

STUDENT_RESPONSE_CASE_IDS = ["correct", "partial_long_text", "incorrect_short_text"]
