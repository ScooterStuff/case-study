"""CLI crawl orchestrator.

    python -m scraper.scrape --appliance dishwasher refrigerator --out backend/data/

Pipeline: listings -> part URLs -> part pages -> repair indexes -> repair pages
-> write parts.json / compatibility.json / repair_guides.json. All fetches go
through the polite on-disk cache (re-runs make zero network requests).
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from scraper.fetch import Fetcher, PageBudgetExceeded
from scraper.parse import (
    Part,
    parse_cross_reference,
    parse_listing,
    parse_model_page,
    parse_part_page,
    parse_repair_index,
    parse_repair_page,
)
from scraper.seeds import (
    APPLIANCES,
    BRANDS,
    MAX_PARTS_PER_APPLIANCE,
    MUST_HAVE_MODEL_URLS,
    MUST_HAVE_PART_URLS,
    REPAIR_INDEXES,
    brand_listing_url,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("scrape")


def collect_part_urls(fetcher: Fetcher, appliance: str) -> list[str]:
    urls: list[str] = parse_listing(fetcher.get(APPLIANCES[appliance]))
    for brand in BRANDS:
        if len(urls) >= MAX_PARTS_PER_APPLIANCE:
            break
        try:
            urls += parse_listing(fetcher.get(brand_listing_url(brand, appliance)))
        except Exception as exc:  # noqa: BLE001 - a missing brand page is not fatal
            logger.warning("listing failed for %s/%s: %s", brand, appliance, exc)
        urls = list(dict.fromkeys(urls))
    return urls[:MAX_PARTS_PER_APPLIANCE]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--appliance", nargs="+", default=list(APPLIANCES), choices=list(APPLIANCES))
    ap.add_argument("--out", type=Path, default=Path("backend/data"))
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    fetcher = Fetcher()
    parts: dict[str, Part] = {}
    compat_rows: list[dict] = []
    guides: list[dict] = []

    try:
        for appliance in args.appliance:
            part_urls = collect_part_urls(fetcher, appliance)
            logger.info("%s: %d part urls", appliance, len(part_urls))
            for i, url in enumerate(dict.fromkeys(part_urls + MUST_HAVE_PART_URLS)):
                html = fetcher.get(url)
                part = parse_part_page(html, source_url=url)
                if part.ps_number and part.ps_number not in parts:
                    if not part.appliance_type:
                        part.appliance_type = appliance
                    parts[part.ps_number] = part
                    compat_rows += [r.model_dump() for r in parse_cross_reference(html, url)]
                    for qna in part.qna:  # Q&A model numbers, flagged source=qna
                        for model in qna.model_numbers:
                            compat_rows.append(
                                {
                                    "ps_number": part.ps_number,
                                    "brand": part.brand,
                                    "model_number": model,
                                    "description": "",
                                    "source": "qna",
                                    "source_url": url,
                                }
                            )
                if (i + 1) % 10 == 0:
                    logger.info("%s: %d/%d part pages", appliance, i + 1, len(part_urls))
            for url in parse_repair_index(fetcher.get(REPAIR_INDEXES[appliance])):
                guides.append(parse_repair_page(fetcher.get(url), appliance, url).model_dump())
        for url in MUST_HAVE_MODEL_URLS:
            compat_rows += [r.model_dump() for r in parse_model_page(fetcher.get(url), url)]
    except PageBudgetExceeded as exc:
        logger.warning("stopping early: %s", exc)

    # dedupe compatibility on (ps, model)
    seen: set[tuple[str, str]] = set()
    deduped = []
    for row in compat_rows:
        key = (row["ps_number"], row["model_number"])
        if key not in seen and row["model_number"]:
            seen.add(key)
            deduped.append(row)

    (args.out / "parts.json").write_text(
        json.dumps([p.model_dump() for p in parts.values()], indent=1), encoding="utf-8"
    )
    (args.out / "compatibility.json").write_text(json.dumps(deduped, indent=1), encoding="utf-8")
    (args.out / "repair_guides.json").write_text(json.dumps(guides, indent=1), encoding="utf-8")
    logger.info(
        "wrote %d parts, %d compat rows, %d guides (live requests: %d)",
        len(parts),
        len(deduped),
        len(guides),
        fetcher.live_requests,
    )


if __name__ == "__main__":
    main()
