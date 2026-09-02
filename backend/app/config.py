"""Environment configuration. Secrets stay server-side."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = BACKEND_ROOT / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_ROOT.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    demo_mode: bool = Field(default=True, alias="DEMO_MODE")
    frontend_origin: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        alias="FRONTEND_ORIGIN",
    )
    perfect_corp_api_key: str | None = Field(default=None, alias="PERFECT_CORP_API_KEY")
    perfect_corp_base_url: str = Field(
        default="https://yce-api-01.makeupar.com",
        alias="PERFECT_CORP_BASE_URL",
    )
    # Official Perfect Corp path: /s2s/v2.0/task/cloth-v4
    # Insert the documented payload fields in providers/perfect_corp.py.
    perfect_corp_tryon_path: str = Field(
        default="/s2s/v2.0/task/cloth-v4",
        alias="PERFECT_CORP_TRYON_PATH",
    )
    perfect_corp_status_path: str = Field(
        default="/s2s/v2.0/task/cloth-v4/{task_id}",
        alias="PERFECT_CORP_STATUS_PATH",
    )
    perfect_corp_image_generator_path: str = Field(
        default="/s2s/v2.0/task/image-to-image/youcam",
        alias="PERFECT_CORP_IMAGE_GENERATOR_PATH",
    )
    request_timeout_seconds: float = 20.0
    max_retries: int = 2

    @property
    def cors_origins(self) -> list[str]:
        return [part.strip() for part in self.frontend_origin.split(",") if part.strip()]

    @property
    def live_try_on_configured(self) -> bool:
        return bool(self.perfect_corp_api_key and self.perfect_corp_base_url)

    @property
    def scenario_configured(self) -> bool:
        return bool(
            self.perfect_corp_api_key
            and self.perfect_corp_base_url
            and self.perfect_corp_image_generator_path
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
