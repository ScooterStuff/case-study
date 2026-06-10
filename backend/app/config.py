"""Central configuration - every knob is an env var (12-factor)."""
from __future__ import annotations

import logging

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://ps:ps@localhost:5432/partselect"

    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o"

    embedding_model: str = "text-embedding-3-small"
    embedding_api_key: str = ""          # falls back to llm_api_key
    embedding_dims: int = 1536

    mock_llm: bool = False               # MOCK_LLM=1 -> scripted client (CI/demo)
    mock_embeddings: bool = False        # MOCK_EMBEDDINGS=1 -> hashed bag-of-words

    log_level: str = "INFO"

    @property
    def effective_embedding_key(self) -> str:
        return self.embedding_api_key or self.llm_api_key


settings = Settings()

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
