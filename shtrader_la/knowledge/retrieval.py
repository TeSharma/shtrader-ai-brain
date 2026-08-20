"""Offline knowledge retrieval.

`KnowledgeProvider` is the interface the agent depends on. `BM25KnowledgeProvider`
is a dependency-free Okapi BM25 implementation over the markdown files in
`knowledge/documents/`. Swapping in sentence embeddings later means writing a new
provider class — the orchestrator does not change.
"""

from __future__ import annotations

import abc
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

from ..core.schemas import KnowledgeHit

DOCUMENTS_DIR = Path(__file__).resolve().parent / "documents"

_TOKEN = re.compile(r"[a-z0-9]+(?:[./][a-z0-9]+)*")

_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "do", "does", "for",
    "from", "how", "i", "if", "in", "is", "it", "its", "me", "my", "no", "not",
    "of", "on", "or", "should", "so", "that", "the", "their", "them", "then",
    "there", "these", "this", "to", "was", "were", "what", "when", "which",
    "who", "why", "will", "with", "you", "your",
}

# Trading synonyms keep the lexical index usable without embeddings.
_SYNONYMS: Dict[str, Sequence[str]] = {
    "rr": ("risk", "reward"),
    "r": ("risk", "reward"),
    "sl": ("stop", "loss"),
    "tp": ("take", "profit"),
    "lot": ("lots", "position", "size"),
    "sizing": ("size", "position"),
    "drawdown": ("drawdown", "loss", "risk"),
    "leverage": ("leverage", "margin"),
    "pip": ("pip", "pips", "forex"),
    "psychology": ("psychology", "discipline", "emotion"),
    "crypto": ("crypto", "bitcoin", "btc"),
    "fx": ("forex", "currency"),
}


def tokenize(text: str) -> List[str]:
    tokens: List[str] = []
    for raw in _TOKEN.findall((text or "").lower()):
        if raw in _STOPWORDS or len(raw) < 2:
            continue
        tokens.append(raw)
        for extra in _SYNONYMS.get(raw, ()):
            if extra != raw:
                tokens.append(extra)
    return tokens


@dataclass
class Document:
    doc_id: str
    title: str
    text: str
    tags: List[str] = field(default_factory=list)

    @property
    def tokens(self) -> List[str]:
        return tokenize(f"{self.title} {' '.join(self.tags)} {self.text}")


class KnowledgeProvider(abc.ABC):
    """Retrieval contract. Implementations must be safe to call offline."""

    name: str = "abstract"

    @abc.abstractmethod
    def search(self, query: str, top_k: int = 3) -> List[KnowledgeHit]: ...

    def documents(self) -> List[Document]:
        return []


class NullKnowledgeProvider(KnowledgeProvider):
    """Used when a caller explicitly wants no retrieval (e.g. pure calculators)."""

    name = "null"

    def search(self, query: str, top_k: int = 3) -> List[KnowledgeHit]:
        return []


class BM25KnowledgeProvider(KnowledgeProvider):
    """Okapi BM25 over an in-memory corpus. Pure standard library."""

    name = "bm25"

    def __init__(
        self,
        documents: Optional[Iterable[Document]] = None,
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        self.k1 = k1
        self.b = b
        self._docs: List[Document] = []
        self._doc_tokens: List[List[str]] = []
        self._term_freqs: List[Counter] = []
        self._doc_freq: Counter = Counter()
        self._avg_len = 0.0
        docs = list(documents) if documents is not None else load_documents()
        for doc in docs:
            self.add(doc, reindex=False)
        self._reindex()

    # -- corpus ------------------------------------------------------------

    def add(self, document: Document, reindex: bool = True) -> None:
        tokens = document.tokens
        self._docs.append(document)
        self._doc_tokens.append(tokens)
        self._term_freqs.append(Counter(tokens))
        if reindex:
            self._reindex()

    def _reindex(self) -> None:
        self._doc_freq = Counter()
        for freqs in self._term_freqs:
            for term in freqs:
                self._doc_freq[term] += 1
        lengths = [len(t) for t in self._doc_tokens]
        self._avg_len = (sum(lengths) / len(lengths)) if lengths else 0.0

    def documents(self) -> List[Document]:
        return list(self._docs)

    def __len__(self) -> int:
        return len(self._docs)

    # -- scoring -----------------------------------------------------------

    def _idf(self, term: str) -> float:
        n = len(self._docs)
        df = self._doc_freq.get(term, 0)
        if df == 0:
            return 0.0
        # BM25+ style floor keeps common-but-present terms weakly positive.
        return max(1e-6, math.log(1 + (n - df + 0.5) / (df + 0.5)))

    def score(self, query_tokens: Sequence[str], index: int) -> float:
        freqs = self._term_freqs[index]
        doc_len = len(self._doc_tokens[index]) or 1
        total = 0.0
        for term in query_tokens:
            tf = freqs.get(term, 0)
            if tf == 0:
                continue
            idf = self._idf(term)
            denom = tf + self.k1 * (1 - self.b + self.b * doc_len / (self._avg_len or doc_len))
            total += idf * (tf * (self.k1 + 1)) / denom
        return total

    def search(self, query: str, top_k: int = 3) -> List[KnowledgeHit]:
        query_tokens = tokenize(query)
        if not query_tokens or not self._docs:
            return []
        scored = []
        for index, doc in enumerate(self._docs):
            score = self.score(query_tokens, index)
            if score > 0:
                scored.append((score, index, doc))
        scored.sort(key=lambda row: (-row[0], row[2].doc_id))
        hits: List[KnowledgeHit] = []
        for score, index, doc in scored[: max(0, top_k)]:
            hits.append(
                KnowledgeHit(
                    doc_id=doc.doc_id,
                    title=doc.title,
                    score=round(score, 4),
                    excerpt=best_excerpt(doc.text, query_tokens),
                )
            )
        return hits


def best_excerpt(text: str, query_tokens: Sequence[str], max_chars: int = 320) -> str:
    """Return the paragraph with the most query-term hits, trimmed."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paragraphs:
        return text[:max_chars].strip()
    wanted = set(query_tokens)
    best = max(
        paragraphs,
        key=lambda p: (sum(1 for token in tokenize(p) if token in wanted), -len(p)),
    )
    collapsed = re.sub(r"\s+", " ", best)
    if len(collapsed) <= max_chars:
        return collapsed
    return collapsed[: max_chars - 1].rsplit(" ", 1)[0] + "…"


def parse_markdown(path: Path) -> Document:
    raw = path.read_text(encoding="utf-8")
    lines = raw.splitlines()
    title = path.stem.replace("-", " ").replace("_", " ").title()
    tags: List[str] = []
    body_start = 0
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("# "):
            title = stripped[2:].strip()
            body_start = index + 1
        elif stripped.lower().startswith("tags:"):
            tags = [t.strip().lower() for t in stripped.split(":", 1)[1].split(",") if t.strip()]
            body_start = index + 1
        elif stripped:
            break
    body = "\n".join(lines[body_start:]).strip()
    return Document(doc_id=path.stem, title=title, text=body or raw, tags=tags)


def load_documents(directory: Optional[Path] = None) -> List[Document]:
    folder = directory or DOCUMENTS_DIR
    if not folder.is_dir():
        return []
    return [parse_markdown(path) for path in sorted(folder.glob("*.md"))]


def build_knowledge_provider(directory: Optional[Path] = None) -> KnowledgeProvider:
    return BM25KnowledgeProvider(load_documents(directory))
