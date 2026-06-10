"""Central configuration & logging - every knob is a typed env var (12-factor).

No bare os.getenv anywhere else in backend/app (checked in CI).
"""

from __future__ import annotations

import json
import logging
from contextvars import ContextVar

from pydantic_settings import BaseSettings, SettingsConfigDict

# request id flows through logs via a contextvar (set by middleware in main.py)
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://ps:ps@localhost:5432/partselect"  # pragma: allowlist secret

    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o"

    embedding_model: str = "text-embedding-3-small"
    embedding_api_key: str = ""  # falls back to llm_api_key
    embedding_dims: int = 1536

    mock_llm: bool = False  # MOCK_LLM=1 -> scripted client (CI/keyless demo)
    mock_embeddings: bool = False  # MOCK_EMBEDDINGS=1 -> hashed bag-of-words

    log_level: str = "INFO"
    log_format: str = "pretty"  # pretty (dev) | json (containers set this)

    @property
    def effective_embedding_key(self) -> str:
        return self.embedding_api_key or self.llm_api_key


settings = Settings()


class _RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "request_id": getattr(record, "request_id", "-"),
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def setup_logging() -> None:
    handler = logging.StreamHandler()
    handler.addFilter(_RequestIdFilter())
    if settings.log_format == "json":
        handler.setFormatter(_JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)-7s %(name)s [%(request_id)s] %(message)s")
        )
    logging.basicConfig(level=settings.log_level, handlers=[handler], force=True)


setup_logging()
