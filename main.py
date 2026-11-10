
import os

from dotenv import load_dotenv

# Load environment variables before importing app modules
load_dotenv()

from fastapi import FastAPI

from app.routes import router


app = FastAPI(
    title=os.getenv(
        "APP_NAME",
        "Loan Management API"
    ),
    version="1.0.0",
    description=(
        "Loan Management API integrated "
        "with ZITADEL OAuth2 authentication"
    ),
    swagger_ui_init_oauth={
        "clientId": os.getenv("ZITADEL_CLIENT_ID", ""),
        "usePkceWithAuthorizationCodeGrant": True
    }
)


app.include_router(router)


@app.get("/")
async def root():

    return {
        "application": "Loan Management API",
        "status": "running",
        "authentication": "ZITADEL OAuth2"
    }


@app.get("/health")
async def health_check():

    return {
        "status": "healthy"
    }
