from __future__ import annotations

import json
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://analytics:analytics_secret@localhost:5432/analytics_db"
    SYNC_DATABASE_URL: str = "postgresql://analytics:analytics_secret@localhost:5432/analytics_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "super_secret_jwt_key_change_in_production_32chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    ENCRYPTION_KEY: str = "VGhpcyBpcyAzMiBieXRlcyBsb25nISEhISE="
    OPENAI_API_KEY: str = ""
    CORS_ORIGINS: str = '["http://localhost:5173","http://localhost:3000"]'
    MAX_UPLOAD_SIZE_MB: int = 100
    UPLOAD_DIR: str = "/app/uploads"

    @property
    def cors_origins_list(self) -> list[str]:
        try:
            return json.loads(self.CORS_ORIGINS)
        except Exception:
            return ["http://localhost:5173"]

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024


settings = Settings()
