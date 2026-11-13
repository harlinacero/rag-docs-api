import pytest

from app.chunking import chunk_text


def test_empty_text_gives_no_chunks():
    assert chunk_text("   ") == []


def test_short_text_is_a_single_chunk():
    assert chunk_text("one two three", chunk_size=10, overlap=2) == ["one two three"]


def test_chunks_overlap():
    words = [f"w{i}" for i in range(10)]
    chunks = chunk_text(" ".join(words), chunk_size=4, overlap=1)
    assert chunks[0] == "w0 w1 w2 w3"
    assert chunks[1].startswith("w3")  # shares one word with the previous chunk
    assert chunks[-1].endswith("w9")   # nothing is lost at the end


def test_every_word_is_covered():
    words = [f"w{i}" for i in range(57)]
    chunks = chunk_text(" ".join(words), chunk_size=10, overlap=3)
    covered = set(" ".join(chunks).split())
    assert covered == set(words)


@pytest.mark.parametrize("size,overlap", [(0, 0), (5, 5), (5, -1)])
def test_invalid_parameters(size, overlap):
    with pytest.raises(ValueError):
        chunk_text("a b c", size, overlap)
