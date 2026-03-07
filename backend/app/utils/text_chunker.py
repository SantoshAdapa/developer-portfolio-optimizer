"""Text chunking utilities for embedding pipelines."""


def chunk_text(
    text: str,
    chunk_size: int = 512,
    overlap: int = 50,
) -> list[str]:
    """Split text into overlapping word-based chunks.

    Args:
        text: The full text to chunk.
        chunk_size: Target number of words per chunk.
        overlap: Number of overlapping words between consecutive chunks.

    Returns:
        List of text chunks. Empty list if input is blank.
    """
    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)

        # Advance by (chunk_size - overlap), but at least 1 word
        step = max(1, chunk_size - overlap)
        start += step

    return chunks


def chunk_text_by_sentences(
    text: str,
    max_chunk_tokens: int = 500,
    overlap_sentences: int = 1,
) -> list[str]:
    """Split text into chunks at sentence boundaries.

    Tries to keep chunks under max_chunk_tokens words while
    avoiding mid-sentence breaks. Overlaps by N sentences.

    Args:
        text: The full text to chunk.
        max_chunk_tokens: Approximate max words per chunk.
        overlap_sentences: Number of sentences to repeat at chunk boundaries.

    Returns:
        List of text chunks.
    """
    import re

    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    sentences = [s for s in sentences if s.strip()]

    if not sentences:
        return []

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for sentence in sentences:
        word_count = len(sentence.split())

        if current_len + word_count > max_chunk_tokens and current:
            chunks.append(" ".join(current))
            # Keep last N sentences for overlap
            current = current[-overlap_sentences:] if overlap_sentences > 0 else []
            current_len = sum(len(s.split()) for s in current)

        current.append(sentence)
        current_len += word_count

    if current:
        chunks.append(" ".join(current))

    return chunks
