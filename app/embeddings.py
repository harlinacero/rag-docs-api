"""Embedders turn text into vectors.

``HashingEmbedder`` runs locally with no network, so tests and demos work
offline. It captures word overlap, not meaning. ``OpenAIEmbedder`` captures
meaning and is the one to use for real data.
"""
import hashlib
import re
from typing import Protocol

import numpy as np

_TOKEN = re.compile(r"[a-z0-9]+")
_STOPWORDS = frozenset(
    "a an and are as at be by for from how in is it of on or that the this to was what when which with".split()
)


class Embedder(Protocol):
    def embed(self, texts: list[str]) -> np.ndarray:
        """Return an array of shape (len(texts), dim) with L2-normalised rows."""


def _normalise(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


class HashingEmbedder:
    """Bag-of-words embedder using the hashing trick (deterministic, offline)."""

    def __init__(self, dim: int = 512) -> None:
        self.dim = dim

    def _bucket(self, token: str) -> int:
        # md5 instead of hash(): Python's hash() changes between runs.
        digest = hashlib.md5(token.encode("utf-8")).digest()
        return int.from_bytes(digest[:4], "little") % self.dim

    def embed(self, texts: list[str]) -> np.ndarray:
        matrix = np.zeros((len(texts), self.dim), dtype=np.float32)
        for row, text in enumerate(texts):
            for token in _TOKEN.findall(text.lower()):
                if token in _STOPWORDS:
                    continue
                matrix[row, self._bucket(token)] += 1.0
        return _normalise(matrix)


class OpenAIEmbedder:
    """Embeddings from the OpenAI API (needs ``pip install openai`` and OPENAI_API_KEY)."""

    def __init__(self, model: str = "text-embedding-3-small") -> None:
        from openai import OpenAI  # imported lazily so the package stays optional

        self._client = OpenAI()
        self._model = model

    def embed(self, texts: list[str]) -> np.ndarray:
        response = self._client.embeddings.create(model=self._model, input=texts)
        matrix = np.array([item.embedding for item in response.data], dtype=np.float32)
        return _normalise(matrix)
