"""Tests for text chunking utilities."""

from app.utils.text_chunker import chunk_text, chunk_text_by_sentences


# ── chunk_text ───────────────────────────────────────────


def test_chunk_text_empty():
    assert chunk_text("") == []
    assert chunk_text("   ") == []


def test_chunk_text_short():
    text = "one two three"
    chunks = chunk_text(text, chunk_size=10, overlap=0)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_text_splits_correctly():
    words = " ".join(f"w{i}" for i in range(20))
    chunks = chunk_text(words, chunk_size=10, overlap=2)
    assert len(chunks) >= 2
    # First chunk has 10 words
    assert len(chunks[0].split()) == 10


def test_chunk_text_overlap():
    words = " ".join(f"w{i}" for i in range(20))
    chunks = chunk_text(words, chunk_size=10, overlap=5)
    # The tail of chunk 0 and head of chunk 1 should share words
    tail_0 = set(chunks[0].split()[-5:])
    head_1 = set(chunks[1].split()[:5])
    assert tail_0 == head_1


def test_chunk_text_overlap_exceeds_size():
    """When overlap >= chunk_size, step should be at least 1 to avoid infinite loop."""
    words = "a b c d e f g h"
    chunks = chunk_text(words, chunk_size=3, overlap=5)
    assert len(chunks) >= 1  # must terminate


# ── chunk_text_by_sentences ──────────────────────────────


def test_sentences_empty():
    assert chunk_text_by_sentences("") == []


def test_sentences_single():
    text = "Hello world."
    chunks = chunk_text_by_sentences(text, max_chunk_tokens=100)
    assert len(chunks) == 1


def test_sentences_split():
    text = "First sentence. Second sentence. Third sentence. Fourth sentence."
    chunks = chunk_text_by_sentences(text, max_chunk_tokens=3, overlap_sentences=0)
    assert len(chunks) >= 2


def test_sentences_overlap():
    text = "A short one. Another short one. Yet another one."
    chunks = chunk_text_by_sentences(text, max_chunk_tokens=4, overlap_sentences=1)
    if len(chunks) >= 2:
        # Last sentence of chunk N should appear at start of chunk N+1
        assert chunks[0].split(".")[-2].strip() in chunks[1]
