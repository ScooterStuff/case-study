"""Pure HTML -> structured-data parsers for PartSelect pages.

Selectors follow playbook/01_data_scraping.md, verified against saved real
pages (scraper/fixtures/). Each parser takes raw HTML and returns pydantic
models - no I/O here, which keeps everything unit-testable.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Tag
from pydantic import BaseModel, Field

from scraper.seeds import BASE_URL

# --------------------------------------------------------------------------- models

class RepairStory(BaseModel):
    title: str = ""
    text: str
    author: str = ""
    difficulty: str = ""
    repair_time: str = ""
    tools: str = ""
    helpful_votes: int = 0

class QnA(BaseModel):
    question: str
    answer: str = ""
    model_numbers: list[str] = Field(default_factory=list)

class Part(BaseModel):
    ps_number: str                      # normalized, e.g. "PS3406971"
    mpn: str                            # manufacturer part number, e.g. "W10195416"
    brand: str = ""
    title: str = ""
    price: float | None = None
    availability: str = ""
    description: str = ""
    appliance_type: str = ""            # "dishwasher" | "refrigerator"
    symptoms: list[str] = Field(default_factory=list)
    works_with: list[str] = Field(default_factory=list)
    replaces: list[str] = Field(default_factory=list)
    rating: float | None = None
    review_count: int | None = None
    install_difficulty: str = ""
    install_time: str = ""
    images: list[str] = Field(default_factory=list)
    videos: list[dict] = Field(default_factory=list)
    repair_stories: list[RepairStory] = Field(default_factory=list)
    qna: list[QnA] = Field(default_factory=list)
    related_parts: list[str] = Field(default_factory=list)
    source_url: str = ""
    scraped_at: str = ""

class CompatibilityRow(BaseModel):
    ps_number: str
    brand: str = ""
    model_number: str                   # normalized (uppercase, stripped)
    description: str = ""
    source: str = "crossref"            # crossref | qna | model_page
    source_url: str = ""

class RepairCause(BaseModel):
    rank: int                           # PartSelect orders causes by likelihood
    name: str
    text: str
    part_links: list[str] = Field(default_factory=list)

class RepairGuide(BaseModel):
    appliance: str
    symptom: str
    slug: str = ""
    intro: str = ""
    percent_reported: int | None = None
    difficulty: str = ""
    repair_story_count: int | None = None
    video_count: int | None = None
    causes: list[RepairCause] = Field(default_factory=list)
    detail_level: str = "full"          # full | summary (see DEVIATIONS.md)
    source_url: str = ""
    scraped_at: str = ""

# ----------------------------------------------------------------- normalization

PS_RE = re.compile(r"PS\d{5,9}")
MODEL_IN_TEXT_RE = re.compile(r"[Ff]or model number[:\s#]*([A-Za-z0-9][A-Za-z0-9\-/#]{3,})")

def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def norm_number(value: str) -> str:
    """Normalize part/model numbers for matching: uppercase, strip separators."""
    return re.sub(r"\s+", "", value).strip().upper().strip("#")

def parse_price(value: str) -> float | None:
    m = re.search(r"([0-9][0-9,]*\.?[0-9]*)", value.replace("$", ""))
    return float(m.group(1).replace(",", "")) if m else None

def _txt(node: Tag | None) -> str:
    if node is None:
        return ""
    if node.name == "meta":
        return (node.get("content") or "").strip()
    return node.get_text(" ", strip=True)

def _itemprop(soup: BeautifulSoup, name: str) -> str:
    node = soup.select_one(f'[itemprop="{name}"]')
    if node is None:
        return ""
    content = node.get("content")
    return content.strip() if content else _txt(node)

def _section(soup: BeautifulSoup, anchor_id: str) -> Tag | None:
    """Content sections are anchored by element id; content sits in the parent."""
    anchor = soup.find(id=anchor_id)
    return anchor.parent if anchor is not None else None

# ------------------------------------------------------------------- part pages

def parse_part_page(html: str, source_url: str = "") -> Part:
    soup = BeautifulSoup(html, "lxml")

    ps_number = norm_number(_itemprop(soup, "productID"))
    mpn = norm_number(_itemprop(soup, "mpn"))
    brand_node = soup.select_one('[itemprop="brand"] [itemprop="name"]') or \
        soup.select_one('[itemprop="brand"]')
    brand = _txt(brand_node)

    title = _itemprop(soup, "name")
    price = parse_price(_itemprop(soup, "price"))
    availability = _availability(_itemprop(soup, "availability"))
    description = _itemprop(soup, "description")
    if not description:
        description = _txt(_section(soup, "ProductDescription"))

    rating = None
    if (raw := _itemprop(soup, "ratingValue")):
        try:
            rating = float(raw)
        except ValueError:
            pass
    review_count = None
    if (raw := _itemprop(soup, "reviewCount")) and raw.isdigit():
        review_count = int(raw)

    symptoms, works_with, replaces = _parse_troubleshooting(_section(soup, "Troubleshooting"))
    appliance_type = _infer_appliance(works_with, title, source_url)

    part = Part(
        ps_number=ps_number, mpn=mpn, brand=brand, title=title, price=price,
        availability=availability, description=description,
        appliance_type=appliance_type, symptoms=symptoms, works_with=works_with,
        replaces=replaces, rating=rating, review_count=review_count,
        images=_parse_images(soup), videos=_parse_videos(_section(soup, "PartVideos")),
        repair_stories=_parse_stories(_section(soup, "InstallationInstructions")),
        qna=_parse_qna(_section(soup, "QuestionsAndAnswers")),
        related_parts=_parse_related(_section(soup, "RelatedParts")),
        source_url=source_url, scraped_at=now_iso(),
    )
    return part

def _availability(raw: str) -> str:
    raw = raw.strip()
    if "/" in raw:                      # schema.org URL form
        raw = raw.rsplit("/", 1)[-1]
    mapping = {"InStock": "In Stock", "OutOfStock": "Out of Stock"}
    return mapping.get(raw, raw)

def _infer_appliance(works_with: list[str], title: str, url: str) -> str:
    haystack = " ".join(works_with + [title, url]).lower()
    for kind in ("dishwasher", "refrigerator"):
        if kind in haystack:
            return kind
    return ""

def _parse_troubleshooting(section: Tag | None) -> tuple[list[str], list[str], list[str]]:
    if section is None:
        return [], [], []
    text = section.get_text("\n", strip=True)

    def block_after(marker: str) -> str:
        idx = text.lower().find(marker.lower())
        if idx == -1:
            return ""
        rest = text[idx + len(marker):]
        for stop in ("This part works with", "replaces these", "Back to Top"):
            cut = rest.lower().find(stop.lower())
            if cut > 0:
                rest = rest[:cut]
        return rest.strip(" :\n")

    symptoms = [s.strip() for s in block_after("fixes the following symptoms").split("\n") if s.strip()]
    works = [s.strip() for s in block_after("works with the following products").split("\n") if s.strip()]
    repl_m = re.search(r"replaces these[:\s]*\n?(.+?)(?:\n\n|$)", text, re.S | re.I)
    replaces = []
    if repl_m:
        replaces = [norm_number(x) for x in repl_m.group(1).split(",") if x.strip()]
    return symptoms, works, replaces

def _parse_images(soup: BeautifulSoup) -> list[str]:
    urls: list[str] = []
    for node in soup.select('[itemprop="image"]'):
        src = node.get("content") or node.get("src") or ""
        if src:
            urls.append(urljoin(BASE_URL, src))
    for img in soup.find_all("img", src=re.compile(r"partselectcom-.*\.azurefd\.net")):
        urls.append(img["src"])
    return list(dict.fromkeys(urls))

def _parse_videos(section: Tag | None) -> list[dict]:
    if section is None:
        return []
    videos = []
    for node in section.find_all(["iframe", "a"], src=True) + section.find_all("a", href=True):
        url = node.get("src") or node.get("href") or ""
        if "youtube" in url or "youtu.be" in url:
            videos.append({"url": url, "title": _txt(node) or node.get("title", "")})
    for node in section.find_all(attrs={"data-yt-init": True}):
        videos.append({"url": f"https://www.youtube.com/watch?v={node['data-yt-init']}",
                       "title": node.get("title", "")})
    return list({v["url"]: v for v in videos}.values())

_LABEL_RE = re.compile(r"Difficulty Level:\s*(?P<difficulty>.+?)\s*Total Repair Time:\s*(?P<time>.+?)(?:\s*Tools:\s*(?P<tools>.+?))?$", re.S)

def _parse_stories(section: Tag | None, limit: int = 5) -> list[RepairStory]:
    if section is None:
        return []
    stories: list[RepairStory] = []
    for label in section.find_all(string=re.compile(r"Difficulty Level:")):
        container = label.find_parent("div")
        for _ in range(4):              # walk up to the story card container
            if container is None:
                break
            text = container.get_text("\n", strip=True)
            if "Total Repair Time" in text:
                break
            container = container.find_parent("div")
        if container is None:
            continue
        text = container.get_text("\n", strip=True)
        m = _LABEL_RE.search(text.replace("\n", " "))
        body = text.split("Difficulty Level:")[0].strip()
        votes_m = re.search(r"(\d+) of \d+ people found this instruction helpful", text)
        author_m = re.search(r"^[-•]?\s*(.+?) from (.+?)$", text, re.M)
        story = RepairStory(
            text=body[:2000],
            author=(author_m.group(0).strip("- ") if author_m else ""),
            difficulty=(m.group("difficulty").strip() if m else ""),
            repair_time=(m.group("time").strip() if m else ""),
            tools=(m.group("tools") or "").strip() if m else "",
            helpful_votes=int(votes_m.group(1)) if votes_m else 0,
        )
        if story.text and story not in stories:
            stories.append(story)
        if len(stories) >= limit:
            break
    return stories

def _parse_qna(section: Tag | None, limit: int = 5) -> list[QnA]:
    if section is None:
        return []
    items: list[QnA] = []
    for q_div in section.find_all(id=re.compile(r"^question-\d+")):
        text = q_div.get_text("\n", strip=True)
        answer = _txt(q_div.select_one(".qna__ps-answer__msg"))
        question = text.split(answer)[0] if answer and answer in text else text
        items.append(QnA(
            question=question[:1500],
            answer=answer[:1500],
            model_numbers=[norm_number(m) for m in MODEL_IN_TEXT_RE.findall(text)],
        ))
        if len(items) >= limit:
            break
    return items

def _parse_related(section: Tag | None) -> list[str]:
    if section is None:
        return []
    found = []
    for a in section.find_all("a", href=re.compile(r"/PS\d+")):
        m = PS_RE.search(a["href"])
        if m:
            found.append(m.group(0))
    return list(dict.fromkeys(found))

def parse_cross_reference(html: str, source_url: str = "") -> list[CompatibilityRow]:
    """#ModelCrossReference rows. The static HTML only contains the first page
    of rows - scrape what is present, do NOT chase AJAX pagination (01 doc)."""
    soup = BeautifulSoup(html, "lxml")
    ps_number = norm_number(_itemprop(soup, "productID"))
    section = _section(soup, "ModelCrossReference")
    if section is None or not ps_number:
        return []
    rows: list[CompatibilityRow] = []
    for tr in section.find_all("tr"):
        cells = [_txt(td) for td in tr.find_all(["td", "th"])]
        if len(cells) >= 3 and cells[1].lower() != "model number":
            rows.append(CompatibilityRow(
                ps_number=ps_number, brand=cells[0],
                model_number=norm_number(cells[1]), description=cells[2],
                source="crossref", source_url=source_url,
            ))
    if rows:
        return rows
    # fallback: the "table" is a div grid: Brand / linked model / description triplets
    for a in section.find_all("a", href=re.compile(r"/Models/")):
        model = norm_number(a.get_text(strip=True))
        brand = _txt(a.find_previous(string=True))
        rows.append(CompatibilityRow(ps_number=ps_number, brand=brand,
                                     model_number=model, source="crossref",
                                     source_url=source_url))
    return rows

# ------------------------------------------------------------------ listing pages

def parse_listing(html: str) -> list[str]:
    """Part detail URLs from a category/brand listing page (div.nf__part cards)."""
    soup = BeautifulSoup(html, "lxml")
    urls: list[str] = []
    cards = soup.select("div.nf__part") or [soup]
    for card in cards:
        for a in card.find_all("a", href=re.compile(r"/PS\d+")):
            href = urljoin(BASE_URL, a["href"]).split("?")[0]
            urls.append(href)
    return list(dict.fromkeys(urls))

# ------------------------------------------------------------------- model pages

def parse_model_page(html: str, source_url: str = "") -> list[CompatibilityRow]:
    """Harvest a model page's parts list as compatibility rows (source: model_page)."""
    soup = BeautifulSoup(html, "lxml")
    model = ""
    m = re.search(r"/Models/([A-Za-z0-9\-]+)", source_url)
    if m:
        model = norm_number(m.group(1))
    h1 = soup.find("h1")
    brand = ""
    description = ""
    if h1:
        words = _txt(h1).split()
        if words:
            brand = words[0]
        description = _txt(h1)
    rows = []
    for text in soup.find_all(string=PS_RE):
        for ps in PS_RE.findall(text):
            rows.append(CompatibilityRow(
                ps_number=ps, brand=brand, model_number=model,
                description=description, source="model_page", source_url=source_url,
            ))
    return list({r.ps_number: r for r in rows}.values())

