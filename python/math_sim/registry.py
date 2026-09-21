from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Subject:
    id: str
    title: str
    description: str = ""
    order: int = 0
    visible_when_empty: bool = False


@dataclass(frozen=True)
class Subcategory:
    id: str
    subject_id: str
    title: str
    description: str = ""
    order: int = 0


@dataclass(frozen=True)
class DemoDescriptor:
    id: str
    title: str
    route: str
    subject_id: str
    subcategory_id: str | None = None
    description: str = ""
    order: int = 0
    related_subjects: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    aliases: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()


class RegistryError(ValueError):
    pass


class LearningRegistry:
    def __init__(
        self,
        subjects: Iterable[Subject] = (),
        subcategories: Iterable[Subcategory] = (),
        demos: Iterable[DemoDescriptor] = (),
    ) -> None:
        self._subjects = self._unique_by_id(subjects, "subject")
        self._subcategories = self._unique_by_id(subcategories, "subcategory")
        self._demos = self._unique_by_id(demos, "demo")
        self.validate()

    @staticmethod
    def _unique_by_id(items: Iterable[object], kind: str) -> dict[str, object]:
        result: dict[str, object] = {}
        for item in items:
            item_id = getattr(item, "id", None)
            if not isinstance(item_id, str) or not item_id.strip():
                raise RegistryError(f"{kind} id must be a non-empty string")
            if item_id in result:
                raise RegistryError(f"duplicate {kind} id: {item_id}")
            result[item_id] = item
        return result

    def validate(self) -> None:
        for subcategory in self._subcategories.values():
            if subcategory.subject_id not in self._subjects:
                raise RegistryError(
                    f"subcategory {subcategory.id} references unknown subject "
                    f"{subcategory.subject_id}"
                )

        for demo in self._demos.values():
            if demo.subject_id not in self._subjects:
                raise RegistryError(
                    f"demo {demo.id} references unknown subject {demo.subject_id}"
                )
            if demo.subcategory_id is not None:
                subcategory = self._subcategories.get(demo.subcategory_id)
                if subcategory is None:
                    raise RegistryError(
                        f"demo {demo.id} references unknown subcategory "
                        f"{demo.subcategory_id}"
                    )
                if subcategory.subject_id != demo.subject_id:
                    raise RegistryError(
                        f"demo {demo.id} subject/subcategory mismatch: "
                        f"{demo.subject_id} vs {subcategory.subject_id}"
                    )
            for related in demo.related_subjects:
                if related not in self._subjects:
                    raise RegistryError(
                        f"demo {demo.id} references unknown related subject {related}"
                    )

    def subjects(self, *, include_empty: bool = False) -> tuple[Subject, ...]:
        non_empty = {demo.subject_id for demo in self._demos.values()}
        items = [
            subject
            for subject in self._subjects.values()
            if include_empty or subject.visible_when_empty or subject.id in non_empty
        ]
        return tuple(sorted(items, key=lambda x: (x.order, x.title, x.id)))

    def subcategories(self, subject_id: str) -> tuple[Subcategory, ...]:
        self.subject(subject_id)
        items = [
            item for item in self._subcategories.values()
            if item.subject_id == subject_id
        ]
        return tuple(sorted(items, key=lambda x: (x.order, x.title, x.id)))

    def demos(
        self,
        *,
        subject_id: str | None = None,
        subcategory_id: str | None = None,
    ) -> tuple[DemoDescriptor, ...]:
        if subject_id is not None:
            self.subject(subject_id)
        if subcategory_id is not None and subcategory_id not in self._subcategories:
            raise KeyError(subcategory_id)

        items = list(self._demos.values())
        if subject_id is not None:
            items = [item for item in items if item.subject_id == subject_id]
        if subcategory_id is not None:
            items = [item for item in items if item.subcategory_id == subcategory_id]
        return tuple(sorted(items, key=lambda x: (x.order, x.title, x.id)))

    def subject(self, subject_id: str) -> Subject:
        try:
            return self._subjects[subject_id]
        except KeyError:
            raise KeyError(subject_id) from None

    def subcategory(self, subcategory_id: str) -> Subcategory:
        try:
            return self._subcategories[subcategory_id]
        except KeyError:
            raise KeyError(subcategory_id) from None

    def demo(self, demo_id: str) -> DemoDescriptor:
        try:
            return self._demos[demo_id]
        except KeyError:
            raise KeyError(demo_id) from None


DEFAULT_SUBJECTS = (
    Subject("math", "数学", order=10, visible_when_empty=True),
    Subject("physics", "物理", order=20, visible_when_empty=True),
    Subject("chemistry", "化学", order=30, visible_when_empty=True),
    Subject("information", "情報", order=40, visible_when_empty=True),
    Subject("english", "英語", order=50, visible_when_empty=True),
    Subject("history", "歴史", order=60, visible_when_empty=True),
    Subject("biology", "生物", order=70, visible_when_empty=True),
    Subject("health", "保健", order=80, visible_when_empty=False),
    Subject("japanese", "国語", order=90, visible_when_empty=False),
)


def create_default_registry(
    *,
    subcategories: Iterable[Subcategory] = (),
    demos: Iterable[DemoDescriptor] = (),
) -> LearningRegistry:
    return LearningRegistry(DEFAULT_SUBJECTS, subcategories, demos)
