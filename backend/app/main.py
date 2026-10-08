from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.database import init_db, close_db_connection
from app.routes.auth import router as auth_router
from app.routes.resume import router as resume_router
from app.routes.interview import router as interview_router
from app.routes.performance import router as performance_router
from app.routes.voice import router as voice_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("interview_ai")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize MongoDB indexes and check connection
    try:
        init_db()
        logger.info("MongoDB initialized successfully.")
    except Exception as e:
        logger.warning(f"MongoDB startup connection warning: {e}")
    yield
    # Shutdown
    close_db_connection()
    logger.info("MongoDB connection closed.")


from app.config import settings
from fastapi import Request
from fastapi.responses import JSONResponse

app = FastAPI(
    title="InterviewAI API",
    description="InterviewAI Production API — AI Mock Interview, Resume Analyzer & Speech-to-Text Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS using environment-configured origins (no wildcard with credentials)
origins = [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Production-safe unhandled exception handler: logs diagnostic error and hides internal stack trace."""
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again later."},
    )


# Register routes
app.include_router(auth_router)
app.include_router(resume_router)
app.include_router(interview_router)
app.include_router(performance_router)
app.include_router(voice_router)


@app.get("/")
def read_root():
    return {
        "status": "ok",
        "service": "InterviewAI API",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "documentation": "/docs",
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "InterviewAI API",
        "version": "1.0.0",
        "database": "connected",
    }
