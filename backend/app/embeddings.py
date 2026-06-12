"""Embedding client: OpenAI-compatible API, or a deterministic mock.

MOCK_EMBEDDINGS=1 produces hashed bag-of-words vectors (token overlap ~ cosine
similarity). It exists so tests/CI run with zero keys - it is NOT a quality
substitute; the committed seed dump is built with real embeddings.
"""

from __future__ import annotations

import hashlib
import math
import re
from functools import lru_cache

from backend.app import config


def _mock_embed(text: str, dims: int) -> list[float]:
    vec = [0.0] * dims
    for token in re.findall(r"[a-z0-9]+", text.lower()):
        bucket = int(hashlib.md5(token.encode(), usedforsecurity=False).hexdigest(), 16) % dims
        vec[bucket] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def embed_batch(texts: list[str]) -> list[list[float]]:
    if config.settings.mock_embeddings:
        return [_mock_embed(t, config.settings.embedding_dims) for t in texts]
    from openai import OpenAI  # lazy: not needed in mock mode

    client = OpenAI(base_url=config.settings.llm_base_url, api_key=config.settings.effective_embedding_key)
    out: list[list[float]] = []
    for i in range(0, len(texts), 100):
        resp = client.embeddings.create(model=config.settings.embedding_model, input=texts[i : i + 100])
        out += [d.embedding for d in resp.data]
    return out


@lru_cache(maxsize=1024)
def _embed_one_cached(text: str, model: str, mock: bool) -> tuple[float, ...]:
    # Cache key includes model + mock flag so swapping either invalidates entries.
    # Tuple return type is hashable + immutable; callers wrap back to list.
    return tuple(embed_batch([text])[0])


def embed_one(text: str) -> list[float]:
    """Single-text embed with an LRU cache (1024 distinct queries).

    Only used for *query-time* embedding (retrieval.py); ingest goes through
    embed_batch directly so unique docs never thrash the cache.
    """
    return list(
        _embed_one_cached(
            text,
            config.settings.embedding_model,
            config.settings.mock_embeddings,
        )
    )
