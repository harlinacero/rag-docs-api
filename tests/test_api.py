import pytest

pytest.importorskip("httpx")  # TestClient needs httpx

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app, get_service  # noqa: E402


@pytest.fixture
def client(service):
    app.dependency_overrides[get_service] = lambda: service
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_add_document_then_ask(client):
    created = client.post("/documents", json={"doc_id": "kafka", "text": "Kafka stores events in partitioned logs that consumers read at their own pace."})
    assert created.status_code == 201
    assert created.json()["chunks"] == 1

    response = client.post("/ask", json={"question": "How do Kafka consumers read events?"})
    body = response.json()
    assert response.status_code == 200
    assert body["grounded"] is True
    assert body["sources"][0]["doc_id"] == "kafka"


def test_unanswerable_question(client):
    body = client.post("/ask", json={"question": "Best recipe for chocolate cake?"}).json()
    assert body["grounded"] is False
    assert body["sources"] == []


def test_validation_errors(client):
    assert client.post("/ask", json={"question": ""}).status_code == 422
    assert client.post("/ask", json={"question": "x", "top_k": 99}).status_code == 422
    assert client.post("/documents", json={"doc_id": "", "text": "x"}).status_code == 422
