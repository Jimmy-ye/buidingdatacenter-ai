import os
from pathlib import Path
import logging

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from shared.db.base import Base
from shared.db.session import engine
from shared.db import models_project, models_asset, models_auth  # noqa: F401

from .api.v1 import health, assets, engineering, projects, auth


logger = logging.getLogger("bdc_ai")

app = FastAPI(title="BDC-AI Backend", version="0.1.0")

# 配置 CORS 中间件 ⭐
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*",  # 开发环境允许所有来源（生产环境应限制具体域名）
    ],
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有 HTTP 方法
    allow_headers=["*"],  # 允许所有请求头
)


@app.on_event("startup")
def on_startup() -> None:
    """Ensure database tables are created on startup."""
    Base.metadata.create_all(bind=engine)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler to log unexpected errors with stack trace."""
    import traceback

    print(f"\n{'='*60}")
    print(f"[SERVER ERROR] {exc.__class__.__name__}: {str(exc)}")
    print(f"[SERVER ERROR] Method: {request.method}")
    print(f"[SERVER ERROR] URL: {request.url}")
    print(f"[SERVER ERROR] Client: {request.client}")
    print(f"[SERVER ERROR] Traceback:")
    traceback.print_exc()
    print(f"{'='*60}\n")

    logger.exception("Unhandled error on %s %s", request.method, request.url)

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_type": exc.__class__.__name__,
            "message": str(exc),
            "path": str(request.url.path),
        },
    )


app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["projects"])
app.include_router(assets.router, prefix="/api/v1/assets", tags=["assets"])
app.include_router(engineering.router, prefix="/api/v1", tags=["engineering"])


@app.get("/")
async def read_root() -> dict:
    return {"status": "ok"}
