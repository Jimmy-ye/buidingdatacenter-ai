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

        # 本地存储目录：将相对路径转换为绝对路径
        local_storage = os.getenv("BDC_LOCAL_STORAGE_DIR", "data/assets")
        if not os.path.isabs(local_storage):
            # 获取项目根目录（shared/config/settings.py 的上三级）
            project_root = Path(__file__).resolve().parent.parent.parent
            local_storage = str(project_root / local_storage)
        self.local_storage_dir = local_storage

        # JWT 配置
        self.jwt_secret_key = os.getenv(
            "BDC_JWT_SECRET_KEY",
            "your-secret-key-please-change-in-production-use-openssl-rand-hex-32"
        )
        self.access_token_expire_minutes = int(
            os.getenv("BDC_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
        )
        self.refresh_token_expire_days = int(
            os.getenv("BDC_REFRESH_TOKEN_EXPIRE_DAYS", "7")
        )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
