import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common.models import Exercise, Chapter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from config import async_session
from sqlalchemy import select
import json
import asyncio
import time

# Free tier limit for gemini-embedding-2 is 100 requests/minute; spacing calls
# out keeps us under it instead of racing to a 429.
EMBED_REQUEST_DELAY_SECONDS = 0.65


def get_embeddings_model():
    return GoogleGenerativeAIEmbeddings(model="gemini-embedding-2-preview", output_dimensionality=768)

def embed_text(text, embeddings_model):
    vector = embeddings_model.embed_query(text)
    time.sleep(EMBED_REQUEST_DELAY_SECONDS)
    return vector

def load_json(output_path="data/parsed/english/grammatika_golitsynskiy.json"):
    path = Path(output_path)
    return json.loads(path.read_text(encoding="utf-8"))

def create_chapter_index(chapter_data):
    chapter = Chapter(topic=chapter_data["topic"])
    print(f"Created chapter: {chapter.topic}")
    return chapter

def create_exercise(exercise_data, chapter, embeddings_model):
    exercise = Exercise(
        chapter=chapter,
        number=exercise_data["number"],
        page=exercise_data["page"],
        sub_topic=exercise_data.get("sub_topic"),
        embedded_sub_topic=embed_text(exercise_data["sub_topic"], embeddings_model) if exercise_data.get("sub_topic") else None,
        task_type=exercise_data["task_type"],
        text=exercise_data["text"],
        rule=exercise_data.get("rule"),
        summary=exercise_data["summary"],
        embedded_summary=embed_text(exercise_data["summary"], embeddings_model),
        needs_review=exercise_data["needs_review"],
        review_reason=exercise_data.get("review_reason")
    )
    print(f"Created exercise: {exercise.number}")
    return exercise

async def save_chapter_and_exercises(chapter):
    async with async_session() as session:
        session.add(chapter)
        await session.commit()

async def chapter_already_saved(topic):
    async with async_session() as session:
        result = await session.execute(select(Chapter.id).where(Chapter.topic == topic))
        return result.scalar_one_or_none() is not None


async def main():
    embeddings = get_embeddings_model()
    for chapter_data in load_json():
        if await chapter_already_saved(chapter_data["topic"]):
            print(f"Skipping chapter '{chapter_data['topic']}', already saved")
            continue
        chapter = create_chapter_index(chapter_data)
        chapter.exercises = [create_exercise(ex_data, chapter, embeddings) for ex_data in chapter_data["exercises"]]
        await save_chapter_and_exercises(chapter)

# fill in the embedded_sub_topic column for existing exercises after the column has been added to the database
async def fill_sub_topic_embeddings():
    embeddings = get_embeddings_model()
    async with async_session() as session:
        result = await session.execute(select(Exercise).where(Exercise.sub_topic.isnot(None)))
        exercises = result.scalars().all()
        for exercise in exercises:
            if exercise.embedded_sub_topic is None:
                exercise.embedded_sub_topic = embed_text(exercise.sub_topic, embeddings)
                await session.commit()
                print(f"Updated embedded_sub_topic for exercise {exercise.number}")


if __name__ == "__main__":
    # asyncio.run(main())
    asyncio.run(fill_sub_topic_embeddings())
