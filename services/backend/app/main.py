import os
from pathlib import Path
import logging

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from shared.db.base import Base
from shared.db.session import engine
from shared.db import models_project, models_asset  # noqa: F401

from .api.v1 import health, projects, assets


logger = logging.getLogger("bdc_ai")

app = FastAPI(title="BDC-AI Backend", version="0.1.0")


@app.on_event("startup")
def on_startup() -> None:
    """Ensure database tables are created on startup."""
    Base.metadata.create_all(bind=engine)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler to log unexpected errors with stack trace."""
    logger.exception("Unhandled error on %s %s", request.method, request.url)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_type": exc.__class__.__name__,
            "message": str(exc),
        },
    )


app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["projects"])
app.include_router(assets.router, prefix="/api/v1/assets", tags=["assets"])


@app.get("/")
async def read_root() -> dict:
    return {"status": "ok"}
