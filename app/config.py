"""Configuration from environment variables, with offline-friendly defaults."""
import os

from app.embeddings import HashingEmbedder, OpenAIEmbedder
from app.llm import ExtractiveGenerator, OpenAIGenerator
from app.rag import RagService


def build_service() -> RagService:
    embedder_name = os.getenv("EMBEDDER", "hashing")
    generator_name = os.getenv("GENERATOR", "extractive")

    embedder = OpenAIEmbedder() if embedder_name == "openai" else HashingEmbedder()
    generator = OpenAIGenerator() if generator_name == "openai" else ExtractiveGenerator()

    return RagService(
        embedder=embedder,
        generator=generator,
        chunk_size=int(os.getenv("CHUNK_SIZE", "120")),
        overlap=int(os.getenv("CHUNK_OVERLAP", "20")),
        # Cosine scores are not comparable across embedders: tune this per embedder.
        min_score=float(os.getenv("MIN_SCORE", "0.15")),
    )
