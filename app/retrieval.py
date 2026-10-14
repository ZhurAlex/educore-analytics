import logging
import time

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from sqlalchemy import select

from app.models import MistakeWithExercises
from common.models import Exercise
from config import async_session

logger = logging.getLogger(__name__)

EMBED_REQUEST_DELAY_SECONDS = 0.65  # Delay between embedding requests to avoid rate limiting
RRF_K = 60  # Reciprocal Rank Fusion parameter
FETCH_DEPTH = 50
TOP_EXERCISES = 10


async def search_exercises_by_summary(query_vector, k=FETCH_DEPTH):
    async with async_session() as session:
        stmt = select(Exercise).order_by(Exercise.embedded_summary.cosine_distance(query_vector)).limit(k)
        result = await session.execute(stmt)
        return result.scalars().all()


async def search_exercises_by_sub_topic(query_vector, k=FETCH_DEPTH):
    async with async_session() as session:
        stmt = select(Exercise).order_by(Exercise.embedded_sub_topic.cosine_distance(query_vector)).limit(k)
        result = await session.execute(stmt)
        return result.scalars().all()


def get_embeddings_model():
    return GoogleGenerativeAIEmbeddings(model="gemini-embedding-2-preview", output_dimensionality=768)


def embed_text(text, embeddings_model):
    vector = embeddings_model.embed_query(text)
    time.sleep(EMBED_REQUEST_DELAY_SECONDS)
    return vector


def reciprocal_rank_fusion(
    summary_exercises, sub_topic_exercises, n=TOP_EXERCISES, summary_weight=0.3, sub_topic_weight=0.7
):
    scores = {}
    exercises_by_id = {}

    for rank, exercise in enumerate(summary_exercises, start=1):
        scores[exercise.id] = scores.get(exercise.id, 0) + summary_weight / (RRF_K + rank)
        exercises_by_id[exercise.id] = exercise

    for rank, exercise in enumerate(sub_topic_exercises, start=1):
        scores[exercise.id] = scores.get(exercise.id, 0) + sub_topic_weight / (RRF_K + rank)
        exercises_by_id[exercise.id] = exercise

    ranked_ids = sorted(scores, key=scores.get, reverse=True)
    return [exercises_by_id[eid] for eid in ranked_ids[:n]]


async def get_exercises(mistakes):
    embeddings_model = get_embeddings_model()
    results = []
    for i, mistake in enumerate(mistakes.mistakes, start=1):
        logger.info("[%d/%d] embedding topic: %s", i, len(mistakes.mistakes), mistake.topic)
        embeded_topic = embed_text(mistake.topic, embeddings_model)
        logger.info("[%d/%d] embedded, searching...", i, len(mistakes.mistakes))
        summary_exercises = await search_exercises_by_summary(embeded_topic)
        sub_topic_exercises = await search_exercises_by_sub_topic(embeded_topic)
        logger.info("[%d/%d] search done, fusing...", i, len(mistakes.mistakes))
        exercises = reciprocal_rank_fusion(summary_exercises, sub_topic_exercises)
        results.append(MistakeWithExercises(index=i, mistake=mistake, exercises=exercises))
    return results
