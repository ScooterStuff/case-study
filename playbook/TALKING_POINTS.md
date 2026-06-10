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
