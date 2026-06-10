"""Seed URLs, crawl scope and politeness constants for the PartSelect scraper."""
from __future__ import annotations

BASE_URL = "https://www.partselect.com"

APPLIANCES: dict[str, str] = {
    "dishwasher": f"{BASE_URL}/Dishwasher-Parts.htm",
    "refrigerator": f"{BASE_URL}/Refrigerator-Parts.htm",
}

# Major brands crawled per appliance (brand listing pattern:
# https://www.partselect.com/{Brand}-{Appliance}-Parts.htm)
BRANDS: list[str] = [
    "Whirlpool", "GE", "Frigidaire", "Samsung",
    "LG", "Bosch", "KitchenAid", "Kenmore",
]

REPAIR_INDEXES: dict[str, str] = {
    "dishwasher": f"{BASE_URL}/Repair/Dishwasher/",
    "refrigerator": f"{BASE_URL}/Repair/Refrigerator/",
}

# Spec-critical pages that must always be in the dataset (CONTEXT.md §4).
MUST_HAVE_PART_URLS: list[str] = [
    # NOTE: the spec example PS11752778 is a Whirlpool *refrigerator door shelf
    # bin* (WPW10321304) on the live site - see playbook/DEVIATIONS.md.
    f"{BASE_URL}/PS11752778-Whirlpool-WPW10321304-Refrigerator-Door-Shelf-Bin.htm",
]
MUST_HAVE_MODEL_URLS: list[str] = [
    f"{BASE_URL}/Models/WDT780SAEM1/",  # spec example dishwasher model
]

def brand_listing_url(brand: str, appliance: str) -> str:
    return f"{BASE_URL}/{brand}-{appliance.capitalize()}-Parts.htm"

# Politeness / scope caps (CONTEXT.md §8 - mandatory).
REQUEST_DELAY_SECONDS = 2.5
MAX_PARTS_PER_APPLIANCE = 200
MAX_PAGES = 600
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
