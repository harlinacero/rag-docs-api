from app.rag import NO_ANSWER


def test_finds_the_right_document(service):
    result = service.ask("How long should access tokens live?")
    assert result.grounded
    assert result.sources[0]["doc_id"] == "jwt"
    # The keyword embedder may rank the neighbouring chunk first, so check that the
    # chunk with the actual answer is among the retrieved sources.
    assert any("fifteen minutes" in source["text"] for source in result.sources)


def test_finds_the_oauth_document(service):
    result = service.ask("What does OpenID Connect add on top of OAuth2?")
    assert result.grounded
    assert result.sources[0]["doc_id"] == "oauth"


def test_unrelated_question_is_not_answered(service):
    result = service.ask("What is the best recipe for chocolate cake?")
    assert not result.grounded
    assert result.answer == NO_ANSWER
    assert result.sources == []


def test_reingesting_replaces_the_document(service):
    before = len(service.store)
    service.ingest("jwt", "Completely new content about queues and topics.")
    assert len(service.store) < before
    result = service.ask("What is refresh token rotation?")
    assert all(s["doc_id"] != "jwt" for s in result.sources)


def test_empty_document_adds_nothing(service):
    before = len(service.store)
    assert service.ingest("empty", "   ") == 0
    assert len(service.store) == before
