from fastapi import FastAPI

from shared.db.base import Base
from shared.db.session import engine
from shared.db import models_project, models_asset  # noqa: F401

from .api.v1 import health, projects, assets


app = FastAPI(title="BDC-AI Backend", version="0.1.0")


@app.on_event("startup")
def on_startup() -> None:
    """Ensure database tables are created on startup."""
    Base.metadata.create_all(bind=engine)


app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["projects"])
app.include_router(assets.router, prefix="/api/v1/assets", tags=["assets"])


@app.get("/")
async def read_root() -> dict:
    return {"status": "ok"}
