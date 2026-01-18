import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv(Path(__file__).parent.parent.parent / ".env")


class Settings:
    def __init__(self) -> None:
        self.database_url = os.getenv(
            "BDC_DATABASE_URL",
            "postgresql://admin:password@localhost:5432/bdc_ai",
        )
        self.minio_endpoint = os.getenv("BDC_MINIO_ENDPOINT", "localhost:9000")
        self.local_storage_dir = os.getenv("BDC_LOCAL_STORAGE_DIR", "data/assets")


@lru_cache()
def get_settings() -> Settings:
    return Settings()
