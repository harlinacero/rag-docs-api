import numpy as np

from app.vector_store import VectorStore


def _store() -> VectorStore:
    store = VectorStore()
    vectors = np.array([[1, 0], [0, 1], [0.7071, 0.7071]], dtype=np.float32)
    metas = [
        {"doc_id": "a", "chunk_index": 0, "text": "x"},
        {"doc_id": "b", "chunk_index": 0, "text": "y"},
        {"doc_id": "b", "chunk_index": 1, "text": "z"},
    ]
    store.add(vectors, metas)
    return store


def test_search_orders_by_similarity():
    hits = _store().search(np.array([1, 0], dtype=np.float32), top_k=3)
    assert [h.meta["text"] for h in hits] == ["x", "z", "y"]
    assert hits[0].score > hits[1].score > hits[2].score


def test_search_on_empty_store():
    assert VectorStore().search(np.array([1, 0], dtype=np.float32)) == []


def test_delete_document_removes_all_its_chunks():
    store = _store()
    assert store.delete_document("b") == 2
    assert len(store) == 1
    assert store.delete_document("missing") == 0


def test_save_and_load_roundtrip(tmp_path):
    store = _store()
    store.save(tmp_path)
    loaded = VectorStore.load(tmp_path)
    query = np.array([0, 1], dtype=np.float32)
    assert [h.meta for h in loaded.search(query)] == [h.meta for h in store.search(query)]
