"""SkyOps Backend FastAPI application entrypoint."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.settings import settings
from app.core.logging import setup_logging
from app.core.exceptions import SkyOpsException
from app.db.session import init_db
from app.api.v1.endpoints import (
    health,
    airports,
    flights,
    predictions,
    gates,
    weather,
    analytics,
)

setup_logging()

# Initialize tables for development and testing environments
try:
    init_db()
except Exception:
    pass

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Centralized exception handler per GEMINI_BACKEND.md Section 34
@app.exception_handler(SkyOpsException)
async def skyops_exception_handler(request: Request, exc: SkyOpsException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.error_code,
                "message": exc.message,
            },
        },
    )


app.include_router(health.router, prefix=f"{settings.API_V1_STR}/health", tags=["Health"])
app.include_router(airports.router, prefix=f"{settings.API_V1_STR}/airports", tags=["Airports"])
app.include_router(flights.router, prefix=f"{settings.API_V1_STR}/flights", tags=["Flights"])
app.include_router(gates.router, prefix=f"{settings.API_V1_STR}/gates", tags=["Gates"])
app.include_router(weather.router, prefix=f"{settings.API_V1_STR}/weather", tags=["Weather"])
app.include_router(predictions.router, prefix=f"{settings.API_V1_STR}/predictions", tags=["Predictions"])
app.include_router(analytics.router, prefix=f"{settings.API_V1_STR}/analytics", tags=["Analytics"])


@app.get("/")
def root():
    return {"message": "Welcome to SkyOps Backend API", "version": settings.VERSION}
