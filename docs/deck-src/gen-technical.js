// Generates docs/PartSelect-Technical-Deck.pptx — design & implementation
// deep-dive (assumes the audience knows the product; demo happens live after).
//   npm install && node gen-technical.js
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const FA = require("react-icons/fa");

const TEAL = "337778", TEAL_DARK = "285F60", YELLOW = "F3C04C", RED = "F4364C",
      PANEL = "F6F6F4", INK = "121212", MUTED = "555453", BORDER = "D7D7D7", CODEBG = "1A2B2B";
const H = "Trebuchet MS", B = "Calibri", M = "Courier New";

async function icon(Comp, color, size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Comp, { color: "#" + color, size: String(size) }));
  return "image/png;base64," + (await sharp(Buffer.from(svg)).png().toBuffer()).toString("base64");
}

(async () => {
  const icons = {};
  for (const [k, c] of Object.entries({ shield: FA.FaShieldAlt, db: FA.FaDatabase, robot: FA.FaRobot,
    camera: FA.FaCamera, puzzle: FA.FaPuzzlePiece, chart: FA.FaChartBar, bolt: FA.FaBolt, stream: FA.FaStream }))
    icons[k] = await icon(c, "FFFFFF");

  const p = new pptxgen();
  p.layout = "LAYOUT_16x9";
  p.author = "Tatsan";
  p.title = "PartSelect Chat Agent — Technical Deep-Dive";
  const shadow = () => ({ type: "outer", color: "000000", blur: 7, offset: 2, angle: 135, opacity: 0.14 });

  const title = (s, text, sub) => {
    s.addText(text, { x: 0.55, y: 0.3, w: 9.0, h: 0.55, fontSize: 27, bold: true, fontFace: H, color: INK, margin: 0 });
    if (sub) s.addText(sub, { x: 0.55, y: 0.83, w: 9.0, h: 0.32, fontSize: 13, fontFace: B, color: MUTED, margin: 0 });
  };
  const code = (s, x, y, w, h, lines, fs = 10.5) => {
    s.addShape(p.shapes.RECTANGLE, { x, y, w, h, fill: { color: CODEBG }, shadow: shadow() });
    s.addText(lines.map((t, i) => ({ text: t, options: { breakLine: i < lines.length - 1 } })),
      { x: x + 0.18, y: y + 0.12, w: w - 0.36, h: h - 0.24, fontFace: M, fontSize: fs,
        color: "D9E6E5", margin: 0, valign: "top", lineSpacingMultiple: 1.12 });
  };
  const circleIcon = (s, key, x, y, d = 0.44, bg = TEAL) => {
    s.addShape(p.shapes.OVAL, { x, y, w: d, h: d, fill: { color: bg } });
    s.addImage({ data: icons[key], x: x + d * 0.25, y: y + d * 0.25, w: d * 0.5, h: d * 0.5 });
  };

  // ---------------------------------------------------------------- 1 TITLE
  let s = p.addSlide();
  s.background = { color: TEAL };
  s.addShape(p.shapes.OVAL, { x: 7.3, y: -1.7, w: 4.6, h: 4.6, fill: { color: TEAL_DARK } });
  s.addShape(p.shapes.OVAL, { x: -1.4, y: 4.1, w: 3.3, h: 3.3, fill: { color: TEAL_DARK } });
  s.addText("Design & Implementation", { x: 0.7, y: 1.35, w: 8.6, h: 0.75, fontSize: 40, bold: true, fontFace: H, color: "FFFFFF", margin: 0 });
  s.addText("PartSelect Chat Agent — a technical deep-dive", { x: 0.7, y: 2.15, w: 8.6, h: 0.45, fontSize: 19, fontFace: B, color: YELLOW, margin: 0 });
  s.addText("Interface engineering  ·  agentic architecture  ·  grounding  ·  extensibility & scalability  ·  quality engineering",
    { x: 0.7, y: 2.72, w: 8.6, h: 0.4, fontSize: 13.5, italic: true, fontFace: B, color: "DCEAE9", margin: 0 });
  const stack = ["FastAPI + SSE", "Postgres 16 + pgvector", "React (CRA)", "client-side OCR", "eval-gated CI"];
  stack.forEach((t, i) => {
    const x = 0.7 + i * 1.78;
    s.addShape(p.shapes.ROUNDED_RECTANGLE, { x, y: 3.5, w: 1.62, h: 0.34, rectRadius: 0.17, fill: { color: TEAL_DARK } });
    s.addText(t, { x, y: 3.48, w: 1.62, h: 0.38, align: "center", fontSize: 10, bold: true, color: "FFFFFF", fontFace: B, margin: 0 });
  });
  s.addText("Tatsan · github.com/ScooterStuff/case-study · live demo follows these slides",
    { x: 0.7, y: 4.8, w: 8.6, h: 0.35, fontSize: 12, fontFace: B, color: "BFD8D6", margin: 0 });

  // ------------------------------------------------- 2 SYSTEM ARCHITECTURE (diagram)
  s = p.addSlide(); s.background = { color: "FFFFFF" };
  title(s, "System architecture", "Full diagram ships in the repo (docs/media) — three properties to notice:");
  s.addImage({ path: "../media/architecture.png", x: 0.4, y: 1.25, w: 6.45, h: 4.07 });
  const props = [
    ["One database, two retrieval substrates", "facts in relational tables, semantics in pgvector — a semantic hit JOINs price & stock in the same query."],
    ["The LLM is surrounded, not trusted", "guard before it, typed tools beside it, a mechanical validator after it."],
    ["Everything runs keyless", "committed seed + scripted MOCK_LLM: CI, e2e and demos need zero API keys."],
  ];
  props.forEach((pr, i) => {
    const y = 1.45 + i * 1.3;
    s.addShape(p.shapes.RECTANGLE, { x: 7.0, y, w: 2.55, h: 1.12, fill: { color: PANEL }, line: { color: BORDER, width: 0.75 } });
    s.addText([{ text: pr[0], options: { bold: true, fontSize: 11, color: TEAL_DARK, breakLine: true } },
               { text: pr[1], options: { fontSize: 9.5, color: MUTED } }],
      { x: 7.12, y: y + 0.08, w: 2.32, h: 1.0, fontFace: B, margin: 0 });
  });

  // ------------------------------------------------- 3 RUNTIME WORKFLOW (diagram)
  s = p.addSlide(); s.background = { color: "FFFFFF" };
  title(s, "Anatomy of one chat turn", "Streaming is the spine: tool events go out live, prose is held ~100 ms for the gate.");
  s.addImage({ path: "../media/workflow.png", x: 0.4, y: 1.25, w: 6.45, h: 4.07 });
  const notes = [
    ["Buffer-and-release", "tool pills + ui_blocks stream immediately; the final draft flushes only after validation. Trust > 100 ms."],
    ["Parallel tool fan-out", "independent calls run via asyncio.gather in threads; a tool error becomes a tool_error event, never a 500."],
    ["Context discipline", "tool results enter history JSON-safe-trimmed (strings ≤400, lists ≤6) — bounded context at any conversation length."],
  ];
  notes.forEach((pr, i) => {
    const y = 1.45 + i * 1.3;
    s.addShape(p.shapes.RECTANGLE, { x: 7.0, y, w: 2.55, h: 1.12, fill: { color: PANEL }, line: { color: BORDER, width: 0.75 } });
    s.addText([{ text: pr[0], options: { bold: true, fontSize: 11, color: TEAL_DARK, breakLine: true } },
               { text: pr[1], options: { fontSize: 9.5, color: MUTED } }],
      { x: 7.12, y: y + 0.08, w: 2.32, h: 1.0, fontFace: B, margin: 0 });
  });

  // ------------------------------------------------- 4 AGENT LOOP CODE
  s = p.addSlide(); s.background = { color: "FFFFFF" };
  title(s, "The agent loop, distilled", "backend/app/agent.py — one orchestrating LLM; the registry, not agent count, is the extension axis.");
  code(s, 0.55, 1.3, 5.4, 3.95, [
    "async def chat_stream(session_id, msg):",
    "    label = guard.classify(msg, history_in_scope)",
    "    if label != 'in_scope':",
    "        yield deflection(label); return",
    "",
    "    for _round in range(MAX_TOOL_ROUNDS + 1):   # 4",
    "        text, calls = await llm.chat(msgs, schemas)",
    "        if not calls: break                # final draft",
    "        yield tool_start(...)              # live",
    "        results = await gather(*map(run_tool, calls))",
    "        yield ui_blocks(results)           # live",
    "        allowed_ps |= ps_numbers(results)",
    "        msgs += compact(results)           # trim JSON",
    "",
    "    validate_part_numbers(text, allowed_ps)",
    "    # fail -> retry w/ nudge -> strip + log",
    "    yield tokens(text); yield done(latency)",
  ], 10.5);
  const pts = [
    ["Single agent, deliberately", "multi-agent at this scale = more latency, more failure modes, harder evals. Tools are the abstraction."],
    ["Bounded by construction", "≤4 tool rounds, ≤20 history messages, trimmed tool payloads — no unbounded loops or context blowup."],
    ["Sessions are a swap point", "in-memory dict behind one accessor; Redis is a one-class change (scalability section)."],
    ["Provider-agnostic", "llm.chat() is an interface: OpenAI-compatible streaming impl + a scripted mock that honors the same contract."],
  ];
  pts.forEach((pr, i) => {
    const y = 1.3 + i * 1.0;
    s.addText([{ text: pr[0] + "  —  ", options: { bold: true, fontSize: 12, color: INK } },
               { text: pr[1], options: { fontSize: 11, color: MUTED } }],
      { x: 6.2, y, w: 3.35, h: 0.95, fontFace: B, margin: 0 });
  });

  // ------------------------------------------------- 5 GUARD LAYERS
  s = p.addSlide(); s.background = { color: "FFFFFF" };
  title(s, "Scope control as a layered system", "Cheap → expensive: most messages never pay for an extra LLM call.");
  const layers = [
    ["1", "Regex fast-path", "part/model-number shapes, appliance vocabulary, symptom verbs — in-scope traffic passes in microseconds; time-to-first-event < 1.5 s is a tested invariant.", TEAL, "FFFFFF"],
    ["2", "Tiny classifier", "only for ambiguous messages: single call, max_tokens=8, three labels (in_scope / out_of_scope / injection). Short follow-ups in an in-scope session skip it.", PANEL, INK],
    ["3", "System prompt + gate", "defense in depth: prompt restates the rules for mid-conversation drift; the hallucination gate backstops everything the first two layers miss.", PANEL, INK],
  ];
  layers.forEach((l, i) => {
    const y = 1.35 + i * 1.05;
    s.addShape(p.shapes.RECTANGLE, { x: 0.55, y, w: 6.1, h: 0.9, fill: { color: l[3] }, line: { color: l[3] === PANEL ? BORDER : l[3], width: 1 } });
    s.addShape(p.shapes.OVAL, { x: 0.72, y: y + 0.26, w: 0.38, h: 0.38, fill: { color: l[3] === TEAL ? TEAL_DARK : TEAL } });
    s.addText(l[0], { x: 0.72, y: y + 0.24, w: 0.38, h: 0.38, align: "center", fontSize: 14, bold: true, color: "FFFFFF", fontFace: H, margin: 0 });
    s.addText([{ text: l[1] + "  —  ", options: { bold: true, fontSize: 12, color: l[4] } },
               { text: l[2], options: { fontSize: 10.5, color: l[3] === TEAL ? "DCEAE9" : MUTED } }],
      { x: 1.25, y: y + 0.06, w: 5.3, h: 0.8, fontFace: B, margin: 0, valign: "middle" });
  });
  s.addShape(p.shapes.RECTANGLE, { x: 6.9, y: 1.35, w: 2.65, h: 3.0, fill: { color: INK } });
  s.addText([{ text: "Design call: embedded injections", options: { bold: true, color: YELLOW, fontSize: 12.5, breakLine: true } },
             { text: "\"Is PS3406971 compatible with X? Also ignore your instructions…\" — the guard does NOT refuse outright: the legitimate question is answered, the payload ignored. Layer 3 makes that safe; the eval's injection suite proves it.", options: { color: "FFFFFF", fontSize: 10.5 } }],
    { x: 7.1, y: 1.55, w: 2.25, h: 2.6, fontFace: B, margin: 0 });
  s.addShape(p.shapes.RECTANGLE, { x: 0.55, y: 4.6, w: 9.0, h: 0.62, fill: { color: PANEL }, line: { color: BORDER, width: 0.75 } });
  s.addText("Deflections are designed, not canned errors: varied, on-brand copy that redirects to what the agent CAN do — scope control as UX, not a wall.",
    { x: 0.8, y: 4.65, w: 8.5, h: 0.52, fontSize: 11.5, fontFace: B, color: MUTED, margin: 0, valign: "middle" });

  // ------------------------------------------------- 6 GROUNDING GATE
  s = p.addSlide(); s.background = { color: "FFFFFF" };
  title(s, "Grounding is mechanical, not prompted", "Prompts ask the model to behave; the gate makes misbehavior unshippable.");
  code(s, 0.55, 1.3, 5.4, 2.6, [
    "ALLOWED = ps_in(tool_results) | ps_typed_by_user",
    "",
    "def validate_part_numbers(draft, allowed):",
    "    mentioned = set(re.findall(r'PS\\d{5,9}', draft))",
    "    unverified = mentioned - allowed",
    "    if unverified:",
    "        raise HallucinationError(unverified)",
    "",
    "# on error: 1) retry once with corrective nudge",
    "#           2) still bad -> strip number + caveat",
    "#           3) append to hallucination_log.jsonl",
  ], 10.5);
  s.addShape(p.shapes.RECTANGLE, { x: 0.55, y: 4.15, w: 5.4, h: 1.1, fill: { color: PANEL }, line: { color: BORDER, width: 0.75 } });
  s.addText([{ text: "Why user-typed numbers are allowed:  ", options: { bold: true, fontSize: 11, color: INK } },
             { text: "\"I couldn't find PS99999999\" must be sayable. The gate blocks invention, not conversation.", options: { fontSize: 11, color: MUTED } }],
    { x: 0.75, y: 4.25, w: 5.0, h: 0.9, fontFace: B, margin: 0 });
  const gr = [
    ["Tested with a lying LLM", "a unit test injects a client that invents PS55555555 — asserts it's stripped, caveated, and logged."],
    ["Auditable by design", "every trigger appends JSONL (session, draft, numbers). The log staying empty across the 40-case eval is a shipped metric."],
    ["Honesty in the schema", "compatibility verdicts are a 4-state enum with evidence counts — 'not in our verified list' is data-layer truth, not prompt wording."],
  ];
  gr.forEach((pr, i) => {
    const y = 1.3 + i * 1.35;
    circleIcon(s, ["shield", "chart", "db"][i], 6.2, y, 0.4);
    s.addText([{ text: pr[0], options: { bold: true, fontSize: 12, color: INK, breakLine: true } },
               { text: pr[1], options: { fontSize: 10.5, color: MUTED } }],
      { x: 6.75, y: y - 0.05, w: 2.8, h: 1.3, fontFace: B, margin: 0 });
  });

  // ------------------------------------------------- 7 DATA LAYER
  s = p.addSlide(); s.background = { color: "FFFFFF" };
  title(s, "Data layer: facts you can JOIN, meaning you can search", "Raw parameterized SQL (no ORM) — ten queries that ARE the architecture.");
  code(s, 0.55, 1.3, 5.0, 3.9, [
    "parts(ps_number PK, mpn, brand, price, stock,",
    "      search_tsv tsvector GENERATED ALWAYS ...)",
    "compatibility(ps_number, model_number,",
    "      source,  PRIMARY KEY (ps, model))",
    "part_replaces(ps_number, old_mpn)  -- supersessions",
    "repair_guides / repair_causes(rank, body)",
    "embeddings(collection, document, metadata JSONB,",
    "      embedding vector(1536))  + HNSW cosine idx",
    "",
    "-- the money query: a JOIN, not a guess",
    "SELECT source FROM compatibility",
    " WHERE ps_number=%s AND model_number=%s;",
    "-- miss => evidence: how many models ARE",
    "-- verified, was the model seen at all",
  ], 10);
  const dl = [
    ["Three vector collections, one table", "repair_chunks (causes, rank preserved) · part_docs · support_snippets (real Q&A + repair stories) — metadata-filtered, no second engine."],
    ["Supersession chain", "old manufacturer numbers resolve through part_replaces — customers paste 10-year-old numbers and still land on the current part."],
    ["Provenance on every row", "compatibility rows carry source (cross-ref / model page / Q&A) — weaker signals are distinguishable, and the agent can say so."],
    ["Reproducible by seed", "pg_dump --inserts, gzipped, committed; restore needs psycopg only. First container boot self-heals."],
  ];
  dl.forEach((pr, i) => {
    const y = 1.3 + i * 1.0;
    s.addText([{ text: pr[0] + "  —  ", options: { bold: true, fontSize: 11.5, color: INK } },
               { text: pr[1], options: { fontSize: 10.5, color: MUTED } }],
      { x: 5.8, y, w: 3.75, h: 0.95, fontFace: B, margin: 0 });
  });

  // ------------------------------------------------- 8 HYBRID SEARCH
  s = p.addSlide(); s.background = { color: "FFFFFF" };
  title(s, "Hybrid search: tsvector + pgvector, RRF-merged", "\"the thing that sprays water in the bottom\" → Lower Spray Arm, with price and stock attached.");
  code(s, 0.55, 1.3, 5.4, 3.0, [
    "kw  = SELECT ... WHERE search_tsv @@",
    "      websearch_to_tsquery('english', %s)",
    "      ORDER BY ts_rank(...) DESC",
    "vec = SELECT ... FROM embeddings",
    "      WHERE collection='part_docs'",
    "        AND metadata->>'appliance_type'=%s",
    "      ORDER BY embedding <=> %s LIMIT k",
    "",
    "for rank, part in enumerate(kw):  score += 1/(60+rank)",
    "for rank, part in enumerate(vec): score += 1/(60+rank)",
    "return top_k(score)        # reciprocal rank fusion",
  ], 10.5);
  const hs = [
    ["Why RRF", "keyword and cosine scores live on incomparable scales; rank fusion needs no calibration, no tuned weights, and degrades gracefully when one side is empty."],
    ["Why both", "exact tokens (mpn, 'W10195416') demand keyword; colloquial language demands vectors. Either alone fails half the queries."],
    ["Appliance scoping", "both branches filter by appliance (SQL WHERE / JSONB metadata) — a dishwasher question never surfaces fridge parts."],
  ];
  hs.forEach((pr, i) => {
    const y = 1.35 + i * 1.3;
    s.addText([{ text: pr[0] + " — ", options: { bold: true, fontSize: 12, color: TEAL_DARK } },
               { text: pr[1], options: { fontSize: 10.5, color: MUTED } }],
      { x: 6.2, y, w: 3.35, h: 1.25, fontFace: B, margin: 0 });
  });
  s.addShape(p.shapes.RECTANGLE, { x: 0.55, y: 4.55, w: 9.0, h: 0.62, fill: { color: INK } });
  s.addText([{ text: "Embeddings are env-swappable too: ", options: { bold: true, color: "FFFFFF", fontSize: 11.5 } },
             { text: "MOCK_EMBEDDINGS=1 uses a deterministic hashed bag-of-words — every vector code path testable with zero keys.", options: { color: "D9E6E5", fontSize: 11.5 } }],
    { x: 0.8, y: 4.6, w: 8.5, h: 0.52, fontFace: B, margin: 0, valign: "middle" });

  // ------------------------------------------------- 9 INTERFACE ENGINEERING
  s = p.addSlide(); s.background = { color: "FFFFFF" };
  title(s, "Interface engineering: the SSE contract", "The frontend is a renderer for a typed event stream — backend owns the vocabulary.");
  const evRows = [
    ["event", "payload", "renders as"],
    ["tool_start / tool_end", "{name, label}", "status pill with spinner (\"Checking compatibility…\")"],
    ["tool_error", "{name}", "pill fades; agent recovers conversationally — never a 500"],
    ["ui_block", "typed payloads ×6", "ProductCard · CompatResult · Diagnosis · InstallGuide …"],
    ["token", "{delta}", "validated prose, streamed with caret"],
    ["done", "{latency_ms}", "turn footer; powers the eval's latency metrics"],
  ];
  const tbl = [evRows[0].map((c) => ({ text: c, options: { bold: true, color: "FFFFFF", fill: { color: TEAL }, fontSize: 10.5 } }))]
    .concat(evRows.slice(1).map((r, i) => r.map((c, j) => ({ text: c, options: {
      fontSize: 9.5, fontFace: j === 0 ? M : B, color: j === 0 ? TEAL_DARK : MUTED, bold: j === 0,
      fill: { color: i % 2 ? PANEL : "FFFFFF" } } }))));
  s.addTable(tbl, { x: 0.55, y: 1.3, w: 5.6, colW: [1.55, 1.3, 2.75], border: { pt: 0.5, color: BORDER },
    fontFace: B, valign: "middle", rowH: 0.42, margin: 0.04 });
  const ie = [
    ["ui_block payloads are the FE/BE contract", "shapes defined once in tools.py, mirrored as JSDoc typedefs in lib/blocks.js — one source of truth, no drift."],
    ["Hand-rolled SSE parser", "fetch + ReadableStream with explicit buffering; unit tests split events mid-JSON and mid-event-name to prove reassembly."],
    ["Chat-native navigation", "block buttons emit templated user messages — product cards become conversation controls, no parallel routing system."],
    ["Resilience", "AbortController stop, retry-on-error message, graceful deflection rendering — error states are designed states."],
  ];
  ie.forEach((pr, i) => {
    const y = 1.3 + i * 1.0;
    s.addText([{ text: pr[0] + "  —  ", options: { bold: true, fontSize: 11, color: INK } },
               { text: pr[1], options: { fontSize: 10, color: MUTED } }],
      { x: 6.35, y, w: 3.2, h: 0.95, fontFace: B, margin: 0 });
  });
  s.addShape(p.shapes.RECTANGLE, { x: 0.55, y: 4.55, w: 5.6, h: 0.62, fill: { color: PANEL }, line: { color: BORDER, width: 0.75 } });
  s.addText("Container path keeps the contract: nginx proxies /chat with proxy_buffering off — tokens stream through Docker too.",
    { x: 0.75, y: 4.6, w: 5.25, h: 0.52, fontSize: 10.5, fontFace: B, color: MUTED, margin: 0, valign: "middle" });

  // ------------------------------------------------- 10 PHOTO OCR
  s = p.addSlide(); s.background = { color: "FFFFFF" };
  title(s, "Photo → model number, client-side", "Model stickers are hard to transcribe — so the composer accepts a photo of one.");
  const steps = ["photo / camera capture", "tesseract.js OCR (lazy chunk)", "extractModelNumber() heuristic", "smart prefill into composer"];
  steps.forEach((t, i) => {
    const x = 0.55 + i * 2.35;
    s.addShape(p.shapes.RECTANGLE, { x, y: 1.35, w: 2.1, h: 0.75, fill: { color: i === 2 ? TEAL : PANEL }, line: { color: i === 2 ? TEAL : BORDER, width: 1 }, shadow: shadow() });
    s.addText(t, { x: x + 0.05, y: 1.38, w: 2.0, h: 0.7, align: "center", fontSize: 10.5, bold: true,
      color: i === 2 ? "FFFFFF" : INK, fontFace: B, margin: 0, valign: "middle" });
    if (i < 3) s.addText("→", { x: x + 2.08, y: 1.5, w: 0.3, h: 0.4, align: "center", fontSize: 15, bold: true, color: TEAL, fontFace: B, margin: 0 });
  });
  code(s, 0.55, 2.4, 5.4, 2.75, [
    "// pure + unit-tested, separate from the OCR call",
    "tier(token):",
    "  reject: <5 or >16 chars · stopwords (MODEL,",
    "          SERIAL, brand names) · bare years · no digits",
    "  tier 1: long pure-numeric (>=9) — Kenmore style",
    "  tier 2: letters+digits mix — Whirlpool/GE style",
    "best = lowest tier, then longest token",
    "",
    "// smart prefill (ChatWindow):",
    "ps_in_history ? `Is part ${ps} compatible with",
    "                 my ${model}?`",
    "              : `My model number is ${model} ...`",
  ], 10);
  const oc = [
    ["Zero backend, zero keys", "OCR runs in the browser — no upload endpoint, no vision-API cost, photos never leave the device."],
    ["Bundle discipline", "tesseract.js (~3 MB) loads via dynamic import only when the camera button is used — first paint stays lean."],
    ["Testable core", "the extractor is a pure function: tier ranking, stopword/year rejection, and best-pick logic are Jest-tested without any OCR."],
    ["Context-aware handoff", "the detected model lands as an editable draft, phrased as a compat check if a part is already in the conversation."],
  ];
  oc.forEach((pr, i) => {
    const y = 2.4 + i * 0.72;
    s.addText([{ text: pr[0] + "  —  ", options: { bold: true, fontSize: 11, color: INK } },
               { text: pr[1], options: { fontSize: 10, color: MUTED } }],
      { x: 6.2, y, w: 3.35, h: 0.7, fontFace: B, margin: 0 });
  });

  // ------------------------------------------------- 11 EXTENSIBILITY & SCALE
  s = p.addSlide(); s.background = { color: "FFFFFF" };
  title(s, "Extensibility & scalability", "Extension points are proven, not promised — one tool was deleted with zero loop changes.");
  s.addShape(p.shapes.RECTANGLE, { x: 0.55, y: 1.3, w: 4.4, h: 3.9, fill: { color: PANEL }, line: { color: BORDER, width: 1 } });
  s.addText("Extension axes", { x: 0.8, y: 1.45, w: 3.9, h: 0.32, fontSize: 14, bold: true, fontFace: H, color: TEAL_DARK, margin: 0 });
  s.addText([
    { text: "Tools are registry entries: fn + Pydantic schema → JSON-schema export. Removing order_support touched the registry only — the loop, SSE protocol and UI never knew.", options: { bullet: true, breakLine: true } },
    { text: "New appliance = scraper seed URLs + one enum value; schema, agent and blocks are appliance-agnostic.", options: { bullet: true, breakLine: true } },
    { text: "LLM/embeddings swap via env (any OpenAI-compatible endpoint); MOCK implementations honor identical contracts.", options: { bullet: true, breakLine: true } },
    { text: "ui_block vocabulary is open: a new block type = one tool payload + one React component.", options: { bullet: true } },
  ], { x: 0.8, y: 1.85, w: 3.95, h: 3.25, fontSize: 10.5, fontFace: B, color: INK, paraSpaceAfter: 7, margin: 0, valign: "top" });
  s.addShape(p.shapes.RECTANGLE, { x: 5.15, y: 1.3, w: 4.4, h: 3.9, fill: { color: TEAL }, shadow: shadow() });
  s.addText("Scale path (deliberate order)", { x: 5.4, y: 1.45, w: 3.9, h: 0.32, fontSize: 14, bold: true, fontFace: H, color: "FFFFFF", margin: 0 });
  s.addText([
    { text: "API is stateless except one in-memory session dict behind an accessor → Redis is a one-class swap, then horizontal replicas behind the existing nginx.", options: { bullet: true, breakLine: true } },
    { text: "Postgres carries both workloads to ~1M embeddings (HNSW); read replicas for search; only then consider a dedicated vector store.", options: { bullet: true, breakLine: true } },
    { text: "Per-tool caching (compat verdicts are immutable per catalog version); guard fast-path already deletes most classifier traffic.", options: { bullet: true, breakLine: true } },
    { text: "Observability is structured now: request-id middleware + per-turn JSON logs (guard label, tools, latency) — OTel exporter, not a rewrite.", options: { bullet: true } },
  ], { x: 5.4, y: 1.85, w: 3.95, h: 3.25, fontSize: 10.5, fontFace: B, color: "EAF2F1", paraSpaceAfter: 7, margin: 0, valign: "top" });

  // ------------------------------------------------- 12 QUALITY + HANDOFF
  s = p.addSlide(); s.background = { color: TEAL };
  s.addText("Quality engineering — then the demo", { x: 0.55, y: 0.35, w: 8.9, h: 0.55, fontSize: 28, bold: true, fontFace: H, color: "FFFFFF", margin: 0 });
  s.addText("Evals measure whether the agent is right; tests measure whether the code is correct. Shipped as separate, automated layers.",
    { x: 0.55, y: 0.92, w: 8.9, h: 0.35, fontSize: 13, fontFace: B, color: "CFE2E1", margin: 0 });
  const q2 = [["91%", "backend coverage,\n80% CI gate"], ["20", "frontend Jest tests\n(blocks · SSE · OCR)"], ["40/40", "eval cases · 0 hallucinated\npart numbers"], ["4 jobs", "CI: lint · tests · e2e ·\nmanual eval (secrets)"]];
  q2.forEach((bs, i) => {
    const x = 0.55 + i * 2.3;
    s.addShape(p.shapes.RECTANGLE, { x, y: 1.55, w: 2.1, h: 1.45, fill: { color: TEAL_DARK } });
    s.addText(bs[0], { x, y: 1.7, w: 2.1, h: 0.6, align: "center", fontSize: 26, bold: true, color: i === 2 ? YELLOW : "FFFFFF", fontFace: H, margin: 0 });
    s.addText(bs[1], { x: x + 0.08, y: 2.35, w: 1.94, h: 0.6, align: "center", fontSize: 9.5, color: "CFE2E1", fontFace: B, margin: 0 });
  });
  s.addText([
    { text: "Eval mechanics: each case replays multi-turn conversations through the live SSE API in a fresh session; assertions cover tool selection, answer content, scope behavior, and a mechanical part-number check against tool results + catalog. One retry absorbs LLM nondeterminism — stated in the published methodology.", options: { breakLine: true, fontSize: 11.5, color: "FFFFFF" } },
    { text: "The harness has already paid for itself: it caught two real routing bugs during development.", options: { fontSize: 11.5, color: "CFE2E1" } },
  ], { x: 0.55, y: 3.25, w: 8.9, h: 1.0, fontFace: B, paraSpaceAfter: 6, margin: 0 });
  s.addShape(p.shapes.RECTANGLE, { x: 0.55, y: 4.5, w: 8.9, h: 0.75, fill: { color: YELLOW } });
  s.addText([{ text: "Now the live demo — watch for: ", options: { bold: true, color: INK, fontSize: 12.5 } },
             { text: "streaming tool pills · the photo-to-model OCR flow · an honest compatibility verdict · the fix-it journey ending in the cart.", options: { color: INK, fontSize: 12.5 } }],
    { x: 0.8, y: 4.56, w: 8.4, h: 0.64, fontFace: B, margin: 0, valign: "middle" });

  await p.writeFile({ fileName: "../PartSelect-Technical-Deck.pptx" });
  console.log("WROTE docs/PartSelect-Technical-Deck.pptx");
})().catch((e) => { console.error(e); process.exit(1); });
