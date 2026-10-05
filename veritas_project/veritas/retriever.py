"""
Evidence Retrieval
------------------
Retrieves the most relevant passages for a claim from a local knowledge
base using TF-IDF + cosine similarity.

In production this stage would be a hybrid keyword + dense-vector search
(FAISS/Milvus over embeddings) across curated knowledge bases, domain
corpora, and live web search, as described in the accompanying research
paper. TF-IDF is used here so the prototype runs anywhere with zero
external downloads or API keys, while remaining a drop-in swappable
component -- see README "Production upgrade path".
"""

import json
import os

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DEFAULT_KB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "knowledge_base.json")


class EvidenceRetriever:
    def __init__(self, kb_path=None):
        kb_path = kb_path or DEFAULT_KB_PATH
        with open(kb_path, "r", encoding="utf-8") as f:
            self.documents = json.load(f)
        corpus = [d["text"] for d in self.documents]
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.doc_matrix = self.vectorizer.fit_transform(corpus)

    def retrieve(self, claim_text, top_k=3, min_score=0.10):
        query_vec = self.vectorizer.transform([claim_text])
        scores = cosine_similarity(query_vec, self.doc_matrix)[0]
        ranked_idx = scores.argsort()[::-1][:top_k]

        results = []
        for i in ranked_idx:
            if scores[i] >= min_score:
                doc = self.documents[i]
                results.append({
                    "doc_id": doc["id"],
                    "title": doc["title"],
                    "text": doc["text"],
                    "source": doc["source"],
                    "trust_score": doc.get("trust_score", 0.8),
                    "similarity": round(float(scores[i]), 3),
                })
        return results
