"""Split text into overlapping chunks of words."""


def chunk_text(text: str, chunk_size: int = 120, overlap: int = 20) -> list[str]:
    """Split ``text`` into chunks of at most ``chunk_size`` words.

    Consecutive chunks share ``overlap`` words so that a sentence cut at a
    boundary still appears whole in at least one chunk.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be >= 0 and smaller than chunk_size")

    words = text.split()
    if not words:
        return []

    step = chunk_size - overlap
    chunks = []
    for start in range(0, len(words), step):
        chunks.append(" ".join(words[start:start + chunk_size]))
        if start + chunk_size >= len(words):
            break
    return chunks
