# 02_data_layer.md — Hybrid Data Layer (Postgres facts + pgvector semantics)

## Objective
One PostgreSQL 16 database (run via Docker) serving BOTH retrieval substrates,
filled by `backend/ingest.py`:

1. **Relational tables** — the source of truth for facts: parts, prices, stock,
   compatibility. Queries here are deterministic.
2. **pgvector columns/tables** — semantic index over repair guides, part
   descriptions, Q&A, and repair stories. Queries here are fuzzy (RAG).

This split is the architectural centerpiece: **anything that can be
hallucinated dangerously lives in relational queries; anything that benefits
from semantic matching lives in vectors.** One engine for both is a deliberate
trade-off (vs SQLite+Chroma) — record the reasoning in
`playbook/TRADEOFFS.md` (entry D1 already drafted; refine it if reality
differs).

## Database bring-up (needed now, before Phase 8 formalizes compose)
Add a minimal `docker-compose.yml` at repo root with just the db service:
```yaml
services:
  db:
    image: pgvector/pgvector:pg16
    environment: [POSTGRES_USER=ps, POSTGRES_PASSWORD=ps, POSTGRES_DB=partselect]
    ports: ["5432:5432"]
    volumes: [pgdata:/var/lib/postgresql/data]
    healthcheck: {test: ["CMD-SHELL","pg_isready -U ps -d partselect"], interval: 5s, retries: 10}
volumes: {pgdata: {}}
```
`DATABASE_URL=postgresql://ps:ps@localhost:5432/partselect` goes in
`.env.example`. Python driver: `psycopg[binary]` (psycopg3) + `pgvector`
package. Keep raw SQL in `retrieval.py` (no ORM — a deliberate trade-off:
the queries ARE the architecture demonstration; log in TRADEOFFS.md).

## Schema (`backend/ingest.py` creates it; idempotent, transactional)

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE parts (
  ps_number      TEXT PRIMARY KEY,          -- 'PS3406971' (normalized upper)
  mpn            TEXT NOT NULL,             -- 'W10195416'
  brand          TEXT NOT NULL,
  title          TEXT NOT NULL,
  appliance_type TEXT NOT NULL CHECK (appliance_type IN ('refrigerator','dishwasher')),
  price          NUMERIC(10,2),
  currency       TEXT DEFAULT 'USD',
  availability   TEXT,
  description    TEXT,
  install_difficulty TEXT,                  -- modal value from repair stories
  install_time   TEXT,
  avg_repair_rating REAL,
  repair_rating_count INTEGER,
  rating         REAL,
  review_count   INTEGER,
  image_url      TEXT,
  product_url    TEXT NOT NULL,
  video_url      TEXT,
  search_tsv     tsvector GENERATED ALWAYS AS (
                   to_tsvector('english', coalesce(title,'') || ' ' ||
                   coalesce(mpn,'') || ' ' || coalesce(description,''))) STORED
);
CREATE INDEX idx_parts_tsv ON parts USING GIN (search_tsv);

CREATE TABLE part_symptoms (
  ps_number TEXT REFERENCES parts(ps_number),
  symptom   TEXT NOT NULL
);
CREATE INDEX idx_symptom ON part_symptoms(symptom);

CREATE TABLE part_replaces (
  ps_number TEXT REFERENCES parts(ps_number),
  old_mpn   TEXT NOT NULL
);
CREATE INDEX idx_old_mpn ON part_replaces(old_mpn);

CREATE TABLE compatibility (
  ps_number    TEXT REFERENCES parts(ps_number),
  brand        TEXT,
  model_number TEXT NOT NULL,               -- normalized upper
  model_desc   TEXT,
  source       TEXT DEFAULT 'cross_ref',    -- 'cross_ref' | 'model_page' | 'qna'
  PRIMARY KEY (ps_number, model_number)
);
CREATE INDEX idx_model ON compatibility(model_number);

CREATE TABLE repair_guides (
  id        SERIAL PRIMARY KEY,
  appliance TEXT NOT NULL,
  symptom   TEXT NOT NULL,
  url       TEXT
);

CREATE TABLE repair_causes (
  guide_id  INTEGER REFERENCES repair_guides(id),
  rank      INTEGER,
  cause     TEXT NOT NULL,
  body      TEXT NOT NULL,
  part_types TEXT
);

