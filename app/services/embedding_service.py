"""
Embedding service — turns text into vectors via the OpenAI embeddings API.

All RAG features degrade gracefully when OPENAI_API_KEY is not configured:
callers must catch EmbeddingUnavailable and fall back to non-AI behaviour.
"""
from typing import List

from app.core.config import settings


class EmbeddingUnavailable(Exception):
    """Raised when embeddings cannot be produced (no key, API error, timeout)."""


_client = None


def is_configured() -> bool:
    return bool(settings.OPENAI_API_KEY)


def _get_client():
    global _client
    if _client is None:
        if not is_configured():
            raise EmbeddingUnavailable("OPENAI_API_KEY is not configured")
        from openai import OpenAI
        _client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=20.0, max_retries=1)
    return _client


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Embed many texts (batched). Order of results matches input order."""
    client = _get_client()
    vectors: List[List[float]] = []
    batch_size = 100
    try:
        for start in range(0, len(texts), batch_size):
            batch = texts[start:start + batch_size]
            response = client.embeddings.create(
                model=settings.EMBEDDING_MODEL,
                input=batch,
                dimensions=settings.EMBEDDING_DIMENSIONS,
            )
            vectors.extend(item.embedding for item in response.data)
    except EmbeddingUnavailable:
        raise
    except Exception as e:
        raise EmbeddingUnavailable(f"Embedding API call failed: {e}") from e
    return vectors


def embed_query(text: str) -> List[float]:
    return embed_texts([text])[0]
