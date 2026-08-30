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

STUDENT_ATTEMPT_CASES = [
    (
        {
            "test": {"title": "Present Simple"},
            "started_at": "2026-01-01",
            "responses": [
                {
                    "question": "Q1",
                    "answer": "A1",
                    "points_awarded": 1,
                    "max_points": 1,
                    "grading_status": "auto_graded",
                },
            ],
        },
        "\n".join(
            [
                'Test: "Present Simple"',
                "Attempt on 2026-01-01",
                "------------\nQuestion: Q1\nStudent's answer: A1\nResult: correct",
                "============",
            ]
        ),
    ),
    (
        {
            "test": {"title": "Present Simple"},
            "started_at": "2026-01-01",
            "responses": [
                {
                    "question": "Q1",
                    "answer": "A1",
                    "points_awarded": 1,
                    "max_points": 1,
                    "grading_status": "auto_graded",
                },
                {
                    "question": "Q2",
                    "answer": "A2",
                    "points_awarded": 0,
                    "max_points": 1,
                    "grading_status": "manual_check_required",
                },
            ],
        },
        "\n".join(
            [
                'Test: "Present Simple"',
                "Attempt on 2026-01-01",
                "------------\nQuestion: Q1\nStudent's answer: A1\nResult: correct",
                "============",
            ]
        ),
    ),
]

STUDENT_ATTEMPT_CASE_IDS = ["single_response", "excludes_manual_check_required"]

STUDENT_RESPONSES_CASES = [
    (
        [
            {
                "test": {"title": "Test B"},
                "started_at": "2026-02-01",
                "responses": [
                    {
                        "question": "Q2",
                        "answer": "A2",
                        "points_awarded": 1,
                        "max_points": 1,
                        "grading_status": "auto_graded",
                    },
                ],
            },
            {
                "test": {"title": "Test A"},
                "started_at": "2026-01-01",
                "responses": [
                    {
                        "question": "Q1",
                        "answer": "A1",
                        "points_awarded": 1,
                        "max_points": 1,
                        "grading_status": "auto_graded",
                    },
                ],
            },
        ],
        "\n".join(
            [
                "\n".join(
                    [
                        'Test: "Test A"',
                        "Attempt on 2026-01-01",
                        "------------\nQuestion: Q1\nStudent's answer: A1\nResult: correct",
                        "============",
                    ]
                ),
                "\n".join(
                    [
                        'Test: "Test B"',
                        "Attempt on 2026-02-01",
                        "------------\nQuestion: Q2\nStudent's answer: A2\nResult: correct",
                        "============",
                    ]
                ),
            ]
        ),
    ),
]

STUDENT_RESPONSES_CASE_IDS = ["sorts_and_joins_attempts"]

CALCULATE_WRONG_ANSWERS_CASES = [
    (
        "Q1",
        [
            {"answer": "works", "points_awarded": 1, "max_points": 1, "correct_answer": "works"},
            {"answer": "works", "points_awarded": 1, "max_points": 1, "correct_answer": "works"},
        ],
        {
            "question": "Q1",
            "correct_answer": "works",
            "total_answers": 2,
            "wrong_answers": 0,
            "top_wrong_answers": [],
        },
    ),
    (
        "Q1",
        [
            {"answer": "works", "points_awarded": 1, "max_points": 1, "correct_answer": "works"},
            {"answer": "work", "points_awarded": 0, "max_points": 1, "correct_answer": "works"},
            {"answer": "work", "points_awarded": 0, "max_points": 1, "correct_answer": "works"},
            {"answer": "working", "points_awarded": 0, "max_points": 1, "correct_answer": "works"},
        ],
        {
            "question": "Q1",
            "correct_answer": "works",
            "total_answers": 4,
            "wrong_answers": 3,
            "top_wrong_answers": [("work", 2), ("working", 1)],
        },
    ),
]

CALCULATE_WRONG_ANSWERS_CASE_IDS = ["all_correct", "counts_and_ranks_wrong_answers"]

ATTEMPTS_TO_DICT_CASES = [
    (
        [
            {
                "responses": [
                    {
                        "question": "Q1",
                        "answer": "works",
                        "points_awarded": 1,
                        "max_points": 1,
                        "correct_answer": "works",
                        "grading_status": "auto_graded",
                    },
                ],
            },
            {
                "responses": [
                    {
                        "question": "Q1",
                        "answer": "work",
                        "points_awarded": 0,
                        "max_points": 1,
                        "correct_answer": "works",
                        "grading_status": "auto_graded",
                    },
                    {
                        "question": "Q1",
                        "answer": "ignored",
                        "points_awarded": 0,
                        "max_points": 1,
                        "correct_answer": "works",
                        "grading_status": "manual_check_required",
                    },
                ],
            },
        ],
        [
            {
                "question": "Q1",
                "correct_answer": "works",
                "total_answers": 2,
                "wrong_answers": 1,
                "top_wrong_answers": [("work", 1)],
            },
        ],
    ),
]

ATTEMPTS_TO_DICT_CASE_IDS = ["groups_across_attempts_and_excludes_manual_check_required"]

FORMAT_CLASS_ATTEMPT_CASES = [
    (
        {
            "question": "Q1",
            "correct_answer": "works",
            "total_answers": 4,
            "wrong_answers": 3,
            "top_wrong_answers": [("work", 2), ("working", 1)],
        },
        "\n".join(
            [
                "Question: Q1",
                "Correct answer: works",
                "Wrong: 3/4",
                'Most common wrong answers: "work" (2), "working" (1)',
                "------------\n",
            ]
        ),
    ),
]

FORMAT_CLASS_ATTEMPT_CASE_IDS = ["typical"]

FORMAT_CLASS_RESPONSES_CASES = [
    (
        [
            {
                "test": {"title": "Present Simple"},
                "responses": [
                    {
                        "question": "Q1",
                        "answer": "works",
                        "points_awarded": 1,
                        "max_points": 1,
                        "correct_answer": "works",
                        "grading_status": "auto_graded",
                    },
                    {
                        "question": "Q2",
                        "answer": "wrong",
                        "points_awarded": 0,
                        "max_points": 1,
                        "correct_answer": "right",
                        "grading_status": "auto_graded",
                    },
                ],
            },
            {
                "test": {"title": "Present Simple"},
                "responses": [
                    {
                        "question": "Q1",
                        "answer": "works",
                        "points_awarded": 1,
                        "max_points": 1,
                        "correct_answer": "works",
                        "grading_status": "auto_graded",
                    },
                    {
                        "question": "Q2",
                        "answer": "wrong",
                        "points_awarded": 0,
                        "max_points": 1,
                        "correct_answer": "right",
                        "grading_status": "auto_graded",
                    },
                ],
            },
        ],
        "\n".join(
            [
                'Test: "Present Simple"\n',
                "\n".join(
                    [
                        "Question: Q2",
                        "Correct answer: right",
                        "Wrong: 2/2",
                        'Most common wrong answers: "wrong" (2)',
                        "------------\n",
                    ]
                ),
            ]
        ),
    ),
]

FORMAT_CLASS_RESPONSES_CASE_IDS = ["excludes_questions_with_no_wrong_answers"]
