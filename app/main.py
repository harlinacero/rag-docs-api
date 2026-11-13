"""HTTP API for the RAG service."""
from functools import lru_cache

from fastapi import Depends, FastAPI
from pydantic import BaseModel, Field

from app.config import build_service
from app.rag import RagService

app = FastAPI(title="Ask My Docs", version="0.1.0")


@lru_cache
def get_service() -> RagService:
    return build_service()


class DocumentIn(BaseModel):
    doc_id: str = Field(min_length=1, max_length=200)
    text: str = Field(min_length=1, max_length=200_000)


class DocumentOut(BaseModel):
    doc_id: str
    chunks: int


class QuestionIn(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    top_k: int = Field(default=3, ge=1, le=10)


class SourceOut(BaseModel):
    doc_id: str
    chunk_index: int
    score: float
    text: str


class AnswerOut(BaseModel):
    answer: str
    grounded: bool
    sources: list[SourceOut]


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/documents", response_model=DocumentOut, status_code=201)
def add_document(body: DocumentIn, service: RagService = Depends(get_service)) -> DocumentOut:
    chunks = service.ingest(body.doc_id, body.text)
    return DocumentOut(doc_id=body.doc_id, chunks=chunks)


@app.post("/ask", response_model=AnswerOut)
def ask(body: QuestionIn, service: RagService = Depends(get_service)) -> AnswerOut:
    result = service.ask(body.question, body.top_k)
    return AnswerOut(answer=result.answer, grounded=result.grounded, sources=result.sources)
