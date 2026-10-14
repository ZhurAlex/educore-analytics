from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models import Mistake, Mistakes
from app.retrieval import (
    embed_text,
    get_exercises,
    reciprocal_rank_fusion,
)


@pytest.mark.parametrize(
    "summary_exercises, sub_topic_exercises, kwargs, expected_ids",
    [
        (
            [SimpleNamespace(id=1), SimpleNamespace(id=2), SimpleNamespace(id=3), SimpleNamespace(id=4)],
            [SimpleNamespace(id=2), SimpleNamespace(id=3), SimpleNamespace(id=1), SimpleNamespace(id=4)],
            {},
            [2, 3, 1, 4],
        ),
        (
            [SimpleNamespace(id=1), SimpleNamespace(id=2)],
            [SimpleNamespace(id=3), SimpleNamespace(id=4)],
            {},
            [3, 4, 1, 2],
        ),
        (
            [SimpleNamespace(id=1), SimpleNamespace(id=2), SimpleNamespace(id=3), SimpleNamespace(id=4)],
            [SimpleNamespace(id=2), SimpleNamespace(id=3), SimpleNamespace(id=1), SimpleNamespace(id=4)],
            {"n": 2},
            [2, 3],
        ),
    ],
    ids=[
        "same_exercises_in_both_lists_different_order",
        "disjoint_lists_sub_topic_weighted_higher",
        "n_limits_number_of_results",
    ],
)
def test_reciprocal_rank_fusion(summary_exercises, sub_topic_exercises, kwargs, expected_ids):
    results = reciprocal_rank_fusion(summary_exercises, sub_topic_exercises, **kwargs)

    assert [exercise.id for exercise in results] == expected_ids


@patch("app.retrieval.time.sleep")
def test_embed_text_returns_vector_from_embeddings_model(sleep_mock):
    mock_model = MagicMock()
    mock_model.embed_query.return_value = [0.1, 0.2, 0.3]

    result = embed_text("some text", mock_model)

    assert result == [0.1, 0.2, 0.3]
    mock_model.embed_query.assert_called_once_with("some text")


@patch("app.retrieval.reciprocal_rank_fusion")
@patch("app.retrieval.search_exercises_by_sub_topic", new_callable=AsyncMock)
@patch("app.retrieval.search_exercises_by_summary", new_callable=AsyncMock)
@patch("app.retrieval.embed_text")
@patch("app.retrieval.get_embeddings_model")
async def test_get_exercises_builds_one_entry_per_mistake_in_order(
    mock_get_model, mock_embed, mock_search_summary, mock_search_sub_topic, mock_rrf
):
    mock_get_model.return_value = "fake-embeddings-model"
    mock_embed.side_effect = ["vector-1", "vector-2"]
    mock_search_summary.side_effect = [["summary-candidates-1"], ["summary-candidates-2"]]
    mock_search_sub_topic.side_effect = [["sub-topic-candidates-1"], ["sub-topic-candidates-2"]]
    mock_rrf.side_effect = [["rrf-result-1"], ["rrf-result-2"]]

    mistake_1 = Mistake(topic="topic one", description="desc one")
    mistake_2 = Mistake(topic="topic two", description="desc two")
    mistakes = Mistakes(mistakes=[mistake_1, mistake_2])

    results = await get_exercises(mistakes)

    assert len(results) == 2
    assert results[0].index == 1
    assert results[0].mistake == mistake_1
    assert results[0].exercises == ["rrf-result-1"]
    assert results[1].index == 2
    assert results[1].mistake == mistake_2
    assert results[1].exercises == ["rrf-result-2"]

    mock_embed.assert_any_call("topic one", "fake-embeddings-model")
    mock_embed.assert_any_call("topic two", "fake-embeddings-model")
    mock_rrf.assert_any_call(["summary-candidates-1"], ["sub-topic-candidates-1"])
    mock_rrf.assert_any_call(["summary-candidates-2"], ["sub-topic-candidates-2"])


async def test_get_exercises_returns_empty_list_for_no_mistakes():
    results = await get_exercises(Mistakes(mistakes=[]))

    assert results == []
