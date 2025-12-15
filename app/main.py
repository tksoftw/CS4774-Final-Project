"""Main FastAPI application entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.config import get_settings
from app.routers import chat_router, courses_router, schedule_router
from app.data.course_loader import CourseLoader


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup: Initialize data if needed
    print("Starting UVA AI Course Assistant...")
    
    # Check if we have indexed data
    try:
        loader = CourseLoader()
        status = loader.get_status()
        print(f"Indexed courses: {status['indexed_count']}")
    except Exception as e:
        print(f"Could not check index status: {e}")
    
    yield
    
    # Shutdown
    print("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title=settings.app_title,
    description="AI-powered course planning assistant for UVA students",
    version="0.1.0",
    lifespan=lifespan,
)

# Mount static files
static_path = Path(__file__).parent.parent / "static"
static_path.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Setup templates
templates_path = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_path))

# Include routers
app.include_router(chat_router)
app.include_router(courses_router)
app.include_router(schedule_router)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the home page."""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "UVA AI Course Assistant",
        }
    )


@app.get("/admin/index", response_class=HTMLResponse)
async def admin_index(request: Request):
    """Admin page to trigger course indexing."""
    return templates.TemplateResponse(
        "admin_index.html",
        {
            "request": request,
            "title": "Admin - Index Courses",
        }
    )


@app.post("/admin/index/run")
async def run_indexing(request: Request):
    """Run course indexing from SIS API."""
    try:
        loader = CourseLoader()
        count = loader.load_courses(term="1252", force_refresh=True)
        
        return templates.TemplateResponse(
            "admin_index.html",
            {
                "request": request,
                "title": "Admin - Index Courses",
                "success_message": f"Successfully indexed {count} courses!",
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "admin_index.html",
            {
                "request": request,
                "title": "Admin - Index Courses",
                "error_message": f"Error indexing courses: {str(e)}",
            }
        )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "app": settings.app_title}

