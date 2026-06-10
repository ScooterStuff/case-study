# TALKING_POINTS.md — running list for the Loom script

- The template repo really is a bare CRA skeleton with a stub `getAIMessage` — the
  whole agentic backend, data layer, and eval harness are net-new work.
- Kept the CRA scaffold instead of rewriting in Next.js: meeting the template where
  it is = lower-risk diff, and the architecture is identical behind the API contract.
- Template shipped ~10 unused heavy dependencies (langchain, antd, rsuite, ...);
  pruning them is itself a small story about dependency hygiene.
- The spec's own example part number PS11752778 is a *refrigerator door shelf bin*,
  not a dishwasher part — so spec query 2 is (probably deliberately) a trick:
  the correct answer is "not a verified fit for WDT780SAEM1", and an agent that
  says "yes" is hallucinating. Our compatibility tool answers from a SQL join, so
  it gets this right; eval has a regression case for it.
- Politeness engineering: sha1 on-disk cache, 2.5s delay, 600-page hard cap,
  re-runs are 100% cache hits (unit-tested with a stubbed transport).
- Compatibility rows carry provenance (`source: crossref | qna | model_page`) —
  Q&A-harvested fits are weaker signals than the official cross-reference table
  and the agent can say so.
- The whole data layer runs three ways with zero code changes: Docker pgvector
  (production/evaluator), pip-installed embedded Postgres (keyless tests anywhere),
  CI service container. Same schema, same SQL.
- check_compat returns a four-state enum with *evidence* (how many models the part
  is verified for, whether the model exists in our data at all) — the agent's
  honesty about partial data is engineered in the data layer, not prompted.
- The hallucination gate is mechanical, not vibes: regex-scan the final draft,
  any PS number not seen in this conversation's tool results (or typed by the
  user) triggers a retry-with-nudge, then strip-and-caveat. Every trigger is
  logged; the log being empty after the eval is a README stat.
- Buffer-and-release streaming: tool status events stream live, final prose is
  held ~100ms for the hallucination check - invisible to users, but it means an
  invented part number can never reach the screen.
- MOCK_LLM mode = a scripted, tool-faithful router. CI, docker demo, and e2e run
  with zero API keys - the eval proves the real model, the mock proves the rails.
- The eval found real bugs before any human did: the mock router read the
  *system prompt* as conversation history (it contains the word "dishwasher",
  so out-of-scope messages got diagnosed as dishwasher problems), and a missing
  \bfits?\b pattern broke three compatibility routings. Eval-driven debugging
  in action - exactly the story the harness is meant to tell.
- ground_03 ("just guess whether it fits - yes or no?") is my favorite case:
  the agent refuses to guess and gives the honest verified-list answer.
- The backend container self-heals on first boot: entrypoint probes the schema
  and restores the committed seed if missing - evaluators never run a scraper
  or need an embedding key just to start the app.
- nginx proxies /chat with proxy_buffering off - SSE tokens stream through the
  container path too, not just in dev.
- Fresh-clone proof: `git clone` to a temp dir + pip install + pytest = fully
  green with zero network/API dependencies - the committed seed and datasets
  carry everything.
- The README's limitations section is deliberate seniority signaling: partial
  cross-reference data, mock orders, 34-part slice - each named, each with the
  mitigation already in the code.
