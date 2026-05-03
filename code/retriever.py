from dataclasses import dataclass
import re
from typing import List, Set

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from models import SupportDocument


@dataclass
class RetrievedDocument:
    document: SupportDocument
    score: float
    body_score: float = 0.0
    metadata_score: float = 0.0
    overlap_score: float = 0.0


class CorpusRetriever:
    def __init__(self, documents: List[SupportDocument]) -> None:
        self.documents = documents

        self.body_texts = [self._build_body_text(document) for document in documents]
        self.metadata_texts = [self._build_metadata_text(document) for document in documents]

        self.body_vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
            max_features=70000,
            sublinear_tf=True,
        )

        self.metadata_vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 3),
            max_features=30000,
            sublinear_tf=True,
        )

        self.body_matrix = self.body_vectorizer.fit_transform(self.body_texts)
        self.metadata_matrix = self.metadata_vectorizer.fit_transform(self.metadata_texts)

    def _build_body_text(self, document: SupportDocument) -> str:
        parts = [
            document.company_name,
            document.title,
            document.breadcrumbs,
            document.text,
        ]

        return "\n".join(part for part in parts if part)

    def _build_metadata_text(self, document: SupportDocument) -> str:
        parts = [
            document.company_name,
            document.title,
            document.title,
            document.title,
            document.breadcrumbs,
            document.breadcrumbs,
        ]

        return "\n".join(part for part in parts if part)

    def _tokens(self, text: str) -> Set[str]:
        words = re.findall(r"[a-z0-9]+", text.lower())

        ignored = {
            "the",
            "and",
            "for",
            "with",
            "that",
            "this",
            "from",
            "have",
            "you",
            "your",
            "can",
            "how",
            "what",
            "where",
            "when",
            "why",
            "are",
            "was",
            "were",
            "will",
            "would",
            "could",
            "should",
            "please",
            "help",
            "need",
            "issue",
            "problem",
        }

        return {word for word in words if len(word) > 2 and word not in ignored}

    def _overlap_score(self, query: str, document: SupportDocument) -> float:
        query_tokens = self._tokens(query)
        if not query_tokens:
            return 0.0

        metadata = f"{document.title} {document.breadcrumbs}"
        metadata_tokens = self._tokens(metadata)

        if not metadata_tokens:
            return 0.0

        overlap = query_tokens.intersection(metadata_tokens)
        return len(overlap) / max(len(query_tokens), 1)

    def search(
        self,
        query: str,
        company_key: str = "",
        top_k: int = 5,
    ) -> List[RetrievedDocument]:
        if not query.strip():
            return []

        candidate_indexes = []

        for index, document in enumerate(self.documents):
            if company_key and document.company_key != company_key:
                continue
            candidate_indexes.append(index)

        if not candidate_indexes:
            return []

        body_query_vector = self.body_vectorizer.transform([query])
        metadata_query_vector = self.metadata_vectorizer.transform([query])

        body_candidate_matrix = self.body_matrix[candidate_indexes]
        metadata_candidate_matrix = self.metadata_matrix[candidate_indexes]

        body_scores = cosine_similarity(body_query_vector, body_candidate_matrix).flatten()
        metadata_scores = cosine_similarity(metadata_query_vector, metadata_candidate_matrix).flatten()

        ranked = []

        for local_index, document_index in enumerate(candidate_indexes):
            document = self.documents[document_index]

            body_score = float(body_scores[local_index])
            metadata_score = float(metadata_scores[local_index])
            overlap_score = self._overlap_score(query, document)

            combined_score = (
                body_score * 0.55
                + metadata_score * 0.35
                + overlap_score * 0.10
            )

            ranked.append(
                RetrievedDocument(
                    document=document,
                    score=float(combined_score),
                    body_score=body_score,
                    metadata_score=metadata_score,
                    overlap_score=overlap_score,
                )
            )

        ranked.sort(key=lambda result: result.score, reverse=True)

        return ranked[:top_k]