"""Root-level tests reuse the backend DB fixtures (pgserver + mock ingest)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.tests.conftest import db_url, ingested_db  # noqa: F401  (pytest fixture re-export)
