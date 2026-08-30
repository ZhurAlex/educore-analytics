import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from app.analysis import analyse_class, analyse_student
from app.educore_client import fetch_test_attempts

router = APIRouter()


@router.get("/get_test_attempts")
async def get_test_attempts(
    subject: str | None = None,
    test_id: int | None = None,
    student_id: int | None = None,
    school_class_id: int | None = None,
):
    return await fetch_attempts(
        subject=subject, test_id=test_id, student_id=student_id, school_class_id=school_class_id
    )


@router.get("/students/{student_id}/gap-analysis", response_class=PlainTextResponse)
async def get_students_attempts(student_id: int, language: str = "English", subject: str = "english"):
    responses = await fetch_attempts(subject=subject, student_id=student_id)
    if not responses:
        return "No results for this student"
    res = await analyse_student(responses, subject=subject, language=language)
    return res.text


@router.get("/class/{test_id}/class-analysis", response_class=PlainTextResponse)
async def get_class_attempts(test_id: int, school_class_id: int, language: str = "English", subject: str = "english"):
    responses = await fetch_attempts(test_id=test_id, school_class_id=school_class_id)
    if not responses:
        return "No results for this class"
    res = await analyse_class(responses, subject=subject, language=language)
    return res.text


async def fetch_attempts(
    subject: str | None = None,
    test_id: int | None = None,
    student_id: int | None = None,
    school_class_id: int | None = None,
):
    try:
        return await fetch_test_attempts(
            subject=subject, test_id=test_id, student_id=student_id, school_class_id=school_class_id
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=str(exc))
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
