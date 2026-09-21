from __future__ import annotations

from dataclasses import dataclass
import unicodedata

from math_sim.registry import DemoDescriptor, LearningRegistry, Subject, Subcategory


@dataclass(frozen=True)
class SearchResult:
    kind: str
    id: str
    title: str
    description: str
    route: str | None = None
    subject_id: str | None = None
    subcategory_id: str | None = None
    score: int = 0


def normalize_query(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).strip().casefold()
    return "".join(ch for ch in value if not ch.isspace())


def _score_field(query: str, value: str, exact: int, prefix: int, contains: int) -> int:
    normalized = normalize_query(value)
    if not normalized:
        return 0
    if normalized == query:
        return exact
    if normalized.startswith(query):
        return prefix
    if query in normalized:
        return contains
    return 0


class RegistrySearch:
    def __init__(self, registry: LearningRegistry) -> None:
        self.registry = registry

    def search(self, raw_query: str, *, limit: int = 30) -> tuple[SearchResult, ...]:
        query = normalize_query(raw_query)
        if not query:
            return ()

        results: list[SearchResult] = []
        for subject in self.registry.subjects(include_empty=True):
            score = max(
                _score_field(query, subject.title, 100, 80, 40),
                _score_field(query, subject.id, 90, 70, 35),
                _score_field(query, subject.description, 30, 20, 10),
            )
            if score:
                results.append(
                    SearchResult("subject", subject.id, subject.title, subject.description, score=score)
                )

        for subject in self.registry.subjects(include_empty=True):
            for subcategory in self.registry.subcategories(subject.id):
                score = max(
                    _score_field(query, subcategory.title, 95, 75, 38),
                    _score_field(query, subcategory.id, 85, 65, 32),
                    _score_field(query, subcategory.description, 28, 18, 9),
                )
                if score:
                    results.append(
                        SearchResult(
                            "subcategory",
                            subcategory.id,
                            subcategory.title,
                            subcategory.description,
                            subject_id=subcategory.subject_id,
                            score=score,
                        )
                    )

        for demo in self.registry.demos():
            score = self._score_demo(query, demo)
            if score:
                results.append(
                    SearchResult(
                        "demo",
                        demo.id,
                        demo.title,
                        demo.description,
                        route=demo.route,
                        subject_id=demo.subject_id,
                        subcategory_id=demo.subcategory_id,
                        score=score,
                    )
                )

        results.sort(key=lambda item: (-item.score, item.kind, item.title, item.id))
        return tuple(results[:limit])

    @staticmethod
    def _score_demo(query: str, demo: DemoDescriptor) -> int:
        scores = [
            _score_field(query, demo.title, 120, 100, 60),
            _score_field(query, demo.id, 105, 85, 50),
            _score_field(query, demo.description, 40, 30, 20),
        ]
        scores.extend(_score_field(query, value, 110, 90, 55) for value in demo.aliases)
        scores.extend(_score_field(query, value, 100, 80, 45) for value in demo.tags)
        scores.extend(_score_field(query, value, 95, 75, 42) for value in demo.keywords)
        scores.extend(_score_field(query, value, 70, 55, 30) for value in demo.related_subjects)
        return max(scores, default=0)