-- Vector side: one embeddings table, three logical collections
CREATE TABLE embeddings (
  id         SERIAL PRIMARY KEY,
  collection TEXT NOT NULL CHECK (collection IN ('repair_chunks','part_docs','support_snippets')),
  document   TEXT NOT NULL,
  metadata   JSONB NOT NULL,                -- ps_number / appliance / symptom / rank / kind ...
  embedding  vector(1536)                   -- text-embedding-3-small dims; keep in sync w/ env
);
CREATE INDEX idx_emb_collection ON embeddings(collection);
CREATE INDEX idx_emb_hnsw ON embeddings USING hnsw (embedding vector_cosine_ops);
```

## Vector collections (same content plan as before)

| Collection | Documents | Metadata |
|---|---|---|
| `repair_chunks` | each repair **cause** = one chunk: `"{appliance} — {symptom} — cause {rank}: {cause}\n{body}"` | appliance, symptom, rank, guide_id, part_types |
| `part_docs` | per part: `"{title} ({ps_number} / {mpn}) by {brand}. Fixes: {symptoms}. {description}"` | ps_number, appliance_type, brand |
| `support_snippets` | Q&A pairs + top repair stories (real customer language — matches colloquial queries) | ps_number, kind: 'qna'\|'story' |

Chunking: causes are natural chunks (split on paragraphs w/ 100-char overlap
only if >1,200 chars). Part docs: one chunk, description truncated at 1,500.

## Seed strategy (so the evaluator never needs an embedding key)
`ingest.py` has two modes:
- `--rebuild` — JSON → tables → embed via API → upsert vectors (needs key;
  batch 100; print cost estimate, expect < $0.10).
- `--load-seed` (default if `backend/data/seed.sql.gz` exists) — restore a
  committed `pg_dump` that INCLUDES the embeddings table. After every
  successful `--rebuild`, regenerate the dump:
  `pg_dump --no-owner -Z6 -f backend/data/seed.sql.gz $DATABASE_URL`.
Commit `seed.sql.gz` + the JSON datasets. README quickstart uses seed mode.

## `backend/app/retrieval.py` — the query API (pure functions, no LLM here)

```python
def get_part(ps_or_mpn: str) -> Part | None            # exact; checks part_replaces too
def check_compat(ps_number: str, model: str) -> CompatResult
#  'verified_fit' | 'no_match_found' | 'unknown_model' | 'unknown_part'
#  + evidence: total model count for the part, sample models, source
def parts_for_model(model: str, symptom: str | None) -> list[Part]
def keyword_search(q: str, appliance: str | None) -> list[Part]      # tsvector
def vector_search_parts(q: str, appliance: str | None, k=8) -> list[Part]
def hybrid_search(q, appliance) -> list[Part]           # RRF-merge keyword+vector
def search_repairs(symptom_text: str, appliance: str, k=6) -> list[RepairChunk]
def search_support(q: str, ps_number: str | None, k=4) -> list[Snippet]
```
Vector queries: cosine distance via pgvector `ORDER BY embedding <=> %s LIMIT k`
with a `collection = X` filter (and JSONB metadata filters for appliance).

`check_compat` semantics matter — be honest about data limits: scraped
cross-reference tables are partial (pagination), so 'no_match_found' must be
phrased downstream as "not in our verified compatibility list — let's
double-check" rather than a hard "incompatible". Encode that nuance in the
result enum, not in prompt vibes.

## Acceptance checks
- [ ] `docker compose up -d db` healthy; `CREATE EXTENSION vector` succeeded
- [ ] `python backend/ingest.py --rebuild` completes; prints row counts + cost
- [ ] `psql $DATABASE_URL -c 'select count(*) from parts;'` ≥ 150
- [ ] `seed.sql.gz` generated; fresh db + `--load-seed` reproduces counts
      WITHOUT any embedding API call
- [ ] `get_part('PS11752778')` returns the door balance link kit
- [ ] `check_compat('PS11752778','WDT780SAEM1')` → `verified_fit`
- [ ] `check_compat('PS11752778','FAKE123')` → `unknown_model` (graceful)
- [ ] `search_repairs('ice maker not making ice','refrigerator')` top result is
      the ice-maker guide, causes in rank order
- [ ] `hybrid_search('thing that sprays water bottom of dishwasher')` returns a
      lower spray arm in top 3
- [ ] `tests/test_retrieval.py` encodes all of the above as pytest
- [ ] TRADEOFFS.md entries D1 (Postgres+pgvector) and D2 (raw SQL, no ORM)
      reviewed/updated against what was actually built
- [ ] `git commit -m "feat(data): postgres+pgvector hybrid data layer"`
