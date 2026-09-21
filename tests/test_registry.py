import unittest

from math_sim.registry import (
    DemoDescriptor,
    LearningRegistry,
    RegistryError,
    Subject,
    Subcategory,
    create_default_registry,
)


class LearningRegistryTests(unittest.TestCase):
    def test_rejects_duplicate_ids(self):
        with self.assertRaises(RegistryError):
            LearningRegistry(
                subjects=[Subject("math", "Math"), Subject("math", "Duplicate")]
            )

    def test_rejects_unknown_references(self):
        with self.assertRaises(RegistryError):
            LearningRegistry(
                subjects=[Subject("math", "Math")],
                subcategories=[Subcategory("mechanics", "physics", "Mechanics")],
            )

    def test_rejects_subject_subcategory_mismatch(self):
        with self.assertRaises(RegistryError):
            LearningRegistry(
                subjects=[Subject("math", "Math"), Subject("physics", "Physics")],
                subcategories=[Subcategory("mechanics", "physics", "Mechanics")],
                demos=[
                    DemoDescriptor(
                        "demo",
                        "Demo",
                        "route",
                        "math",
                        subcategory_id="mechanics",
                    )
                ],
            )

    def test_orders_subjects_subcategories_and_demos(self):
        registry = LearningRegistry(
            subjects=[
                Subject("b", "B", order=20, visible_when_empty=True),
                Subject("a", "A", order=10, visible_when_empty=True),
            ],
            subcategories=[
                Subcategory("b2", "b", "B2", order=20),
                Subcategory("b1", "b", "B1", order=10),
            ],
            demos=[
                DemoDescriptor("d2", "D2", "r2", "b", "b1", order=20),
                DemoDescriptor("d1", "D1", "r1", "b", "b1", order=10),
            ],
        )
        self.assertEqual([item.id for item in registry.subjects()], ["a", "b"])
        self.assertEqual(
            [item.id for item in registry.subcategories("b")], ["b1", "b2"]
        )
        self.assertEqual(
            [item.id for item in registry.demos(subject_id="b")], ["d1", "d2"]
        )

    def test_visible_when_empty(self):
        registry = LearningRegistry(
            subjects=[
                Subject("shown", "Shown", visible_when_empty=True),
                Subject("hidden", "Hidden", visible_when_empty=False),
            ]
        )
        self.assertEqual([item.id for item in registry.subjects()], ["shown"])
        self.assertEqual(
            {item.id for item in registry.subjects(include_empty=True)},
            {"shown", "hidden"},
        )

    def test_default_registry_contains_initial_subjects(self):
        registry = create_default_registry()
        self.assertEqual(
            [item.id for item in registry.subjects(include_empty=True)],
            [
                "math",
                "physics",
                "chemistry",
                "information",
                "english",
                "history",
                "biology",
                "health",
                "japanese",
            ],
        )

    def test_related_subjects_are_validated(self):
        with self.assertRaises(RegistryError):
            LearningRegistry(
                subjects=[Subject("math", "Math")],
                demos=[
                    DemoDescriptor(
                        "demo",
                        "Demo",
                        "route",
                        "math",
                        related_subjects=("physics",),
                    )
                ],
            )


if __name__ == "__main__":
    unittest.main()
