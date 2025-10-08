from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import settings
from app.api.routers import users, assessments, auth, admin, coach, weeks, daily_lessons, assessment_results, user_journeys, user_lessons, user_progress, user_preferences
from app.utils.response import APIException, api_exception_handler
from app.core.scheduler import start_scheduler, stop_scheduler

# Import models to ensure they are registered with SQLAlchemy
from app.models import User, Assessment, AssessmentResult, UserJourney, UserLesson, UserProgress
from app.models.week import Week
from app.models.daily_lesson import DailyLesson

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    version="1.0.0",
    description="A modern FastAPI backend with comprehensive features",
)

# Start background scheduler
@app.on_event("startup")
async def startup_event():
    """Start background jobs on application startup"""
    start_scheduler()

@app.on_event("shutdown")
async def shutdown_event():
    """Stop background jobs on application shutdown"""
    stop_scheduler()

# Register custom exception handler
app.add_exception_handler(APIException, api_exception_handler)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Set up trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS,
)

# Include API routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["authentication"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
# app.include_router(items.router, prefix=f"{settings.API_V1_STR}/items", tags=["items"])
app.include_router(assessments.router, prefix=f"{settings.API_V1_STR}/assessments", tags=["assessments"])
app.include_router(assessment_results.router, prefix=f"{settings.API_V1_STR}", tags=["assessment-results"])
app.include_router(weeks.router, prefix=f"{settings.API_V1_STR}/weeks", tags=["weeks"])
app.include_router(daily_lessons.router, prefix=f"{settings.API_V1_STR}/daily-lessons", tags=["daily-lessons"])
app.include_router(admin.router, prefix=f"{settings.API_V1_STR}/admin", tags=["admin"])
app.include_router(coach.router, prefix=f"{settings.API_V1_STR}/coach", tags=["coach"])

# User Journey System routers
app.include_router(user_journeys.router, prefix=f"{settings.API_V1_STR}", tags=["user-journeys"])
app.include_router(user_lessons.router, prefix=f"{settings.API_V1_STR}", tags=["user-lessons"])
app.include_router(user_progress.router, prefix=f"{settings.API_V1_STR}", tags=["user-progress"])
app.include_router(user_preferences.router, prefix=f"{settings.API_V1_STR}", tags=["user-preferences"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to FastAPI Backend", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
