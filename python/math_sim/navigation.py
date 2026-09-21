from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NavigationContext:
    route: str = "home"
    subject_id: str | None = None
    subcategory_id: str | None = None


class NavigationModel:
    def __init__(self) -> None:
        self._context = NavigationContext()

    @property
    def context(self) -> NavigationContext:
        return self._context

    def go_home(self) -> NavigationContext:
        self._context = NavigationContext()
        return self._context

    def go_subject(self, subject_id: str) -> NavigationContext:
        self._context = NavigationContext(route="home", subject_id=subject_id)
        return self._context

    def go_demo(
        self,
        route: str,
        *,
        subject_id: str | None = None,
        subcategory_id: str | None = None,
    ) -> NavigationContext:
        self._context = NavigationContext(
            route=route,
            subject_id=subject_id,
            subcategory_id=subcategory_id,
        )
        return self._context

    def back(self) -> NavigationContext:
        current = self._context
        if current.route != "home":
            if current.subject_id:
                return self.go_subject(current.subject_id)
            return self.go_home()
        if current.subject_id:
            return self.go_home()
        return self._context

    def breadcrumb(self) -> tuple[str, ...]:
        current = self._context
        parts = ["Subjects"]
        if current.subject_id:
            parts.append(current.subject_id)
        if current.route != "home":
            parts.append(current.route)
        return tuple(parts)
