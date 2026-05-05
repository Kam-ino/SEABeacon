from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


PACKAGE_ROOT = Path(__file__).resolve().parent
FIXTURES_DIR = PACKAGE_ROOT / "fixtures"
REPO_ROOT = PACKAGE_ROOT.parent.parent


def _is_serverless() -> bool:
    """Detect environments with a read-only working directory.

    Vercel sets VERCEL=1; AWS Lambda sets AWS_LAMBDA_FUNCTION_NAME.
    """
    return bool(os.getenv("VERCEL")) or bool(os.getenv("AWS_LAMBDA_FUNCTION_NAME"))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[".env", str(REPO_ROOT / ".env")],
        env_file_encoding="utf-8",
        extra="ignore",
    )

    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    database_url: str = Field(default="sqlite:///./seabeacon.db", alias="DATABASE_URL")
    api_base_url: str = Field(default="http://localhost:8000", alias="API_BASE_URL")

    @model_validator(mode="after")
    def _redirect_sqlite_to_tmp_on_serverless(self) -> "Settings":
        # On Vercel/Lambda the working dir is read-only — only /tmp is writable.
        # If the configured DB is the default relative SQLite, rewrite it.
        if _is_serverless() and self.database_url == "sqlite:///./seabeacon.db":
            self.database_url = "sqlite:////tmp/seabeacon.db"
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
