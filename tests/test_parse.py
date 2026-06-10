"""Parser tests.

Two layers:
1. Pure-function unit tests - always run.
2. Fixture tests against saved real PartSelect pages in scraper/fixtures/
   (raw HTML, supplied by the candidate) and scraper/fixtures/extractions/
   (text extractions captured during the AI-native build).
HTML fixture tests are skipped with a loud reason until the files exist.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scraper import extract_text
from scraper.parse import (
    MODEL_IN_TEXT_RE,
    _availability,
    norm_number,
    parse_cross_reference,
    parse_part_page,
    parse_price,
)

FIXTURES = Path(__file__).parent.parent / "scraper" / "fixtures"
PART_FIXTURE = next(iter(FIXTURES.glob("*PS3406971*.htm*")), None)
EXTRACTION = FIXTURES / "extractions" / "PS11752778.txt"

# ------------------------------------------------------------- pure functions


def test_parse_price() -> None:
    assert parse_price("$33.69") == 33.69
    assert parse_price("1,049.00") == 1049.0
    assert parse_price("no price") is None


def test_norm_number() -> None:
    assert norm_number(" w10195416v ") == "W10195416V"
    assert norm_number("#WDT780SAEM1") == "WDT780SAEM1"


def test_model_number_harvest() -> None:
    text = "For model number WDT780SAEM1\nthanks! for model number: ed5fvgxws01"
    assert MODEL_IN_TEXT_RE.findall(text) == ["WDT780SAEM1", "ed5fvgxws01"]


def test_availability_mapping() -> None:
    assert _availability("http://schema.org/InStock") == "In Stock"
    assert _availability("In Stock") == "In Stock"


# ------------------------------------------- text-extraction fixture (real data)


@pytest.mark.skipif(not EXTRACTION.exists(), reason="extraction fixture missing")
def test_extraction_part_page() -> None:
    text = EXTRACTION.read_text(encoding="utf-8")
    kind, url = extract_text.detect(text)
    assert kind == "part" and "PS11752778" in url
    part, rows = extract_text.parse_part_extraction(text, url)
    assert part.ps_number == "PS11752778"
    assert part.mpn == "WPW10321304"
    assert part.brand == "Whirlpool"
    assert part.price == 47.40
    assert part.availability == "In Stock"
    assert part.appliance_type == "refrigerator"
    assert "Leaking" in part.symptoms
    assert "AP6019471" in part.replaces
    models = {r.model_number for r in rows}
    assert "10640262010" in models  # Kenmore row from the cross-reference


# ------------------------------------------------- raw HTML fixtures (playbook 01)

needs_html = pytest.mark.skipif(
    PART_FIXTURE is None,
    reason="saved PartSelect HTML pages not yet in scraper/fixtures/ - "
    "drop the saved part page (PS3406971) there to enable",
)


@needs_html
def test_part_page_fixture() -> None:
    html = PART_FIXTURE.read_text(encoding="utf-8", errors="replace")
    part = parse_part_page(html, source_url=str(PART_FIXTURE))
    assert part.ps_number == "PS3406971"
    assert part.mpn == "W10195416"
    assert part.brand == "Whirlpool"
    assert part.price is not None and part.price > 0
    assert part.availability == "In Stock"
    assert "Noisy" in part.symptoms and "Leaking" in part.symptoms
    assert "W10195416V" in part.replaces


@needs_html
def test_cross_reference_fixture() -> None:
    html = PART_FIXTURE.read_text(encoding="utf-8", errors="replace")
    rows = parse_cross_reference(html, source_url=str(PART_FIXTURE))
    assert rows, "expected cross-reference rows in the static HTML"
    models = {r.model_number for r in rows}
    assert "2213222N414" in models  # Kenmore model from playbook 01


# ---------------------------------------------------------------- fetch cache


def test_fetcher_cache_hits_disk_not_network(tmp_path, monkeypatch) -> None:
    """Re-running against a warm cache makes zero live requests (01 acceptance)."""
    from scraper.fetch import Fetcher

    calls = {"live": 0}
    f = Fetcher(cache_dir=tmp_path, delay=0)

    def fake_live(url: str, retries: int = 3) -> str:
        calls["live"] += 1
        return "<html>cached!</html>"

    monkeypatch.setattr(f, "_fetch_live", fake_live)
    assert f.get("https://example.com/page") == "<html>cached!</html>"
    assert f.get("https://example.com/page") == "<html>cached!</html>"
    assert calls["live"] == 1

    f2 = Fetcher(cache_dir=tmp_path, delay=0)
    monkeypatch.setattr(f2, "_fetch_live", fake_live)
    assert f2.get("https://example.com/page") == "<html>cached!</html>"
    assert calls["live"] == 1


def test_fetcher_page_budget(tmp_path, monkeypatch) -> None:
    import pytest as _pytest

    from scraper.fetch import Fetcher, PageBudgetExceeded

    f = Fetcher(cache_dir=tmp_path, delay=0, max_pages=1)
    monkeypatch.setattr(f, "_fetch_live", lambda url, retries=3: (_ for _ in ()).throw(AssertionError))
    f.live_requests = 1
    with _pytest.raises(PageBudgetExceeded):
        f.get("https://example.com/over-budget")
