from collections import Counter, defaultdict

IGNORED_GRADING_STATUSES = {"pending", "manual_check_required"}


def response_status(points, max_points):
    if max_points == points:
        return "correct"
    elif points == 0:
        return "incorrect"
    else:
        return "partially correct"


def format_student_response(question):
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


def format_student_attempt(attempt):
    header = [f'Test: "{attempt["test"]["title"]}"', f"Attempt on {attempt['started_at']}"]
    blocks = [
        format_student_response(question)
        for question in attempt["responses"]
        if question["grading_status"] not in IGNORED_GRADING_STATUSES
    ]
    return "\n".join(header + ["------------\n" + block for block in blocks] + ["============"])


def format_student_responses(attempts):
    attempts.sort(key=lambda attempt: attempt["started_at"])
    return "\n".join(format_student_attempt(attempt) for attempt in attempts)


########################################################################################################
def calculate_wrong_answers(question, responses):
    wrong = [r for r in responses if response_status(r["points_awarded"], r["max_points"]) != "correct"]
    wrong_answers = Counter(r["answer"] for r in wrong)
    top_wrong = wrong_answers.most_common(3)
    return {
        "question": question,
        "correct_answer": responses[0]["correct_answer"],
        "total_answers": len(responses),
        "wrong_answers": len(wrong),
        "top_wrong_answers": top_wrong,
    }


def attempts_to_dict(attempts):
    by_question = defaultdict(list)
    for attempt in attempts:
        for response in attempt["responses"]:
            if response["grading_status"] in IGNORED_GRADING_STATUSES:
                continue
            by_question[response["question"]].append(response)
    return [calculate_wrong_answers(question, responses) for question, responses in by_question.items()]


def format_class_attempt(question):
    lines = [
        f"Question: {question['question']}",
        f"Correct answer: {question['correct_answer']}",
        f"Wrong: {question['wrong_answers']}/{question['total_answers']}",
        f"Most common wrong answers: {', '.join(f'"{a[0]}" ({a[1]})' for a in question['top_wrong_answers'])}",
        "------------\n",
    ]
    return "\n".join(lines)


def format_class_responses(attempts):
    answers_dictionary = attempts_to_dict(attempts)
    header = [f'Test: "{attempts[0]["test"]["title"]}"\n']
    return "\n".join(header + [format_class_attempt(ans) for ans in answers_dictionary if ans["wrong_answers"] > 0])
