// Generates docs/PartSelect-Chat-Agent-Deck.pptx
//   npm install && node gen.js
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const FA = require("react-icons/fa");

const TEAL = "337778", TEAL_DARK = "285F60", YELLOW = "F3C04C", RED = "F4364C",
      BG = "FFFFFF", PANEL = "F6F6F4", INK = "121212", MUTED = "555453", BORDER = "D7D7D7";
const H = "Trebuchet MS", B = "Calibri";

async function icon(Comp, color, size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Comp, { color: "#" + color, size: String(size) }));
  const png = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + png.toString("base64");
}

(async () => {
  const icons = {};
  const want = {
    search: [FA.FaSearch, "FFFFFF"], db: [FA.FaDatabase, "FFFFFF"], shield: [FA.FaShieldAlt, "FFFFFF"],
    chart: [FA.FaChartBar, "FFFFFF"], puzzle: [FA.FaPuzzlePiece, "FFFFFF"], robot: [FA.FaRobot, "FFFFFF"],
    wrench: [FA.FaWrench, "FFFFFF"], snow: [FA.FaSnowflake, "FFFFFF"], dish: [FA.FaTint, "FFFFFF"],
    eye: [FA.FaEye, "FFFFFF"], redX: [FA.FaTimesCircle, RED],
  };
  for (const [k, [c, col]] of Object.entries(want)) icons[k] = await icon(c, col);

  const p = new pptxgen();
  p.layout = "LAYOUT_16x9";
  p.author = "Tatsan";
  p.title = "PartSelect Chat Agent — Instalily Case Study";
  const shadow = () => ({ type: "outer", color: "000000", blur: 7, offset: 2, angle: 135, opacity: 0.14 });

  const chip = (s, x, y, w, text, opts = {}) => {
    s.addShape(p.shapes.ROUNDED_RECTANGLE, { x, y, w, h: 0.32, rectRadius: 0.16,
      fill: { color: opts.fill || PANEL }, line: { color: opts.line || BORDER, width: 0.75 } });
    s.addText(text, { x, y: y - 0.015, w, h: 0.35, align: "center", fontSize: opts.fs || 10.5,
      fontFace: B, color: opts.color || MUTED, bold: !!opts.bold, margin: 0 });
  };
  const circleIcon = (s, key, x, y, d = 0.46, bg = TEAL) => {
    s.addShape(p.shapes.OVAL, { x, y, w: d, h: d, fill: { color: bg } });
    s.addImage({ data: icons[key], x: x + d * 0.24, y: y + d * 0.24, w: d * 0.52, h: d * 0.52 });
  };
  const title = (s, text, sub) => {
    s.addText(text, { x: 0.55, y: 0.32, w: 8.9, h: 0.6, fontSize: 30, bold: true, fontFace: H, color: INK, margin: 0 });
    if (sub) s.addText(sub, { x: 0.55, y: 0.88, w: 8.9, h: 0.34, fontSize: 13.5, fontFace: B, color: MUTED, margin: 0 });
  };

  // ---------------------------------------------------------------- 1 TITLE
  let s = p.addSlide();
  s.background = { color: TEAL };
  s.addShape(p.shapes.OVAL, { x: 7.1, y: -1.6, w: 4.6, h: 4.6, fill: { color: TEAL_DARK } });
  s.addShape(p.shapes.OVAL, { x: -1.3, y: 4.0, w: 3.4, h: 3.4, fill: { color: TEAL_DARK } });
  s.addText([{ text: "Part", options: { color: "FFFFFF" } }, { text: "Select", options: { color: YELLOW } },
             { text: "  Chat Agent", options: { color: "FFFFFF" } }],
    { x: 0.7, y: 1.55, w: 8.6, h: 0.85, fontSize: 44, bold: true, fontFace: H, margin: 0 });
  s.addText("From symptom to a verified, in-cart part — with measured accuracy.",
    { x: 0.7, y: 2.45, w: 7.6, h: 0.5, fontSize: 18, fontFace: B, color: "E8F0EF", italic: true, margin: 0 });
  chip(s, 0.7, 3.25, 2.05, "40/40 eval cases", { fill: TEAL_DARK, line: TEAL_DARK, color: "FFFFFF", bold: true, fs: 11 });
  chip(s, 2.9, 3.25, 2.5, "0 hallucinated part #s", { fill: TEAL_DARK, line: TEAL_DARK, color: "FFFFFF", bold: true, fs: 11 });
  chip(s, 5.55, 3.25, 2.3, "real scraped data", { fill: TEAL_DARK, line: TEAL_DARK, color: "FFFFFF", bold: true, fs: 11 });
  s.addText("Instalily case study  ·  Tatsan  ·  github.com/ScooterStuff/case-study",
    { x: 0.7, y: 4.75, w: 8.6, h: 0.35, fontSize: 12.5, fontFace: B, color: "BFD8D6", margin: 0 });

  // ------------------------------------------- 2 THREE USER JOBS (product framing)
  s = p.addSlide(); s.background = { color: BG };
  title(s, "Built around three user jobs", "What does someone with a broken appliance actually want from a parts chat?");
  const q = [
    ["1", "“How can I install part number PS11752778?”", "→  I have the part — walk me through the install"],
    ["2", "“Is this part compatible with my WDT780SAEM1 model?”", "→  will this fit MY machine? (the money question)"],
    ["3", "“The ice maker on my Whirlpool fridge is not working…”", "→  something's broken — figure out what I need"],
  ];
  q.forEach((row, i) => {
    const y = 1.45 + i * 0.78;
    s.addShape(p.shapes.RECTANGLE, { x: 0.55, y, w: 5.7, h: 0.62, fill: { color: PANEL }, line: { color: BORDER, width: 0.75 } });
    s.addShape(p.shapes.OVAL, { x: 0.72, y: y + 0.14, w: 0.34, h: 0.34, fill: { color: TEAL } });
    s.addText(row[0], { x: 0.72, y: y + 0.12, w: 0.34, h: 0.34, align: "center", fontSize: 13, bold: true, color: "FFFFFF", fontFace: H, margin: 0 });
    s.addText([{ text: row[1], options: { fontSize: 11.5, bold: true, color: INK, breakLine: true } },
               { text: row[2], options: { fontSize: 10, color: MUTED } }],
      { x: 1.22, y: y + 0.05, w: 4.95, h: 0.55, fontFace: B, margin: 0, valign: "middle" });
  });
  s.addShape(p.shapes.RECTANGLE, { x: 6.55, y: 1.45, w: 2.95, h: 2.34, fill: { color: TEAL }, shadow: shadow() });
  s.addText("Jobs → flows → tests", { x: 6.8, y: 1.7, w: 2.45, h: 0.4, fontSize: 15, bold: true, color: YELLOW, fontFace: H, margin: 0 });
  s.addText("Each job became a product flow in the chat — install help, fit checks, diagnosis — and an automated test that gates every change.",
    { x: 6.8, y: 2.15, w: 2.45, h: 1.5, fontSize: 11.5, color: "FFFFFF", fontFace: B, margin: 0 });
  s.addShape(p.shapes.RECTANGLE, { x: 0.55, y: 4.15, w: 8.95, h: 0.78, fill: { color: PANEL }, line: { color: BORDER, width: 0.75 } });
  s.addText([{ text: "Product principle:  ", options: { bold: true, color: INK } },
             { text: "a parts assistant is only useful if every answer can be trusted — wrong part numbers mean wrong orders and returns. So ", options: { color: MUTED } },
             { text: "accuracy is a feature", options: { bold: true, color: TEAL } },
             { text: ", and it's measured like one.", options: { color: MUTED } }],
    { x: 0.8, y: 4.25, w: 8.5, h: 0.6, fontSize: 12.5, fontFace: B, margin: 0, valign: "middle" });

  // ------------------------------------------------- 3 WHY TRUST IS THE HARD PART
  s = p.addSlide(); s.background = { color: BG };
  title(s, "Why trust is the hard part", "I pulled the real PartSelect pages for those queries before designing anything. Look closely:");
  s.addShape(p.shapes.RECTANGLE, { x: 0.55, y: 1.5, w: 3.6, h: 2.15, fill: { color: PANEL }, line: { color: BORDER, width: 1 } });
  circleIcon(s, "snow", 0.8, 1.75, 0.5);
  s.addText("PS11752778", { x: 1.45, y: 1.78, w: 2.6, h: 0.3, fontSize: 14, bold: true, fontFace: "Courier New", color: INK, margin: 0 });
  s.addText("Refrigerator Door Shelf Bin\nWhirlpool WPW10321304 · $47.40 · In Stock",
    { x: 0.8, y: 2.45, w: 3.15, h: 0.9, fontSize: 11, fontFace: B, color: MUTED, margin: 0 });
  s.addShape(p.shapes.RECTANGLE, { x: 5.85, y: 1.5, w: 3.6, h: 2.15, fill: { color: PANEL }, line: { color: BORDER, width: 1 } });
  circleIcon(s, "dish", 6.1, 1.75, 0.5);
  s.addText("WDT780SAEM1", { x: 6.75, y: 1.78, w: 2.6, h: 0.3, fontSize: 14, bold: true, fontFace: "Courier New", color: INK, margin: 0 });
  s.addText("Whirlpool DISHWASHER model\n(12 verified parts in the scraped cross-reference)",
    { x: 6.1, y: 2.45, w: 3.15, h: 0.9, fontSize: 11, fontFace: B, color: MUTED, margin: 0 });
  s.addImage({ data: icons.redX, x: 4.62, y: 2.05, w: 0.75, h: 0.75 });
  s.addText("not a\nverified fit", { x: 4.32, y: 2.85, w: 1.36, h: 0.6, align: "center", fontSize: 10.5, bold: true, color: RED, fontFace: B, margin: 0 });
  s.addShape(p.shapes.RECTANGLE, { x: 0.55, y: 4.0, w: 8.95, h: 1.05, fill: { color: INK } });
  s.addText([{ text: "Real customers mix up parts and models constantly — example query 2 does it too.", options: { bold: true, color: YELLOW, breakLine: true, fontSize: 13.5 } },
             { text: "A chatbot that confidently says “yes, it fits!” here causes a wrong order, a return, and lost trust. So in this product, compatibility comes from a database JOIN over scraped fitment data — the LLM never gets to guess.",
               options: { color: "FFFFFF", fontSize: 12 } }],
    { x: 0.85, y: 4.13, w: 8.35, h: 0.85, fontFace: B, margin: 0 });

  // ------------------------------------------------- 4 ARCHITECTURE
  s = p.addSlide(); s.background = { color: BG };
  title(s, "Architecture: one agent, hard rails", "Single tool-calling LLM — extensibility lives in the tool registry, not in agent count.");
  const boxes = [
    { x: 0.45, w: 1.5, t: "Scope Guard", d: "regex fast-path,\nthen tiny classifier", ic: "shield", bg: PANEL, tc: INK },
    { x: 2.35, w: 1.75, t: "Agent Loop", d: "one LLM · 6 tools\nmax 4 rounds · SSE", ic: "robot", bg: TEAL, tc: "FFFFFF" },
    { x: 4.5, w: 1.95, t: "Tool Registry", d: "search · details · compat\ndiagnose · install · orders", ic: "wrench", bg: PANEL, tc: INK },
    { x: 6.85, w: 2.7, t: "Postgres + pgvector", d: "facts via SQL · fuzz via RAG\none database, one JOIN away", ic: "db", bg: TEAL, tc: "FFFFFF" },
  ];
  boxes.forEach((b2, i) => {
    s.addShape(p.shapes.RECTANGLE, { x: b2.x, y: 1.55, w: b2.w, h: 1.7, fill: { color: b2.bg },
      line: { color: b2.bg === PANEL ? BORDER : b2.bg, width: 1 }, shadow: shadow() });
    circleIcon(s, b2.ic, b2.x + b2.w / 2 - 0.23, 1.75, 0.46, b2.bg === TEAL ? TEAL_DARK : TEAL);
    s.addText(b2.t, { x: b2.x + 0.05, y: 2.3, w: b2.w - 0.1, h: 0.3, align: "center", fontSize: 12.5, bold: true,
      fontFace: H, color: b2.tc, margin: 0 });
    s.addText(b2.d, { x: b2.x + 0.05, y: 2.62, w: b2.w - 0.1, h: 0.55, align: "center", fontSize: 9,
      fontFace: B, color: b2.tc === INK ? MUTED : "DCEAE9", margin: 0 });
    if (i < boxes.length - 1) {
      const ax = b2.x + b2.w, nx = boxes[i + 1].x;
      s.addText("→", { x: ax - 0.02, y: 2.18, w: nx - ax + 0.04, h: 0.4, align: "center", fontSize: 18, bold: true, color: TEAL, fontFace: B, margin: 0 });
    }
  });
  s.addShape(p.shapes.RECTANGLE, { x: 2.35, y: 3.6, w: 4.1, h: 0.72, fill: { color: RED } });
  s.addText([{ text: "Hallucination validator  ", options: { bold: true, color: "FFFFFF", fontSize: 12 } },
             { text: "every PS# in the final draft must come from a tool result — retry, then strip", options: { color: "FFE3E6", fontSize: 10 } }],
    { x: 2.55, y: 3.66, w: 3.8, h: 0.6, fontFace: B, margin: 0, valign: "middle" });
  s.addText("↑ final draft gated before tokens flush", { x: 2.35, y: 4.38, w: 4.1, h: 0.3, align: "center", fontSize: 9.5, italic: true, color: MUTED, fontFace: B, margin: 0 });
  s.addShape(p.shapes.RECTANGLE, { x: 0.45, y: 4.78, w: 9.1, h: 0.55, fill: { color: PANEL }, line: { color: BORDER, width: 0.75 } });
  s.addText("Streaming UX: tool-status pills stream live; ui_blocks render as rich components mid-stream; provider swaps via 3 env vars (OpenAI-compatible).",
    { x: 0.7, y: 4.83, w: 8.7, h: 0.45, fontSize: 10.5, fontFace: B, color: MUTED, margin: 0, valign: "middle" });

  // ------------------------------------------------- 5 HYBRID RETRIEVAL
  s = p.addSlide(); s.background = { color: BG };
  title(s, "Hybrid retrieval: facts vs. fuzz", "The split that makes honesty possible — in one database, so semantic hits JOIN price & stock.");
  s.addShape(p.shapes.RECTANGLE, { x: 0.55, y: 1.5, w: 4.3, h: 3.0, fill: { color: TEAL }, shadow: shadow() });
  s.addText("FACTS — deterministic SQL", { x: 0.85, y: 1.7, w: 3.8, h: 0.35, fontSize: 14.5, bold: true, color: "FFFFFF", fontFace: H, margin: 0 });
  s.addText([
    { text: "prices · stock · compatibility · supersessions", options: { bullet: true, breakLine: true } },
    { text: "check_compat() returns a 4-state verdict with evidence — verified_fit / no_match_found / unknown_model / unknown_part", options: { bullet: true, breakLine: true } },
    { text: "cross-reference pages are paginated → partial data → a miss is “not in our verified list,” never “incompatible”", options: { bullet: true } },
  ], { x: 0.85, y: 2.1, w: 3.75, h: 2.25, fontSize: 11, color: "EAF2F1", fontFace: B, paraSpaceAfter: 8, margin: 0 });
  s.addShape(p.shapes.RECTANGLE, { x: 5.15, y: 1.5, w: 4.3, h: 3.0, fill: { color: PANEL }, line: { color: BORDER, width: 1 }, shadow: shadow() });
  s.addText("FUZZ — RAG over pgvector", { x: 5.45, y: 1.7, w: 3.8, h: 0.35, fontSize: 14.5, bold: true, color: TEAL_DARK, fontFace: H, margin: 0 });
  s.addText([
    { text: "“the thing that sprays water in the bottom” → Lower Spray Arm (hybrid: tsvector + vectors, RRF-merged)", options: { bullet: true, breakLine: true } },
    { text: "symptoms → repair guides with causes kept in PartSelect's likelihood order", options: { bullet: true, breakLine: true } },
    { text: "real customer Q&A + repair stories embedded — matches how people actually talk", options: { bullet: true } },
  ], { x: 5.45, y: 2.1, w: 3.75, h: 2.25, fontSize: 11, color: INK, fontFace: B, paraSpaceAfter: 8, margin: 0 });
  s.addShape(p.shapes.RECTANGLE, { x: 0.55, y: 4.72, w: 8.95, h: 0.6, fill: { color: INK } });
  s.addText([{ text: "Anything dangerous to hallucinate lives in SQL. Anything that benefits from meaning lives in vectors. ", options: { color: "FFFFFF", bold: true } },
             { text: "Same engine, one docker compose up.", options: { color: YELLOW } }],
    { x: 0.8, y: 4.76, w: 8.5, h: 0.52, fontSize: 12, fontFace: B, margin: 0, valign: "middle" });

  // ------------------------------------------------- 6 DATA PIPELINE
  s = p.addSlide(); s.background = { color: BG };
  title(s, "Real data, shipped reproducibly", "An agent is only as honest as its data — so data came before any LLM work.");
  const steps = [
    ["1", "Polite crawler", "on-disk cache by URL hash · 2.5s delay · 600-page cap · re-runs = zero network (unit-tested)"],
    ["2", "Parse the site's hidden data model", "schema.org microdata · cross-reference tables · ranked repair causes · Q&A model numbers (provenance-tagged)"],
    ["3", "Ingest + embed", "normalize → Postgres → pgvector embeddings · tsvector keyword index"],
    ["4", "Committed seed", "datasets + seed.sql.gz in the repo → fresh clone runs with no scraping and no API keys; first boot self-heals"],
  ];
  steps.forEach((row, i) => {
    const y = 1.5 + i * 0.82;
    s.addShape(p.shapes.OVAL, { x: 0.6, y: y + 0.08, w: 0.4, h: 0.4, fill: { color: TEAL } });
    s.addText(row[0], { x: 0.6, y: y + 0.06, w: 0.4, h: 0.4, align: "center", fontSize: 14, bold: true, color: "FFFFFF", fontFace: H, margin: 0 });
    s.addText([{ text: row[1] + "  ", options: { bold: true, fontSize: 12.5, color: INK } },
               { text: row[2], options: { fontSize: 11, color: MUTED } }],
      { x: 1.2, y, w: 5.3, h: 0.72, fontFace: B, margin: 0, valign: "middle" });
  });
  s.addShape(p.shapes.RECTANGLE, { x: 6.85, y: 1.5, w: 2.65, h: 3.3, fill: { color: PANEL }, line: { color: BORDER, width: 1 } });
  s.addText("In the seed", { x: 7.1, y: 1.68, w: 2.2, h: 0.3, fontSize: 13, bold: true, fontFace: H, color: TEAL_DARK, margin: 0 });
  const stats = [["34", "real parts (all spec-critical records)"], ["1,130", "compatibility rows"], ["21", "repair guides"], ["358", "embedded docs"]];
  stats.forEach((st, i) => {
    const y = 2.05 + i * 0.68;
    s.addText(st[0], { x: 7.1, y, w: 1.0, h: 0.4, fontSize: 19, bold: true, color: TEAL, fontFace: H, margin: 0 });
    s.addText(st[1], { x: 7.95, y: y + 0.02, w: 1.5, h: 0.6, fontSize: 9, color: MUTED, fontFace: B, margin: 0 });
  });
  s.addText("scrape.py scales the same pipeline to 150+ parts — architecture over volume.",
    { x: 0.6, y: 4.85, w: 8.9, h: 0.35, fontSize: 11, italic: true, color: MUTED, fontFace: B, margin: 0 });

  // ------------------------------------------------- 7 EVAL RESULTS
  s = p.addSlide(); s.background = { color: TEAL };
  s.addText("Accuracy is a feature — so it's measured", { x: 0.55, y: 0.35, w: 8.9, h: 0.55, fontSize: 29, bold: true, fontFace: H, color: "FFFFFF", margin: 0 });
  s.addText("40 multi-turn cases replayed through the live SSE API — tool selection, answer content, scope, and a mechanical hallucination check.",
    { x: 0.55, y: 0.92, w: 8.9, h: 0.35, fontSize: 13, fontFace: B, color: "CFE2E1", margin: 0 });
  const big = [["40/40", "cases pass"], ["0", "hallucinated part numbers"], ["100%", "scope adherence"], ["31 ms", "p50 latency (mock mode)"]];
  big.forEach((bs, i) => {
    const x = 0.55 + i * 2.3;
    s.addShape(p.shapes.RECTANGLE, { x, y: 1.6, w: 2.1, h: 1.5, fill: { color: TEAL_DARK } });
    s.addText(bs[0], { x, y: 1.75, w: 2.1, h: 0.7, align: "center", fontSize: i === 1 ? 40 : 28, bold: true, color: i === 1 ? YELLOW : "FFFFFF", fontFace: H, margin: 0 });
    s.addText(bs[1], { x: x + 0.1, y: 2.5, w: 1.9, h: 0.5, align: "center", fontSize: 11, color: "CFE2E1", fontFace: B, margin: 0 });
  });
  s.addText([
    { text: "Suites: user-job canonical 3/3 · compatibility 8/8 · fuzzy search 6/6 · diagnosis 6/6 · scope 8/8 · injection 4/4 · grounding 5/5", options: { breakLine: true, fontSize: 12, color: "FFFFFF", bold: true } },
    { text: "Favorite case — “Just guess whether it fits, yes or no?” → the agent refuses to guess and gives the verified-list answer.", options: { breakLine: true, fontSize: 11.5, color: "CFE2E1" } },
    { text: "The eval earned its keep: it caught two real routing bugs before any human tester would have.", options: { fontSize: 11.5, color: "CFE2E1" } },
  ], { x: 0.55, y: 3.45, w: 8.9, h: 1.1, fontFace: B, paraSpaceAfter: 6, margin: 0 });
  s.addShape(p.shapes.RECTANGLE, { x: 0.55, y: 4.75, w: 8.9, h: 0.55, fill: { color: YELLOW } });
  s.addText("Evals measure whether the agent is right. Tests measure whether the code is correct. This repo ships both.",
    { x: 0.8, y: 4.79, w: 8.4, h: 0.47, fontSize: 12.5, bold: true, color: INK, fontFace: B, margin: 0, valign: "middle" });

  // ------------------------------------------------- 8 UX JOURNEY
  s = p.addSlide(); s.background = { color: BG };
  title(s, "UX: the fix-it journey is the product", "A stressed person with a broken appliance needs one continuous path — the conversation is the UI.");
  const jr = [["1", "Symptom", "ranked diagnosis card,\ncauses expandable"], ["2", "Right part", "product cards: price,\nstock, difficulty, rating"],
              ["3", "Verify fit", "“Check fits my model” →\n✓ / ⚠ verdict + evidence"], ["4", "Install", "video + real customer\nrepair stories"], ["5", "Cart", "add to cart → drawer,\norder-status timeline"]];
  jr.forEach((j, i) => {
    const x = 0.45 + i * 1.92;
    s.addShape(p.shapes.RECTANGLE, { x, y: 1.6, w: 1.72, h: 1.95, fill: { color: i === 2 ? TEAL : PANEL }, line: { color: i === 2 ? TEAL : BORDER, width: 1 }, shadow: shadow() });
    s.addShape(p.shapes.OVAL, { x: x + 0.61, y: 1.78, w: 0.5, h: 0.5, fill: { color: i === 2 ? TEAL_DARK : TEAL } });
    s.addText(j[0], { x: x + 0.61, y: 1.76, w: 0.5, h: 0.5, align: "center", fontSize: 16, bold: true, color: "FFFFFF", fontFace: H, margin: 0 });
    s.addText(j[1], { x, y: 2.38, w: 1.72, h: 0.3, align: "center", fontSize: 12.5, bold: true, fontFace: H, color: i === 2 ? "FFFFFF" : INK, margin: 0 });
    s.addText(j[2], { x: x + 0.06, y: 2.7, w: 1.6, h: 0.8, align: "center", fontSize: 9, fontFace: B, color: i === 2 ? "DCEAE9" : MUTED, margin: 0 });
    if (i < 4) s.addText("→", { x: x + 1.7, y: 2.3, w: 0.26, h: 0.4, align: "center", fontSize: 15, bold: true, color: TEAL, fontFace: B, margin: 0 });
  });
  s.addText([
    { text: "Chat-native navigation: card buttons (“Install guide”, “Check fits my model”) send templated messages back into the conversation.", options: { bullet: true, breakLine: true } },
    { text: "Streaming everywhere: tokens < 1.5s, tool pills (“Checking compatibility…”) appear and fade live; SSE proxied unbuffered through nginx.", options: { bullet: true, breakLine: true } },
    { text: "PartSelect branding tokens lifted from the real site's CSS (teal #337778, accent yellow) — trustworthy DIY-helper, not a flashy AI app.", options: { bullet: true } },
  ], { x: 0.6, y: 3.85, w: 8.9, h: 1.5, fontSize: 11.5, fontFace: B, color: INK, paraSpaceAfter: 7, margin: 0 });

  // ------------------------------------------------- 9 TRADE-OFFS
  s = p.addSlide(); s.background = { color: BG };
  title(s, "Decisions & trade-offs", "Full ADR-style log lives in playbook/TRADEOFFS.md — these are the five that matter.");
  const rows = [
    ["One Postgres for facts AND vectors", "semantic hits JOIN price/stock in-db; one engine to run", "vs. SQLite+Chroma simplicity · revisit ~1M embeddings"],
    ["Raw parameterized SQL, no ORM", "~10 queries — the SQL is the architecture demo", "gave up migrations tooling · revisit at 3× query count"],
    ["Single agent + tool registry", "lower latency, simpler failures, easier evals", "vs. multi-agent · revisit when tools outgrow one prompt"],
    ["Buffer-and-release final prose", "mechanical zero-hallucination guarantee", "costs ~100ms perceived · invisible next to tool time"],
    ["Scripted MOCK_LLM mode", "CI, e2e, demos run keyless and free", "mock proves the rails; eval proves the model"],
  ];
  const tbl = [[
    { text: "Decision", options: { bold: true, color: "FFFFFF", fill: { color: TEAL }, fontSize: 11.5 } },
    { text: "Why", options: { bold: true, color: "FFFFFF", fill: { color: TEAL }, fontSize: 11.5 } },
    { text: "The other side of it", options: { bold: true, color: "FFFFFF", fill: { color: TEAL }, fontSize: 11.5 } },
  ]].concat(rows.map((r, i) => r.map((c, j) => ({ text: c, options: {
    fontSize: 10.5, color: j === 0 ? INK : MUTED, bold: j === 0,
    fill: { color: i % 2 ? PANEL : "FFFFFF" } } }))));
  s.addTable(tbl, { x: 0.55, y: 1.5, w: 8.95, colW: [2.85, 3.05, 3.05], border: { pt: 0.5, color: BORDER },
    fontFace: B, valign: "middle", rowH: 0.62, margin: 0.06 });

  // ------------------------------------------------- 10 EXTENSIBILITY + LIMITS
  s = p.addSlide(); s.background = { color: BG };
  title(s, "Extensibility, honest limitations", "Naming your own weaknesses is a feature: it shows you know what you shipped.");
  s.addShape(p.shapes.RECTANGLE, { x: 0.55, y: 1.5, w: 4.3, h: 3.5, fill: { color: PANEL }, line: { color: BORDER, width: 1 } });
  circleIcon(s, "puzzle", 0.8, 1.7, 0.44);
  s.addText("Designed to extend", { x: 1.4, y: 1.76, w: 3.2, h: 0.32, fontSize: 14, bold: true, fontFace: H, color: TEAL_DARK, margin: 0 });
  s.addText([
    { text: "New appliance = seed URLs + one enum value", options: { bullet: true, breakLine: true } },
    { text: "Real order support = swap the mocked tool body for an OMS/ERP client — the Pydantic schema is already the contract", options: { bullet: true, breakLine: true } },
    { text: "Swap LLM provider = 3 env vars (OpenAI-compatible)", options: { bullet: true, breakLine: true } },
    { text: "Scale path: Redis sessions, per-tool caching, OTel on the existing request-id structured logs", options: { bullet: true } },
  ], { x: 0.85, y: 2.3, w: 3.75, h: 2.55, fontSize: 11, fontFace: B, color: INK, paraSpaceAfter: 8, margin: 0, valign: "top" });
  s.addShape(p.shapes.RECTANGLE, { x: 5.15, y: 1.5, w: 4.3, h: 3.5, fill: { color: PANEL }, line: { color: BORDER, width: 1 } });
  circleIcon(s, "eye", 5.4, 1.7, 0.44, "8A6A0D");
  s.addText("Known limits (by design)", { x: 6.0, y: 1.76, w: 3.2, h: 0.32, fontSize: 14, bold: true, fontFace: H, color: "8A6A0D", margin: 0 });
  s.addText([
    { text: "Cross-reference data is partial (source pages paginate) → verdicts say “verified fit” or “not in our verified list” — never a hard no", options: { bullet: true, breakLine: true } },
    { text: "34-part catalog slice; the scraper scales it on demand", options: { bullet: true, breakLine: true } },
    { text: "Order support is mocked (deterministic, schema-real)", options: { bullet: true, breakLine: true } },
    { text: "In-memory sessions; single-locale USD pricing", options: { bullet: true } },
  ], { x: 5.45, y: 2.3, w: 3.75, h: 2.55, fontSize: 11, fontFace: B, color: INK, paraSpaceAfter: 8, margin: 0, valign: "top" });

  // ------------------------------------------------- 11 CLOSING
  s = p.addSlide(); s.background = { color: TEAL };
  s.addShape(p.shapes.OVAL, { x: 7.4, y: 3.6, w: 4.2, h: 4.2, fill: { color: TEAL_DARK } });
  s.addText("Built AI-natively, verified like software", { x: 0.7, y: 0.5, w: 8.6, h: 0.6, fontSize: 28, bold: true, fontFace: H, color: "FFFFFF", margin: 0 });
  s.addText([
    { text: "A Claude agent executed the planning docs in /playbook end-to-end — scraper, data layer, agent, evals, UI, CI — with every deviation from the plan logged in DEVIATIONS.md and human review on top. The playbook ships in the repo: the process is part of the engineering.", options: { breakLine: true, fontSize: 13, color: "EAF2F1" } },
  ], { x: 0.7, y: 1.25, w: 8.4, h: 1.0, fontFace: B, margin: 0 });
  const proof = [["60+ / 87%", "pytest · backend coverage"], ["10 + 1", "Jest tests + Playwright journey"], ["CI", "lint · tests · e2e · manual eval job"], ["1 cmd", "docker compose up — seed auto-restores"]];
  proof.forEach((pr, i) => {
    const x = 0.7 + i * 2.25;
    s.addShape(p.shapes.RECTANGLE, { x, y: 2.5, w: 2.05, h: 1.15, fill: { color: TEAL_DARK } });
    s.addText(pr[0], { x, y: 2.62, w: 2.05, h: 0.45, align: "center", fontSize: 17, bold: true, color: YELLOW, fontFace: H, margin: 0 });
    s.addText(pr[1], { x: x + 0.08, y: 3.1, w: 1.9, h: 0.5, align: "center", fontSize: 9.5, color: "CFE2E1", fontFace: B, margin: 0 });
  });
  s.addText([
    { text: "Try it:  ", options: { bold: true, color: YELLOW, fontSize: 14 } },
    { text: "MOCK_LLM=1 docker compose up --build", options: { fontFace: "Courier New", color: "FFFFFF", fontSize: 13 } },
    { text: "   then ask it the three user-job queries.", options: { color: "CFE2E1", fontSize: 12 } },
  ], { x: 0.7, y: 4.05, w: 8.6, h: 0.4, fontFace: B, margin: 0 });
  s.addText("Thanks — Tatsan  ·  github.com/ScooterStuff/case-study  ·  full decision log in /playbook",
    { x: 0.7, y: 4.85, w: 8.6, h: 0.35, fontSize: 12, color: "BFD8D6", fontFace: B, margin: 0 });

  await p.writeFile({ fileName: "../PartSelect-Chat-Agent-Deck.pptx" });
  console.log("WROTE docs/PartSelect-Chat-Agent-Deck.pptx");
})().catch((e) => { console.error(e); process.exit(1); });
