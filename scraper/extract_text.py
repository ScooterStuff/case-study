"""Fallback parser for *text-extracted* PartSelect pages.

Primary path is parse.py over raw HTML. During the AI-native build the agent
environment could only retrieve text extractions of live pages (no raw HTML),
so this module parses those extractions into the same record shapes. See
playbook/DEVIATIONS.md. Usage:

    python -m scraper.extract_text <extraction.txt> ... --out workdir/
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from scraper.parse import CompatibilityRow, Part, QnA, RepairStory, now_iso, norm_number, parse_price

CANONICAL_RE = re.compile(r"^canonical: (\S+)", re.M)
ARROW_RE = re.compile(r"^\u2192 (\S+)", re.M)
PS_URL_RE = re.compile(r"https://www\.partselect\.com/(PS\d+)-([A-Za-z0-9\-]+?)-([A-Za-z0-9]+)-([A-Za-z0-9\-]+)\.htm")

def detect(text: str) -> tuple[str, str]:
    m = CANONICAL_RE.search(text) or ARROW_RE.search(text)
    url = m.group(1) if m else ""
    if re.search(r"/PS\d+-", url):
        return "part", url
    if "/Models/" in url:
        return "model", url
    if "/Repair/" in url:
        return "repair", url
    if url.endswith("-Parts.htm"):
        return "listing", url
    return "unknown", url

def _block_after(text: str, marker: str, stops: list[str]) -> str:
    idx = text.find(marker)
    if idx == -1:
        return ""
    rest = text[idx + len(marker):]
    cut = min((rest.find(s) for s in stops if rest.find(s) > 0), default=len(rest))
    return rest[:cut]

def _bullets(block: str) -> list[str]:
    return [ln.lstrip("-* ").strip() for ln in block.splitlines()
            if ln.strip().startswith(("- ", "* "))]

def _infer_appliance_text(works: list[str], title: str, url: str) -> str:
    hay = " ".join(works).lower() or (title + " " + url).lower()
    if "dishwasher" in hay or "dishrack" in hay:
        return "dishwasher"
    if any(k in hay for k in ("refrigerator", "fridge", "freezer", "ice maker", "icemaker")):
        return "refrigerator"
    return ""


def parse_part_extraction(text: str, url: str) -> tuple[Part, list[CompatibilityRow]]:
    ps = re.search(r"PartSelect Number (PS\d+)", text)
    mpn = re.search(r"Manufacturer Part Number (\S+)", text)
    um = PS_URL_RE.search(url)
    brand = um.group(2).replace("-", " ") if um else ""
    title = um.group(4).replace("-", " ") if um else ""
    h1_m = re.search(r"^# (?!How To)(.+)$", text, re.M)
    title_m = re.search(r"^Official .*?([A-Z][^|–]+?) – PartSelect\.com", text)
    if h1_m:
        title = h1_m.group(1).strip()
    elif title_m:
        title = title_m.group(1).strip()
    price_m = (re.search(r"^\$ ([0-9][0-9,]*\.[0-9]{2})$", text, re.M)
               or re.search(r"^\$\s*\n\s*\n?([0-9][0-9,]*\.[0-9]{2})\s*$", text, re.M))
    avail_m = re.search(r"^(In Stock|Special Order|Out of Stock|No Longer Available)$", text, re.M)
    desc_m = re.search(r"Product Description\n\n(?:#+ [^\n]+\n\n)?(.+?)(?:\n\n!\[|\n\nHow Buying OEM|\n\nBack to Top)", text, re.S)
    desc = desc_m.group(1).strip() if desc_m else ""
    if desc.startswith(("[", "Jump to:")):
        desc = ""
    rating_m = re.search(r"(\d\.\d)\n\nFilter By Rating", text) or re.search(r"Average Rating:.*?(\d\.\d)", text, re.S)
    reviews_m = re.search(r"(\d+) Reviews", text)
    diff_m = re.search(r"Reviews\]\(#CustomerReviews\)\n\n(.+?)\n\n(.+?)\n\nRated by", text, re.S)

    symptoms = _bullets(_block_after(text, "This part fixes the following symptoms:", ["This part works with"]))
    works = _bullets(_block_after(text, "This part works with the following products:", ["Part#", "Back to Top"]))
    repl_m = re.search(r"replaces these:\n\n(.+?)\n\n", text, re.S)
    replaces = [norm_number(x) for x in repl_m.group(1).split(",")] if repl_m else []

    qna = []
    for q_m in re.finditer(r"For model number ([A-Za-z0-9#/\- ]+)\n", text):
        qna.append(QnA(question=f"For model number {q_m.group(1).strip()}",
                       model_numbers=[norm_number(q_m.group(1).split()[-1])]))
    stories = []
    for s_m in re.finditer(r"\n(?P<body>[^\n]{30,400})\n\n.*?- Difficulty Level:\n\n(?P<d>.+?)\n\n- Total Repair Time:\n\n(?P<t>.+?)\n", text, re.S):
        stories.append(RepairStory(text=s_m.group("body").strip(),
                                   difficulty=s_m.group("d").strip(),
                                   repair_time=s_m.group("t").strip()))
        if len(stories) >= 5:
            break
    yt = list(dict.fromkeys(
        re.findall(r"https://www\.youtube\.com/watch[^)\"\s]+", text)
        + [f"https://www.youtube.com/watch?v={vid}"
           for vid in re.findall(r"i\.ytimg\.com/vi/([A-Za-z0-9_-]{6,})/", text)]))
    videos = [{"url": u, "title": ""} for u in yt]

    part = Part(
        ps_number=norm_number(ps.group(1)) if ps else "",
        mpn=norm_number(mpn.group(1)) if mpn else "",
        brand=brand, title=title, price=parse_price(price_m.group(1)) if price_m else None,
        availability=avail_m.group(1) if avail_m else "",
        description=desc[:1500],
        symptoms=symptoms, works_with=works, replaces=replaces,
        rating=float(rating_m.group(1)) if rating_m else None,
        review_count=int(reviews_m.group(1)) if reviews_m else None,
        install_difficulty=diff_m.group(1).strip() if diff_m else "",
        install_time=diff_m.group(2).strip() if diff_m else "",
        videos=videos, repair_stories=stories, qna=qna[:5],
        appliance_type=_infer_appliance_text(works, title, url),
        source_url=url, scraped_at=now_iso(),
    )

    rows: list[CompatibilityRow] = []
    xref = _block_after(text, "This part works with the following models:", ["Back to Top\n\nYou May Also Need", "\n#### Join Our"])
    triplet = re.compile(r"\n([A-Za-z][A-Za-z \-]+?)\n\n\[([A-Za-z0-9\-]+)\]\(https://www\.partselect\.com/Models/[^)]+\)\n\n([^\n]+)")
    for m in triplet.finditer(xref):
        rows.append(CompatibilityRow(ps_number=part.ps_number, brand=m.group(1).strip(),
                                     model_number=norm_number(m.group(2)),
                                     description=m.group(3).strip(" -"), source="crossref",
                                     source_url=url))
    if not part.appliance_type and rows:
        part.appliance_type = _infer_appliance_text(
            [r.description for r in rows[:5]], part.title, url)
    for q in part.qna:
        for model in q.model_numbers:
            rows.append(CompatibilityRow(ps_number=part.ps_number, brand=part.brand,
                                         model_number=model, source="qna", source_url=url))
    return part, rows

def parse_model_extraction(text: str, url: str) -> list[CompatibilityRow]:
    model_m = re.search(r"/Models/([A-Za-z0-9\-]+)", url)
    model = norm_number(model_m.group(1)) if model_m else ""
    desc_m = re.search(r"^(.+?) - OEM Parts & Repair Help", text, re.M)
    description = desc_m.group(1).strip() if desc_m else ""
    brand = description.split()[0] if description else ""
    rows = [CompatibilityRow(ps_number=ps, brand=brand, model_number=model,
                             description=description, source="model_page", source_url=url)
            for ps in dict.fromkeys(re.findall(r"PartSelect #: (PS\d+)", text))]
    return rows

def parse_listing_extraction(text: str, url: str) -> list[str]:
    return list(dict.fromkeys(m.group(0).split("?")[0] for m in PS_URL_RE.finditer(text)))

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    parts, rows, urls = [], [], []
    for f in args.files:
        text = f.read_text(encoding="utf-8", errors="replace")
        kind, url = detect(text)
        if kind == "part":
            part, part_rows = parse_part_extraction(text, url)
            if part.ps_number:
                parts.append(part.model_dump())
                rows += [r.model_dump() for r in part_rows]
        elif kind == "model":
            rows += [r.model_dump() for r in parse_model_extraction(text, url)]
        elif kind == "listing":
            urls += parse_listing_extraction(text, url)
        print(f"{f.name}: {kind} ({url})")
    for name, payload in (("parts", parts), ("compat", rows), ("urls", list(dict.fromkeys(urls)))):
        path = args.out / f"{name}.jsonl"
        with path.open("a", encoding="utf-8") as fh:
            for item in payload:
                fh.write(json.dumps(item) + "\n")
    print(f"appended: {len(parts)} parts, {len(rows)} compat rows, {len(urls)} urls -> {args.out}")

if __name__ == "__main__":
    main()
