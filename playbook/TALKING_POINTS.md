# TALKING_POINTS.md — running list for the Loom script

- The template repo really is a bare CRA skeleton with a stub `getAIMessage` — the
  whole agentic backend, data layer, and eval harness are net-new work.
- Kept the CRA scaffold instead of rewriting in Next.js: meeting the template where
  it is = lower-risk diff, and the architecture is identical behind the API contract.
- Template shipped ~10 unused heavy dependencies (langchain, antd, rsuite, ...);
  pruning them is itself a small story about dependency hygiene.
