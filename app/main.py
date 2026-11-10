
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import engine, get_db

from app.api.v1.router import api_router


# APPLICATION LIFESPAN
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting E-Commerce Management API...")

    yield

    print("Shutting down E-Commerce Management API...")

    engine.dispose()


# CREATE FASTAPI APPLICATION
app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "E-Commerce Management API built using "
        "FastAPI, MySQL, SQLAlchemy, and ZITADEL authentication."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# CORS CONFIGURATION
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# REGISTER API VERSION 1
app.include_router(
    api_router,
    prefix="/api/v1",
)


# ROOT ENDPOINT
@app.get(
    "/",
    tags=["Home"],
)
def home():
    return {
        "application": settings.APP_NAME,
        "message": "Welcome to E-Commerce Management API",
        "version": "1.0.0",
        "status": "Running",
    }


# APPLICATION HEALTH CHECK
@app.get(
    "/health",
    tags=["Health"],
)
def health_check():
    return {
        "status": "Healthy",
        "application": settings.APP_NAME,
    }


# DATABASE HEALTH CHECK
@app.get(
    "/health/database",
    tags=["Health"],
)
def database_health(
    db: Session = Depends(get_db),
):
    try:
        db.execute(text("SELECT 1"))

        return {
            "status": "Healthy",
            "database": "MySQL",
            "connection": "Connected",
        }

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed",
        ) from error
