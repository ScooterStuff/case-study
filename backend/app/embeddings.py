"""Embedding client: OpenAI-compatible API, or a deterministic mock.

MOCK_EMBEDDINGS=1 produces hashed bag-of-words vectors (token overlap ~ cosine
similarity). It exists so tests/CI run with zero keys - it is NOT a quality
substitute; the committed seed dump is built with real embeddings.
"""
from __future__ import annotations

import hashlib
import math
import re

from backend.app.config import settings


def _mock_embed(text: str, dims: int) -> list[float]:
    vec = [0.0] * dims
    for token in re.findall(r"[a-z0-9]+", text.lower()):
        bucket = int(hashlib.md5(token.encode()).hexdigest(), 16) % dims
        vec[bucket] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def embed_batch(texts: list[str]) -> list[list[float]]:
    if settings.mock_embeddings:
        return [_mock_embed(t, settings.embedding_dims) for t in texts]
    from openai import OpenAI  # lazy: not needed in mock mode

    client = OpenAI(base_url=settings.llm_base_url, api_key=settings.effective_embedding_key)
    out: list[list[float]] = []
    for i in range(0, len(texts), 100):
        resp = client.embeddings.create(model=settings.embedding_model, input=texts[i:i + 100])
        out += [d.embedding for d in resp.data]
    return out


def embed_one(text: str) -> list[float]:
    return embed_batch([text])[0]
