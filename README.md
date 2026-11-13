# Ask My Docs: a small RAG API with FastAPI

[![CI](https://github.com/harlinacero/rag-docs-api/actions/workflows/ci.yml/badge.svg)](https://github.com/harlinacero/rag-docs-api/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A minimal retrieval-augmented generation (RAG) service. You upload documents, ask questions, and get answers **grounded in those documents**, with the sources that support each answer.

It is a learning and portfolio project: small enough to read in an afternoon, with the same building blocks a production RAG system has.

## How it works

```
POST /documents            POST /ask
      |                        |
   chunking                 embed question
      |                        |
   embeddings  ---->  vector store (cosine similarity)
                               |
                  keep chunks above a similarity threshold
                               |
              none?  --> "I don't know" (no generation)
              some?  --> generator answers from those chunks only
                               |
                       answer + sources + grounded flag
```

| Module | Responsibility |
| --- | --- |
| `app/chunking.py` | Overlapping word chunks, so a sentence cut at a boundary survives in one chunk |
| `app/embeddings.py` | `HashingEmbedder` (local, offline) and `OpenAIEmbedder` (semantic) behind one interface |
| `app/vector_store.py` | NumPy cosine-similarity search, delete by document, save/load |
| `app/llm.py` | `ExtractiveGenerator` (no LLM) and `OpenAIGenerator`, behind one interface |
| `app/rag.py` | The pipeline: ingest, retrieve, guard, generate |
| `app/main.py` | FastAPI endpoints with validated request and response models |

## Run it

Requires Python 3.12 (as in CI and Docker). Step-by-step guides in Spanish, including Windows commands and sequence diagrams, are in [`docs/`](docs/).

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs, add a document and ask a question:

```bash
curl -X POST localhost:8000/documents -H 'content-type: application/json' \
  -d "{\"doc_id\": \"jwt\", \"text\": \"$(cat data/jwt.md | tr '\n' ' ')\"}"

curl -X POST localhost:8000/ask -H 'content-type: application/json' \
  -d '{"question": "How long should access tokens live?"}'
```

With Docker: `docker build -t ask-my-docs . && docker run -p 8000:8000 ask-my-docs`.

### Using real embeddings and an LLM

By default everything runs offline. To use OpenAI:

```bash
pip install -r requirements-openai.txt
export OPENAI_API_KEY=...
export EMBEDDER=openai GENERATOR=openai
export MIN_SCORE=0.30   # similarity scores are not comparable across embedders: tune it
uvicorn app.main:app
```

| Variable | Default | Meaning |
| --- | --- | --- |
| `EMBEDDER` | `hashing` | `hashing` or `openai` |
| `GENERATOR` | `extractive` | `extractive` or `openai` |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | `120` / `20` | Words per chunk and shared words |
| `MIN_SCORE` | `0.15` | Minimum cosine similarity to use a chunk |

## Design decisions

- **Interfaces, not vendors.** `Embedder` and `Generator` are small protocols. Swapping the offline implementation for OpenAI, or for another provider, is a config change, and tests never need the network.
- **Deterministic offline embedder.** It uses `md5` instead of Python's `hash()`, which changes between runs, so tests are reproducible.
- **Normalised vectors.** Cosine similarity becomes a single matrix product.
- **Dependency injection.** The service is provided through FastAPI's `Depends`, so tests replace it with `app.dependency_overrides`.
- **Idempotent ingest.** Re-posting the same `doc_id` replaces the document instead of duplicating chunks.

## Responsible-AI guardrails

- **No context, no answer.** If no chunk reaches the similarity threshold, the service returns "I don't know" and never calls the generator. This reduces hallucination.
- **Grounded answers.** The OpenAI prompt allows answers only from the retrieved context and asks for citations. Every response includes the sources and a `grounded` flag so a human can verify.
- **Context is data.** The system prompt tells the model to ignore instructions found inside documents, a basic defence against prompt injection. It is not a complete one.
- **Bounded inputs.** Request sizes and `top_k` are validated.

## Known limitations

- The offline embedder matches **words, not meaning**. A question phrased with different words than the document can miss, and a neighbouring chunk can rank first. That is why the OpenAI embedder exists, and why one test checks that the answering chunk is *among* the sources rather than first.
- The store is in memory and single-process. State is lost on restart unless you call `VectorStore.save`.
- No authentication, rate limiting or per-user document isolation.
- No evaluation set yet to measure retrieval quality.
- The OpenAI classes are thin wrappers that I have not covered with automated tests, because tests must run offline.

## Ideas for next steps

1. Replace the in-memory store with PostgreSQL + pgvector.
2. Add a small evaluation set (questions with expected sources) and report hit rate at k.
3. Add hybrid search (BM25 + embeddings) and a re-ranker.
4. Stream answers, add authentication and per-tenant isolation.
5. Add structured logging without storing document text or personal data.

## License

[MIT](LICENSE)
