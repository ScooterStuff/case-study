# 01_data_scraping.md — Scrape a Real Slice of PartSelect

## Objective
Produce three JSON datasets from real partselect.com pages, cached politely:

- `backend/data/parts.json` — 200–400 parts (refrigerator + dishwasher)
- `backend/data/compatibility.json` — (part_number, brand, model_number, description) rows
- `backend/data/repair_guides.json` — 16–30 symptom/repair pages

## Ground truth: page structure (verified against saved real pages, June 2026)

The selectors below were extracted from actual saved PartSelect pages. Build
`scraper/parse.py` against the saved fixtures FIRST (TDD style), then point the
crawler at the live site. Copy the user's three saved HTML files into
`scraper/fixtures/` and write parser unit tests against them.

### A. Part detail page (`https://www.partselect.com/PS{id}-{Brand}-{MPN}-{Name}.htm`)

Schema.org microdata — most reliable extraction path:

| Field | Selector | Example value |
|---|---|---|
| PartSelect number | `[itemprop="productID"]` | `PS3406971` |
| Manufacturer part number | `[itemprop="mpn"]` | `W10195416` |
| Brand | `[itemprop="brand"] [itemprop="name"]` (or `[itemprop="brand"]`) | `Whirlpool` |
| Title | `[itemprop="name"]` (the product-level one) | `Lower Dishrack Wheel W10195416` |
| Price | `[itemprop="price"]` | `$33.69` → store as float `33.69` |
| Availability | `[itemprop="availability"]` | `In Stock` |
| Description | `[itemprop="description"]` | full paragraph |
| Rating | `[itemprop="ratingValue"]`, `[itemprop="reviewCount"]` | may be in meta/content attrs |
| Images | `[itemprop="image"]`, plus CDN URLs matching `partselectcom-*.azurefd.net` | webp/jpg |

Content sections are anchored by element **id** (content is in the anchor's
parent container — use `soup.find(id=X).parent`):

| Section id | What to extract |
|---|---|
| `#ProductDescription` | long description (backup for itemprop) |
| `#Troubleshooting` | three lists in text: "This part fixes the following symptoms: …" (symptom list), "This part works with the following products: …" (appliance types), "Part# X replaces these: …" (superseded part numbers, comma-separated) |
| `#ModelCrossReference` | table rows of Brand / Model Number / Description. **NOTE: paginated — the static HTML contains only the first ~20–100 rows. Scrape what is present; do NOT chase AJAX pagination.** Store what you get; the compatibility tool will report "verified fit" vs "not in our verified list" honestly. |
| `#PartVideos` | YouTube embed/links + video titles |
| `#InstallationInstructions` | customer repair stories: each has story text, author/location, `Difficulty Level:` (e.g. "Very Easy"), `Total Repair Time:` (e.g. "Less than 15 mins"), `Tools:` (e.g. "Screw drivers"), helpful votes. Also page-level "Average Repair Rating: 4.8 / 5.0, 28 reviews". Take top ~5 stories per part. |
| `#QuestionsAndAnswers` | items with id `question-{n}`; question text often contains "For model number {MODEL}" (harvest those model numbers as additional compatibility signals, flagged `source: "qna"`), answer in `.qna__ps-answer__msg`. Take top ~5 per part. |
| `#RelatedParts` | related part links (PS numbers) |

### B. Category/brand listing pages

- Top-level: `https://www.partselect.com/Dishwasher-Parts.htm`, `/Refrigerator-Parts.htm`
- Brand level: `https://www.partselect.com/{Brand}-Dishwasher-Parts.htm` (39 brands
  linked from the top page; same pattern for refrigerator)
- Part cards: `div.nf__part` — each contains an `<a href*="/PS">` detail link,
  price (`.nf__part__left-col__basic-info__price`), stock sticker, image.
- Crawl strategy: harvest "Popular {Appliance} Parts" from the two top-level
  pages + 6–8 major brand pages per appliance (Whirlpool, GE, Frigidaire,
  Samsung, LG, Bosch, KitchenAid, Kenmore) until you have 100–200 unique part
  URLs per appliance.

