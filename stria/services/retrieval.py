from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import ClassVar

from rank_bm25 import BM25Okapi

logger = logging.getLogger(__name__)

CHUNK_SIZE = 1200  # ~300 tokens at ~4 chars/token
CHUNK_OVERLAP = 50


@dataclass
class Chunk:
    text: str
    source: str
    chunk_id: int


class DocumentStore:
    """
    In-memory BM25 index over chunked clinical documents.
    Singleton — load once at startup via warm_from_directory().
    """

    _instance: ClassVar[DocumentStore | None] = None

    def __init__(self) -> None:
        self._chunks: list[Chunk] = []
        self._bm25: BM25Okapi | None = None

    @classmethod
    def get(cls) -> DocumentStore:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load(self, documents: list[dict]) -> None:
        """
        documents: list of {"text": str, "source": str}
        Chunks each document, tokenises, and builds the BM25 index.
        """
        self._chunks = []
        for doc in documents:
            text = doc["text"]
            source = doc["source"]
            for i, chunk_text in enumerate(_chunk(text)):
                self._chunks.append(Chunk(text=chunk_text, source=source, chunk_id=i))

        if not self._chunks:
            logger.warning("DocumentStore loaded with no chunks")
            return

        tokenised = [_tokenise(c.text) for c in self._chunks]
        self._bm25 = BM25Okapi(tokenised)
        logger.info("DocumentStore built: %d chunks from %d documents", len(self._chunks), len(documents))

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        """
        Return top_k chunks sorted by BM25 score.
        Each result: {"text": str, "source": str}.
        """
        if self._bm25 is None or not self._chunks:
            return []

        tokens = _tokenise(query)
        scores = self._bm25.get_scores(tokens)

        ranked = sorted(
            zip(scores, self._chunks),
            key=lambda pair: pair[0],
            reverse=True,
        )
        return [
            {"text": chunk.text, "source": chunk.source}
            for _, chunk in ranked[:top_k]
        ]

    def warm_from_directory(self, documents_dir: str) -> None:
        """Load all .txt files from documents_dir into the store."""
        if not os.path.isdir(documents_dir):
            logger.warning("Documents directory not found: %s", documents_dir)
            return

        docs = []
        for fname in sorted(os.listdir(documents_dir)):
            if not fname.endswith(".txt"):
                continue
            fpath = os.path.join(documents_dir, fname)
            try:
                with open(fpath, encoding="utf-8") as f:
                    text = f.read()
                # Use the SOURCE line as the title if present
                source = fname
                for line in text.splitlines()[:3]:
                    if line.startswith("TITLE:"):
                        source = line[len("TITLE:"):].strip()
                        break
                docs.append({"text": text, "source": source})
            except Exception as exc:
                logger.error("Failed to load document %s: %s", fname, exc)

        self.load(docs)


def _chunk(text: str) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(text[start:end])
        start = end - CHUNK_OVERLAP
    return chunks


def _tokenise(text: str) -> list[str]:
    return text.lower().split()


# Module-level singleton access
store = DocumentStore.get()
