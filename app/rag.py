"""The RAG pipeline: chunk -> embed -> store -> retrieve -> generate."""
from dataclasses import dataclass

from app.chunking import chunk_text
from app.embeddings import Embedder
from app.llm import Generator
from app.vector_store import VectorStore

NO_ANSWER = "I don't know based on the provided documents."


@dataclass
class Answer:
    answer: str
    grounded: bool
    sources: list[dict]


class RagService:
    def __init__(
        self,
        embedder: Embedder,
        generator: Generator,
        store: VectorStore | None = None,
        chunk_size: int = 120,
        overlap: int = 20,
        min_score: float = 0.15,
    ) -> None:
        self.embedder = embedder
        self.generator = generator
        self.store = store or VectorStore()
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.min_score = min_score

    def ingest(self, doc_id: str, text: str) -> int:
        """Index a document. Re-ingesting the same ``doc_id`` replaces it."""
        chunks = chunk_text(text, self.chunk_size, self.overlap)
        self.store.delete_document(doc_id)
        if not chunks:
            return 0
        vectors = self.embedder.embed(chunks)
        metas = [
            {"doc_id": doc_id, "chunk_index": i, "text": chunk}
            for i, chunk in enumerate(chunks)
        ]
        self.store.add(vectors, metas)
        return len(chunks)

    def ask(self, question: str, top_k: int = 3) -> Answer:
        query_vector = self.embedder.embed([question])[0]
        hits = self.store.search(query_vector, top_k)
        relevant = [h for h in hits if h.score >= self.min_score]

        # Guard against hallucination: with no relevant context, do not call the generator.
        if not relevant:
            return Answer(answer=NO_ANSWER, grounded=False, sources=[])

        sources = [{**h.meta, "score": round(h.score, 4)} for h in relevant]
        answer = self.generator.generate(question, sources)
        return Answer(answer=answer, grounded=True, sources=sources)