### C. Repair/symptom pages

- Index: `https://www.partselect.com/Repair/Dishwasher/` and `/Repair/Refrigerator/`
- Each index links symptom pages (e.g. "Ice maker not working", "Not draining",
  "Door won't close" — also visible in part-page Troubleshooting symptom lists).
- For each symptom page extract: symptom title, intro text, ordered list of
  likely causes (each cause has a name + explanatory paragraphs + the part
  type(s) to inspect/replace), and any linked part categories/PS numbers.
- Target: every dishwasher + refrigerator symptom page (~10–15 each).
- These power RAG for `diagnose_issue` — extract clean text, preserve cause order
  (PartSelect orders causes by likelihood; say so in metadata: `rank: 1..n`).

## Implementation tasks

1. `scraper/seeds.py` — seed URL lists and constants (brands, appliance types,
   caps: `MAX_PARTS_PER_APPLIANCE = 200`, `MAX_PAGES = 600`).
2. `scraper/fetch.py` — `get(url)` with: on-disk cache at
   `scraper/data/raw_html/{sha1(url)}.html` (check cache before network),
   2.5s sleep between live requests, browser User-Agent, 3 retries with backoff,
   and a global page counter that hard-stops at `MAX_PAGES`.
3. `scraper/parse.py` — pure functions, each taking HTML and returning dicts:
   `parse_part_page(html) -> Part`, `parse_listing(html) -> list[url]`,
   `parse_repair_page(html) -> RepairGuide`. Pydantic models for `Part`,
   `CompatibilityRow`, `RepairGuide`, `RepairStory`, `QnA`.
4. `tests/test_parse.py` — pytest against the three fixtures. Assert exact known
   values: PS3406971, W10195416, Whirlpool, 33.69, "In Stock", symptom list
   includes "Noisy" and "Leaking", cross-reference includes Kenmore model
   `2213222N414`, replaces-list includes `W10195416V`.
5. `scraper/scrape.py` — CLI orchestrator:
   `python -m scraper.scrape --appliance dishwasher refrigerator --out backend/data/`.
   Pipeline: listings → part URLs → part pages → repair indexes → repair pages →
   write the three JSON files. Log progress every 10 pages.
6. Normalization rules: uppercase part/model numbers and strip whitespace for
   matching, keep display originals; price `$33.69` → `33.69`; dedupe parts by
   PS number; every record carries `source_url` and `scraped_at`.

## Fallback path (if blocked/captcha'd)
Do not fight anti-bot measures. Parse the three fixtures + hand-write ~30
additional realistic parts into `backend/data/parts_seed.json` (clearly marked
synthetic) and proceed. Record in DEVIATIONS.md. The agent architecture, not
crawl volume, is what's evaluated. **Must-have either way:** part `PS11752778`
and model `WDT780SAEM1` (spec examples) and Whirlpool fridge ice-maker parts
must exist in the dataset with correct data from their live pages — fetch at
least those specific pages individually if bulk crawling fails. Verify:
PS11752778 is a Whirlpool dishwasher door balance link kit; WDT780SAEM1 is a
Whirlpool dishwasher model. Confirm against the live pages and ensure the
compatibility table links them (it should — if the scraped cross-reference
slice doesn't include it, fetch the model page
`https://www.partselect.com/Models/WDT780SAEM1/` and harvest its parts list
as additional compatibility rows, `source: "model_page"`).

## Acceptance checks
- [ ] `pytest tests/test_parse.py` green
- [ ] `parts.json` ≥ 150 parts total, both appliances represented
- [ ] Every part has: ps_number, mpn, brand, title, price, availability,
      description, appliance_type, ≥0 symptoms, source_url
- [ ] `compatibility.json` ≥ 1,000 rows; includes (PS11752778, WDT780SAEM1)
- [ ] `repair_guides.json` ≥ 16 guides; includes refrigerator "Ice maker not
      working" and dishwasher "Not draining"
- [ ] Re-running scrape.py makes zero network requests (cache hit)
- [ ] `git commit -m "feat(scraper): polite cached scraper + parsed datasets"`
