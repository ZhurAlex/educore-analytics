from unittest.mock import patch

from app.analysis import analyse_class, analyse_student
from app.models import Mistake, Mistakes, MistakeWithExercises, RecommendedExercise, RecommendedExercises
from common.models import Exercise


@patch("app.analysis.make_request_to_LLM")
@patch("app.analysis.get_exercises")
@patch("app.analysis.format_student_responses")
async def test_analyse_student(mock_format, mock_db, mock_llm):
    mock_format.return_value = "formatted history text"
    mock_llm.side_effect = [
        Mistakes(mistakes=[Mistake(topic="grammar", description="Student made a grammar mistake")]),
        RecommendedExercises(
            recommendations=[RecommendedExercise(index=0, best_exercise_id=1, other_exercise_ids=[2, 3])]
        ),
    ]
    mock_db.return_value = [
        MistakeWithExercises(
            index=0,
            mistake=Mistake(topic="grammar", description="Student made a grammar mistake"),
            exercises=[Exercise(id=1, number=1), Exercise(id=2, number=2), Exercise(id=3, number=3)],
        )
    ]
    result = await analyse_student(responses="Student responses", subject="math", language="English")

    assert result[0].description == "Student made a grammar mistake"


@patch("app.analysis.make_request_to_LLM")
@patch("app.analysis.get_exercises")
@patch("app.analysis.format_class_responses")
async def test_analyse_class(mock_format, mock_db, mock_llm):
    mock_format.return_value = "formatted class text"
    mock_llm.side_effect = [
        Mistakes(mistakes=[Mistake(topic="grammar", description="Class made a grammar mistake")]),
        RecommendedExercises(
            recommendations=[RecommendedExercise(index=0, best_exercise_id=1, other_exercise_ids=[2, 3])]
        ),
    ]
    mock_db.return_value = [
        MistakeWithExercises(
            index=0,
            mistake=Mistake(topic="grammar", description="Class made a grammar mistake"),
            exercises=[Exercise(id=1, number=1), Exercise(id=2, number=2), Exercise(id=3, number=3)],
        )
    ]
    result = await analyse_class(responses="Class responses", subject="math", language="English")

    assert result[0].description == "Class made a grammar mistake"
