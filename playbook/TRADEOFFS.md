# TRADEOFFS.md — decision log

## D1 — One PostgreSQL 16 + pgvector for facts AND vectors
**Decision.** A single Postgres (Docker image `pgvector/pgvector:pg16`) holds the
relational source of truth (parts, prices, stock, compatibility) and the semantic
index (one `embeddings` table, three logical collections), plus tsvector keyword
search.
**Alternatives.** SQLite + Chroma (simplest), dedicated vector DB (Pinecone/Qdrant),
Elasticsearch hybrid.
**Why.** Vector hits JOIN prices/stock/compatibility *in-database* — one engine,
one backup, one `docker compose up`; production-realistic; the facts/semantics
split is the architecture pillar and is visible in one schema file.
**Given up.** SQLite's zero-dependency setup; a managed vector DB's scaling story.
**Mitigation found during build.** The sandbox had no Docker — `pgserver` (pip)
provides an embedded Postgres 16.2 *with pgvector* for keyless local tests, so the
test suite runs anywhere; CI/evaluator use the Docker image. Seed restore is a
`pg_dump --inserts` script executable through psycopg alone (no psql required).
**Revisit when.** Catalog grows past ~1M embeddings (HNSW build times) or
multi-tenant isolation is needed.

## D2 — Raw parameterized SQL via psycopg3, no ORM
**Decision.** `backend/app/retrieval.py` is ~10 hand-written SQL queries.
**Alternatives.** SQLAlchemy (core or ORM), SQLModel.
**Why.** The queries ARE the architecture demo (compatibility is literally a JOIN;
hybrid search is two queries + RRF in 10 lines). An ORM would hide exactly the
thing the case study needs to show, and adds a dependency for 10 queries.
**Given up.** Migrations tooling, model validation on rows (mitigated: pydantic
models at the tool boundary in Phase 3).
**Revisit when.** Schema churn or query count grows ~3x.

## D3 — Two-mode embeddings (real API / deterministic mock)
**Decision.** `MOCK_EMBEDDINGS=1` swaps the OpenAI-compatible embedding API for a
deterministic hashed bag-of-words vector (same dims, L2-normalized).
**Why.** Tests and CI run with zero keys; cosine over token-hash vectors gives
keyword-overlap behavior good enough to exercise every vector code path.
**Given up.** Mock vectors are NOT semantic; the committed seed must be rebuilt
with real embeddings before submission (tracked in DEVIATIONS #15).
