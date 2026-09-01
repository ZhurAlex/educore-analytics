import bleach
import httpx
import markdown
from fastapi import APIRouter, HTTPException, Request
from fastapi.templating import Jinja2Templates

from app.analysis import analyse_class, analyse_student
from app.educore_client import fetch_classes, fetch_students, fetch_test_attempts, fetch_tests

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

ALLOWED_RESULT_TAGS = [
    "p",
    "strong",
    "em",
    "ul",
    "ol",
    "li",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "a",
    "code",
    "pre",
    "blockquote",
    "br",
    "hr",
]
ALLOWED_RESULT_ATTRIBUTES = {"a": ["href", "title"]}


@router.get("/")
async def get_root(request: Request):
    classes = await fetch_classes()
    classes = sorted(classes, key=lambda cls: cls["name"])
    return templates.TemplateResponse(request, "classes.html", {"classes": classes})


@router.get("/class/{class_id}/students")
async def students_list(request: Request, class_id: int, language: str, subject: str):
    students = await fetch_students(class_id)
    params = {"students": students, "class_id": class_id, "subject": subject, "language": language}
    return templates.TemplateResponse(request, "students.html", params)


@router.get("/class/{class_id}/tests")
async def tests_list(request: Request, class_id: int, language: str, subject: str):
    tests = await fetch_tests(class_id)
    params = {"tests": tests, "class_id": class_id, "subject": subject, "language": language}
    return templates.TemplateResponse(request, "tests.html", params)


@router.get("/classes/{class_id}")
async def analysis_configuration(request: Request, class_id: int):
    return templates.TemplateResponse(request, "analysis_configuration.html", {"class_id": class_id})


@router.get("/students/{student_id}/gap-analysis")
async def get_students_attempts(request: Request, student_id: int, language: str = "English", subject: str = "english"):
    responses = await fetch_attempts(subject=subject, student_id=student_id)
    return await render_analysis(request, responses, analyse_student, subject, language, "No results for this student")


@router.get("/class/{test_id}/class-analysis")
async def get_class_attempts(
    request: Request, test_id: int, school_class_id: int, language: str = "English", subject: str = "english"
):
    responses = await fetch_attempts(test_id=test_id, school_class_id=school_class_id)
    return await render_analysis(request, responses, analyse_class, subject, language, "No results for this class")


async def render_analysis(request, responses, analyse_fn, subject, language, no_results_message):
    if not responses:
        return templates.TemplateResponse(request, "no_results.html", {"result_message": no_results_message})
    res = await analyse_fn(responses, subject=subject, language=language)
    result_html = bleach.clean(
        markdown.markdown(res.text), tags=ALLOWED_RESULT_TAGS, attributes=ALLOWED_RESULT_ATTRIBUTES, strip=True
    )
    return templates.TemplateResponse(request, "analysis_results.html", {"res": res, "result_html": result_html})


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
