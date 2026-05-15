"""Unit tests for the BM25 document store."""
import pytest

from stria.services.retrieval import DocumentStore, _chunk, _tokenise


# ---------------------------------------------------------------------------
# Chunking helpers
# ---------------------------------------------------------------------------

def test_chunk_short_text():
    text = "Short text."
    chunks = _chunk(text)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_long_text():
    text = "A" * 3000
    chunks = _chunk(text)
    assert len(chunks) > 1


def test_tokenise_lowercases():
    tokens = _tokenise("Hello World")
    assert tokens == ["hello", "world"]


def test_tokenise_empty():
    assert _tokenise("") == []


# ---------------------------------------------------------------------------
# DocumentStore
# ---------------------------------------------------------------------------

@pytest.fixture
def fresh_store() -> DocumentStore:
    """Each test gets its own store instance (not the singleton)."""
    return DocumentStore()


def test_store_empty_search(fresh_store):
    results = fresh_store.search("malaria", top_k=3)
    assert results == []


def test_store_load_and_search(fresh_store):
    docs = [
        {"text": "Malaria is caused by Plasmodium falciparum. Control line must be present.", "source": "WHO Guidelines"},
        {"text": "A faint T line still counts as a positive result for malaria RDT.", "source": "WHO Guidelines"},
        {"text": "COVID-19 antigen tests detect SARS-CoV-2 antigens in nasal swabs.", "source": "COVID Protocols"},
    ]
    fresh_store.load(docs)
    results = fresh_store.search("malaria faint positive", top_k=2)
    assert len(results) <= 2
    assert all("text" in r and "source" in r for r in results)


def test_store_top_k_respected(fresh_store):
    docs = [{"text": f"Document {i} about malaria and diagnostics.", "source": f"Source {i}"} for i in range(10)]
    fresh_store.load(docs)
    results = fresh_store.search("malaria diagnostics", top_k=3)
    assert len(results) <= 3


def test_store_search_returns_relevant_first(fresh_store):
    docs = [
        {"text": "Malaria treatment requires artemether-lumefantrine ACT therapy.", "source": "WHO Malaria"},
        {"text": "Pregnancy tests detect hCG hormone in urine samples.", "source": "Pregnancy Protocols"},
        {"text": "HIV testing requires confirmatory testing after reactive result.", "source": "HIV Protocols"},
    ]
    fresh_store.load(docs)
    results = fresh_store.search("malaria artemether treatment", top_k=3)
    # The malaria document should rank highest
    assert results[0]["source"] == "WHO Malaria"


def test_store_warm_from_directory(fresh_store, tmp_path):
    (tmp_path / "doc1.txt").write_text("TITLE: Test Document\nContent about malaria control lines.", encoding="utf-8")
    (tmp_path / "doc2.txt").write_text("TITLE: Another Doc\nContent about COVID testing protocols.", encoding="utf-8")
    (tmp_path / "not_text.json").write_text("{}", encoding="utf-8")

    fresh_store.warm_from_directory(str(tmp_path))
    assert len(fresh_store._chunks) > 0
    results = fresh_store.search("malaria control")
    assert any("malaria" in r["text"].lower() for r in results)


def test_store_warm_missing_directory(fresh_store):
    """Missing directory should warn but not raise."""
    fresh_store.warm_from_directory("/nonexistent/path/that/does/not/exist")
    assert fresh_store._chunks == []


def test_store_load_empty(fresh_store):
    fresh_store.load([])
    assert fresh_store._chunks == []
    assert fresh_store.search("anything") == []
