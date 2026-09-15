import httpx

from config.settings import EDUCORE_API_KEY, EDUCORE_HOST


async def fetch_test_attempts(
    subject: str, test_id: int | None = None, student_id: int | None = None, school_class_id: int | None = None
):
    url = f"{EDUCORE_HOST}/api/test_attempts"
    params = {
        "test_id": test_id,
        "student_id": student_id,
        "school_class_id": school_class_id,
        "subject": subject,
    }
    return await make_request(url, params)


async def fetch_classes():
    url = f"{EDUCORE_HOST}/api/school_classes"
    return await make_request(url)


async def fetch_students(class_id: int):
    url = f"{EDUCORE_HOST}/api/students"
    params = {"school_class_id": class_id}
    return await make_request(url, params)


async def fetch_tests(class_id: int):
    url = f"{EDUCORE_HOST}/api/tests"
    params = {"school_class_id": class_id}
    return await make_request(url, params)


async def make_request(url, params=None):
    params = params or {}
    headers = {"Authorization": f"Bearer {EDUCORE_API_KEY}"}
    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=headers, params=params)
    res.raise_for_status()
    return res.json()
