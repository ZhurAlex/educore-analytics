import httpx
from settings import EDUCORE_HOST, EDUCORE_API_KEY


def fetch_test_attempts(
    subject: str,
    test_id: int | None = None,
    student_id: int | None = None,
    school_class_id: int | None = None
):
    url = f"{EDUCORE_HOST}/api/test_attempts"
    headers = {"Authorization": f"Bearer {EDUCORE_API_KEY}"}
    params = {
        "test_id": test_id,
        "student_id": student_id,
        "school_class_id": school_class_id,
        "subject": subject,
    }

    res = httpx.get(url, headers=headers, params=params)
    res.raise_for_status()
    return res.json()
