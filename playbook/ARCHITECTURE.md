# ARCHITECTURE.md — System Diagram

This Mermaid diagram is the canonical architecture picture. Embed it verbatim
in the README (§Architecture) — GitHub renders Mermaid natively. Keep it in
sync if the design changes; this file is the single source of truth.

```mermaid
flowchart LR
    subgraph CLIENT["Frontend — React (CRA template, adapted)"]
        UI["Chat UI<br/>streaming + rich blocks"]
        BLOCKS["UI Blocks<br/>ProductCard · CompatResult ·<br/>Diagnosis · InstallGuide ·<br/>OrderStatus · Cart"]
        UI --- BLOCKS
    end

    subgraph API["Backend — FastAPI"]
        SSE["POST /chat (SSE)<br/>request_id middleware"]
        GUARD["Scope Guard<br/>keyword fast-path →<br/>cheap LLM classifier"]
        AGENT["Agent Loop<br/>single LLM, tool calling,<br/>max 4 iterations"]
        VAL["Hallucination Validator<br/>every PS# must come<br/>from tool results"]
        SSE --> GUARD --> AGENT --> VAL --> SSE
    end

    subgraph TOOLS["Tool Registry (extension point)"]
        T1["search_parts"]
        T2["get_part_details"]
        T3["check_compatibility"]
        T4["diagnose_issue"]
        T5["get_installation_guide"]
        T6["order_support (mock →<br/>ERP/OMS in production)"]
    end

    subgraph DATA["Postgres 16 + pgvector (one database)"]
        SQL[("Relational tables + tsvector<br/>FACTS — deterministic:<br/>parts · prices · stock ·<br/>compatibility · replaces")]
        VEC[("embeddings table (pgvector)<br/>SEMANTICS — RAG:<br/>repair causes · part docs ·<br/>Q&A + repair stories")]
    end

    subgraph PIPELINE["Offline Pipeline"]
        SCRAPER["Polite cached scraper<br/>partselect.com slice"]
        INGEST["ingest.py<br/>--rebuild: normalize + embed<br/>--load-seed: restore dump"]
        SCRAPER --> INGEST
    end

    LLM["LLM Provider<br/>OpenAI-compatible,<br/>3 env vars to swap"]

    UI -- "SSE: tokens · tool status · ui_blocks" --> SSE
    AGENT <--> LLM
    AGENT --> TOOLS
    T1 & T2 & T3 & T5 --> SQL
    T1 & T4 --> VEC
    T4 --> SQL
    INGEST --> SQL
    INGEST --> VEC

    style SQL fill:#337778,color:#fff
    style VEC fill:#f3c04c,color:#121212
    style VAL fill:#f4364c,color:#fff
    style GUARD fill:#f6f6f4,stroke:#337778
```

## The one-paragraph narration (reuse in README)

A user message first hits the **scope guard** (keyword fast-path, then a cheap
classifier only when needed — latency matters). In-scope messages go to a
**single tool-calling agent**: facts that must never be wrong (prices, stock,
compatibility) are answered from **relational tables via deterministic SQL**, while
fuzzy natural language (symptoms, "the thing that sprays water") is answered
via **RAG over pgvector embeddings in the same database** — which also lets semantic hits JOIN prices and stock in one query. Every tool can attach a **ui_block**, which the
frontend renders as a rich component mid-stream. Before the final answer
flushes, a **validator** rejects any part number that didn't come from a tool
result. The tool registry is the extension point: a new appliance is new data
plus an enum value; real order support is the same `order_support` schema with
an ERP client behind it.

## Sequence (compatibility check, the deterministic path)

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant G as Guard
    participant A as Agent
    participant T as check_compatibility
    participant DB as Postgres

    U->>F: "Is this part compatible with my WDT780SAEM1?"
    F->>G: POST /chat (SSE open)
    G->>A: in_scope (fast-path)
    A->>A: resolve "this part" = PS11752778 from history
    A->>T: check_compatibility(PS11752778, WDT780SAEM1)
    F-->>U: tool pill: "Checking compatibility…"
    T->>DB: SELECT … FROM compatibility WHERE …
    DB-->>T: no_match_found + evidence (fridge part vs dishwasher model)
    T-->>A: result + compat_result ui_block
    F-->>U: ⚠ CompatResult block renders (honest "not in verified list")
    A->>A: honest draft → validator: PS11752778 ∈ tool results ✓
    A-->>F: streamed tokens → done
```
