from pathlib import Path
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_env: Literal["development", "production"] = "development"
    storage_backend: Literal["sqlite", "supabase"] = "sqlite"
    sqlite_path: Path = Path(".local/black-fire.sqlite3")
    cors_origins: str = "http://127.0.0.1:5173,http://localhost:5173"
    supabase_url: str = ""
    supabase_publishable_key: str = ""

    @model_validator(mode="after")
    def deployment_guard(self):
        if self.app_env == "production" and self.storage_backend != "supabase":
            raise ValueError("Hosted mode requires Supabase; local anonymous SQLite is disabled")
        if self.storage_backend == "supabase" and (
            not self.supabase_url.startswith("https://") or not self.supabase_publishable_key
        ):
            raise ValueError("Supabase HTTPS URL and publishable key are required")
        return self
