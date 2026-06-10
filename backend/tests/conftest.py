"""Test bootstrap: ephemeral Postgres (pgserver) + mock embeddings + ingest."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

# Set BEFORE any backend import that test modules might do at collection time.
os.environ.setdefault("MOCK_LLM", "1")
os.environ.setdefault("MOCK_EMBEDDINGS", "1")


@pytest.fixture(scope="session")
def db_url(tmp_path_factory) -> str:
    if os.environ.get("DATABASE_URL"):  # CI provides a real postgres
        return os.environ["DATABASE_URL"]
    pgserver = pytest.importorskip("pgserver", reason="pgserver not installed (CI uses docker postgres)")
    server = pgserver.get_server(str(tmp_path_factory.mktemp("pg")))
    return server.get_uri()


@pytest.fixture(scope="session", autouse=True)
def ingested_db(db_url: str):
    os.environ["DATABASE_URL"] = db_url
    os.environ["MOCK_EMBEDDINGS"] = "1"
    os.environ["MOCK_LLM"] = "1"
    from backend.app import config

    config.settings = config.Settings()  # re-read env
    import psycopg

    from backend import ingest

    with psycopg.connect(db_url, autocommit=False) as conn:
        ingest.rebuild(conn)
    yield db_url
