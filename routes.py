from fastapi import APIRouter, HTTPException, Body
from educore_client import fetch_test_attempts
from analysis import analyse
import httpx

router = APIRouter()

@router.get("/get_test_attempts")
def get_test_attempts(
    subject: str,
    test_id: int | None = None,
    student_id: int | None = None,
    school_class_id: int | None = None
):
    return fetch_attempts(
                    subject=subject,
                    test_id=test_id,
                    student_id=student_id,
                    school_class_id=school_class_id
                )

@router.get("/students/{student_id}/gap-analysis")
def get_students_attempts(
    student_id: int,
    subject: str = "english"
):
    responses = fetch_attempts(subject=subject, student_id=student_id)
    return analyse(responses)

def fetch_attempts(
    subject: str,
    test_id: int | None = None,
    student_id: int | None = None,
    school_class_id: int | None = None
):
    try:
        return fetch_test_attempts(
            subject=subject,
            test_id=test_id,
            student_id=student_id,
            school_class_id=school_class_id
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=str(exc))
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=str(exc))