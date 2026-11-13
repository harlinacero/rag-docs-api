from pathlib import Path

import pytest

from app.embeddings import HashingEmbedder
from app.llm import ExtractiveGenerator
from app.rag import RagService

DATA = Path(__file__).parent.parent / "data"


@pytest.fixture
def service() -> RagService:
    svc = RagService(HashingEmbedder(), ExtractiveGenerator(), chunk_size=40, overlap=5)
    for path in sorted(DATA.glob("*.md")):
        svc.ingest(path.stem, path.read_text(encoding="utf-8"))
    return svc
