"""Polite, cached HTTP fetcher.

Every fetched page is cached on disk; a URL is never fetched twice across
runs. Live requests are throttled and hard-capped (CONTEXT.md §8).
"""
from __future__ import annotations

import hashlib
import logging
import time
from pathlib import Path

import httpx

from scraper.seeds import MAX_PAGES, REQUEST_DELAY_SECONDS, USER_AGENT

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).parent / "data" / "raw_html"

class PageBudgetExceeded(RuntimeError):
    """Raised when the global MAX_PAGES crawl budget is exhausted."""

class Fetcher:
    def __init__(self, cache_dir: Path = CACHE_DIR, delay: float = REQUEST_DELAY_SECONDS,
                 max_pages: int = MAX_PAGES) -> None:
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.delay = delay
        self.max_pages = max_pages
        self.live_requests = 0
        self._client = httpx.Client(
            headers={"User-Agent": USER_AGENT}, follow_redirects=True, timeout=30,
            trust_env=False,  # NOTE: ignore env proxies; sandbox sets a SOCKS proxy httpx cannot use
        )

    def _cache_path(self, url: str) -> Path:
        return self.cache_dir / f"{hashlib.sha1(url.encode()).hexdigest()}.html"

    def get(self, url: str) -> str:
        """Return page HTML, from cache when available (zero network on re-run)."""
        path = self._cache_path(url)
        if path.exists():
            logger.debug("cache hit: %s", url)
            return path.read_text(encoding="utf-8")
        if self.live_requests >= self.max_pages:
            raise PageBudgetExceeded(f"crawl budget of {self.max_pages} pages spent")
        html = self._fetch_live(url)
        path.write_text(html, encoding="utf-8")
        return html

    def _fetch_live(self, url: str, retries: int = 3) -> str:
        backoff = 5.0
        for attempt in range(1, retries + 1):
            time.sleep(self.delay)  # politeness delay before every live request
            self.live_requests += 1
            try:
                resp = self._client.get(url)
                resp.raise_for_status()
                return resp.text
            except httpx.HTTPError as exc:
                logger.warning("fetch failed (%s/%s) %s: %s", attempt, retries, url, exc)
                if attempt == retries:
                    raise
                time.sleep(backoff)
                backoff *= 2
        raise AssertionError("unreachable")