# ------------------------------------------------------------------ repair pages

def parse_repair_index(html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    urls = []
    for a in soup.find_all("a", href=re.compile(r"/Repair/(Dishwasher|Refrigerator)/[A-Za-z\-]+/?$")):
        urls.append(urljoin(BASE_URL, a["href"]))
    return list(dict.fromkeys(urls))

def parse_repair_page(html: str, appliance: str, source_url: str = "") -> RepairGuide:
    soup = BeautifulSoup(html, "lxml")
    h1 = _txt(soup.find("h1"))
    intro = ""
    if (h1_node := soup.find("h1")) is not None:
        p = h1_node.find_next("p")
        intro = _txt(p)
    causes: list[RepairCause] = []
    # Cause sections are h2 headings between the intro and the footer.
    for rank, h2 in enumerate(soup.find_all("h2"), start=1):
        name = _txt(h2)
        if not name or name.lower().startswith(("common", "troubleshooting videos", "available brands", "more repair")):
            continue
        chunks: list[str] = []
        links: list[str] = []
        for sib in h2.find_next_siblings():
            if isinstance(sib, Tag) and sib.name == "h2":
                break
            if isinstance(sib, Tag):
                chunks.append(sib.get_text(" ", strip=True))
                links += [urljoin(BASE_URL, a["href"]) for a in sib.find_all("a", href=re.compile(r"-Parts?\.htm|/PS\d+"))]
        causes.append(RepairCause(rank=len(causes) + 1, name=name,
                                  text=" ".join(c for c in chunks if c)[:4000],
                                  part_links=list(dict.fromkeys(links))))
    slug = urlparse(source_url).path.rstrip("/").rsplit("/", 1)[-1]
    return RepairGuide(
        appliance=appliance, symptom=h1 or slug.replace("-", " "), slug=slug,
        intro=intro, causes=causes, detail_level="full",
        source_url=source_url, scraped_at=now_iso(),
    )
