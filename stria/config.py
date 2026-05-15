from __future__ import annotations

import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str = ""
    anthropic_api_key: str = ""

    database_url: str = ""
    sqlite_db_path: str = "stria/data/stria.sqlite3"

    # Pipeline tuning
    min_confidence: float = 0.70
    blur_variance_threshold: float = 80.0
    max_image_size_mb: int = 10

    # Runtime
    port: str = ""
    data_dir: str = "stria/data"

    @property
    def is_production(self) -> bool:
        return bool(self.port)

    @property
    def protocols_path(self) -> str:
        return os.path.join(self.data_dir, "protocols.json")

    @property
    def cassette_profiles_path(self) -> str:
        return os.path.join(self.data_dir, "cassette_profiles.json")

    @property
    def documents_dir(self) -> str:
        return os.path.join(self.data_dir, "documents")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
