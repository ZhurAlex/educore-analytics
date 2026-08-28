import httpx

from app.settings import EDUCORE_API_KEY, EDUCORE_HOST


async def fetch_test_attempts(
    subject: str, test_id: int | None = None, student_id: int | None = None, school_class_id: int | None = None
):
    url = f"{EDUCORE_HOST}/api/test_attempts"
    headers = {"Authorization": f"Bearer {EDUCORE_API_KEY}"}
    params = {
        "test_id": test_id,
        "student_id": student_id,
        "school_class_id": school_class_id,
        "subject": subject,
    }

    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=headers, params=params)
    res.raise_for_status()
    return res.json()
