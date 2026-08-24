IGNORED_GRADING_STATUSES = {"pending", "manual_check_required"}


def response_status(points, max_points):
    if max_points == points:
        return "correct"
    elif points == 0:
        return "incorrect"
    else:
        return "partially correct"


def format_response(question):
    lines = [
        f"Question: {question['question']}",
        f"Student's answer: {question['answer']}",
    ]
    status = response_status(question["points_awarded"], question["max_points"])
    if status != "correct":
        if question["answer_type"] == "long_text":
            lines.append(f"Grader's note: {question['feedback']}")
        else:
            lines.append(f"Correct answer: {question['correct_answer']}")
    lines.append(f"Result: {status}")
    return "\n".join(lines)


def format_attempt(attempt):
    header = [f'Test: "{attempt["test"]["title"]}"', f"Attempt on {attempt['started_at']}"]
    blocks = [
        format_response(question)
        for question in attempt["responses"]
        if question["grading_status"] not in IGNORED_GRADING_STATUSES
    ]
    return "\n".join(header + ["------------\n" + block for block in blocks] + ["============"])


def format_responses(attempts):
    attempts.sort(key=lambda attempt: attempt["started_at"])
    return "\n".join(format_attempt(attempt) for attempt in attempts)
