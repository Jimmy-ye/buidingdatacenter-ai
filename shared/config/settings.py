import os
from functools import lru_cache


class Settings:
    def __init__(self) -> None:
        self.database_url = os.getenv(
            "BDC_DATABASE_URL",
            "postgresql://admin:password@localhost:5432/bdc_ai",
        )
        self.minio_endpoint = os.getenv("BDC_MINIO_ENDPOINT", "localhost:9000")


@lru_cache()
def get_settings() -> Settings:
    return Settings()
