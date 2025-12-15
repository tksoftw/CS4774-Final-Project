"""Courses router for browsing and searching courses."""

from fastapi import APIRouter, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.config import get_settings
from app.services.sis_service import SISService

router = APIRouter(prefix="/courses", tags=["courses"])
settings = get_settings()
templates = Jinja2Templates(directory=str(settings.templates_dir))


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def courses_page(
    request: Request,
    subject: str = Query(default=""),
    keyword: str = Query(default=""),
    term: str = Query(default="1252"),
    page: int = Query(default=1),
):
    """Render the course browser page."""
    courses = []
    total_count = 0
    error_message = None
    
    # Only search if we have some filter
    if subject or keyword:
        try:
            sis_service = SISService()
            response = sis_service.search_courses_sync(
                subject=subject if subject else None,
                keyword=keyword if keyword else None,
                term=term,
                page=page,
            )
            
            # Handle both list and dict response formats
            courses = sis_service._get_classes_list(response)
            total_count = len(courses)
            
        except Exception as e:
            error_message = f"Error searching courses: {str(e)}"
    
    return templates.TemplateResponse(
        "courses.html",
        {
            "request": request,
            "courses": courses,
            "subject": subject,
            "keyword": keyword,
            "term": term,
            "page": page,
            "total_count": total_count,
            "error_message": error_message,
            "title": "Courses - UVA Course Assistant",
            "subjects": get_common_subjects(),
        }
    )


@router.post("/search", response_class=HTMLResponse)
async def search_courses(
    subject: str = Form(default=""),
    keyword: str = Form(default=""),
    term: str = Form(default="1252"),
):
    """Handle course search form submission."""
    params = []
    if subject:
        params.append(f"subject={subject}")
    if keyword:
        params.append(f"keyword={keyword}")
    if term:
        params.append(f"term={term}")
    
    query_string = "&".join(params)
    
    return RedirectResponse(
        url=f"/courses?{query_string}",
        status_code=303,
    )


def get_common_subjects() -> list[dict]:
    """Get list of common subject codes."""
    return [
        {"code": "CS", "name": "Computer Science"},
        {"code": "DSA", "name": "Data Science"},
        {"code": "MATH", "name": "Mathematics"},
        {"code": "STAT", "name": "Statistics"},
        {"code": "STS", "name": "Science, Technology & Society"},
        {"code": "ENGR", "name": "Engineering"},
        {"code": "APMA", "name": "Applied Mathematics"},
        {"code": "ECE", "name": "Electrical & Computer Engineering"},
        {"code": "PHYS", "name": "Physics"},
        {"code": "ECON", "name": "Economics"},
    ]

