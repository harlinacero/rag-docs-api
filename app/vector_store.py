"""A small in-memory vector store with cosine similarity search."""
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class Hit:
    score: float
    meta: dict


class VectorStore:
    """Stores L2-normalised vectors, so cosine similarity is a dot product."""

    def __init__(self) -> None:
        self._vectors = np.empty((0, 0), dtype=np.float32)
        self._metas: list[dict] = []

    def __len__(self) -> int:
        return len(self._metas)

    def add(self, vectors: np.ndarray, metas: list[dict]) -> None:
        if len(vectors) != len(metas):
            raise ValueError("vectors and metas must have the same length")
        if len(metas) == 0:
            return
        if len(self) == 0:
            self._vectors = vectors.astype(np.float32)
        else:
            if vectors.shape[1] != self._vectors.shape[1]:
                raise ValueError("vector dimension does not match the store")
            self._vectors = np.vstack([self._vectors, vectors.astype(np.float32)])
        self._metas.extend(metas)

    def delete_document(self, doc_id: str) -> int:
        """Remove every chunk of ``doc_id``. Returns how many were removed."""
        keep = [i for i, meta in enumerate(self._metas) if meta["doc_id"] != doc_id]
        removed = len(self._metas) - len(keep)
        if removed:
            self._vectors = self._vectors[keep] if keep else np.empty((0, 0), dtype=np.float32)
            self._metas = [self._metas[i] for i in keep]
        return removed

    def search(self, query_vector: np.ndarray, top_k: int = 3) -> list[Hit]:
        if len(self) == 0:
            return []
        scores = self._vectors @ query_vector.astype(np.float32)
        order = np.argsort(scores)[::-1][:top_k]
        return [Hit(score=float(scores[i]), meta=self._metas[i]) for i in order]

    def save(self, directory: str | Path) -> None:
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        np.save(directory / "vectors.npy", self._vectors)
        (directory / "metas.json").write_text(json.dumps(self._metas), encoding="utf-8")

    @classmethod
    def load(cls, directory: str | Path) -> "VectorStore":
        directory = Path(directory)
        store = cls()
        store._vectors = np.load(directory / "vectors.npy")
        store._metas = json.loads((directory / "metas.json").read_text(encoding="utf-8"))
        return store
