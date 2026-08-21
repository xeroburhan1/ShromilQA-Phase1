"""
Embed & vector store (architecture report §4.5-4.6).

Phase 1 uses a dependency-light, fully offline embedding: TF-IDF vectors
reduced to a dense space with truncated SVD (a.k.a. latent semantic
indexing), then indexed in FAISS. This avoids downloading a multi-gigabyte
transformer model for a corpus this small, while still giving semantic-ish
similarity (SVD captures co-occurring legal terminology, not just exact
word overlap) and a genuine FAISS vector store, per the architecture.

Swapping in a sentence-transformer model later only touches `embed_query`
and `_fit_embedder` — nothing else in the pipeline needs to change.
"""
from __future__ import annotations

import json
import pickle
import re
from pathlib import Path

import faiss
import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize

from .corpus import Section, parse_sections

INDEX_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "rag_index"
EMBED_DIM = 128


class RagIndex:
    def __init__(self, sections: list[Section], vectorizer, svd, faiss_index):
        self.sections = sections
        self.vectorizer = vectorizer
        self.svd = svd
        self.index = faiss_index

    # ---- building ----

    @classmethod
    def build(cls, sections: list[Section] | None = None) -> "RagIndex":
        sections = sections if sections is not None else parse_sections()
        corpus_texts = [f"{s.title}. {s.text}" for s in sections]

        n_components = min(EMBED_DIM, max(2, len(corpus_texts) - 1))
        vectorizer = TfidfVectorizer(
            stop_words="english", ngram_range=(1, 2), min_df=1, max_df=0.9
        )
        tfidf = vectorizer.fit_transform(corpus_texts)

        svd = TruncatedSVD(n_components=n_components, random_state=42)
        dense = svd.fit_transform(tfidf).astype("float32")
        dense = normalize(dense, axis=1)

        faiss_index = faiss.IndexFlatIP(dense.shape[1])
        faiss_index.add(dense)

        return cls(sections, vectorizer, svd, faiss_index)

    def save(self, directory: Path = INDEX_DIR) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(directory / "sections.faiss"))
        with open(directory / "vectorizer.pkl", "wb") as f:
            pickle.dump(self.vectorizer, f)
        with open(directory / "svd.pkl", "wb") as f:
            pickle.dump(self.svd, f)
        with open(directory / "sections.json", "w", encoding="utf-8") as f:
            json.dump(
                [s.__dict__ for s in self.sections], f, ensure_ascii=False, indent=1
            )

    @classmethod
    def load(cls, directory: Path = INDEX_DIR) -> "RagIndex":
        with open(directory / "sections.json", encoding="utf-8") as f:
            sections = [Section(**d) for d in json.load(f)]
        with open(directory / "vectorizer.pkl", "rb") as f:
            vectorizer = pickle.load(f)
        with open(directory / "svd.pkl", "rb") as f:
            svd = pickle.load(f)
        faiss_index = faiss.read_index(str(directory / "sections.faiss"))
        return cls(sections, vectorizer, svd, faiss_index)

    @classmethod
    def load_or_build(cls, directory: Path = INDEX_DIR) -> "RagIndex":
        required = ["sections.faiss", "vectorizer.pkl", "svd.pkl", "sections.json"]
        if all((directory / f).exists() for f in required):
            return cls.load(directory)
        idx = cls.build()
        idx.save(directory)
        return idx

    # ---- querying ----

    def embed_query(self, query: str) -> np.ndarray:
        tfidf = self.vectorizer.transform([query])
        dense = self.svd.transform(tfidf).astype("float32")
        return normalize(dense, axis=1)

    def search(self, query: str, top_k: int = 4) -> list[tuple[Section, float]]:
        """
        Hybrid search: blends the SVD/FAISS dense score (captures related
        vocabulary) with a raw TF-IDF cosine score (rewards exact legal-term
        matches, e.g. "maternity benefit"). A pure dense score alone under-
        ranks sections that use precise statutory wording different from
        the query's phrasing; pure TF-IDF alone misses paraphrases. Blending
        both is a lightweight stand-in for the hybrid dense-sparse retrieval
        the course covers, sized for an 80-section corpus.
        """
        query_tfidf = self.vectorizer.transform([query])
        corpus_tfidf = self.vectorizer.transform(
            [f"{s.title}. {s.text}" for s in self.sections]
        )
        sparse_scores = cosine_similarity(query_tfidf, corpus_tfidf)[0]

        dense_vec = self.embed_query(query)
        # Search the whole index so we can blend on every candidate, not just FAISS's top_k.
        dense_scores, dense_idxs = self.index.search(dense_vec, len(self.sections))
        dense_by_idx = {int(i): float(s) for s, i in zip(dense_scores[0], dense_idxs[0]) if i != -1}

        blended = []
        query_words = {w for w in re.findall(r"[a-z]{4,}", query.lower())}
        for i, section in enumerate(self.sections):
            dense_s = dense_by_idx.get(i, 0.0)
            sparse_s = float(sparse_scores[i])
            title_words = set(re.findall(r"[a-z]{4,}", section.title.lower()))
            title_hits = len(query_words & title_words)
            title_boost = 0.25 * title_hits
            score = 0.5 * dense_s + 0.5 * sparse_s + title_boost
            blended.append((section, score))

        blended.sort(key=lambda pair: pair[1], reverse=True)
        return blended[:top_k]

    def get_by_number(self, number: int) -> Section | None:
        for s in self.sections:
            if s.number == number:
                return s
        return None


if __name__ == "__main__":
    index = RagIndex.build()
    index.save()
    print(f"Built and saved index with {len(index.sections)} sections -> {INDEX_DIR}")

    for q in ["how many days notice to fire a permanent worker", "maternity leave pay", "fire safety exits"]:
        print(f"\nQuery: {q!r}")
        for sec, score in index.search(q, top_k=3):
            print(f"  {score:.3f}  {sec.citation} — {sec.title}")
