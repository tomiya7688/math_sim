import unittest

from math_sim.catalog import REGISTRY
from math_sim.registry import DemoDescriptor, LearningRegistry, Subject, Subcategory
from math_sim.search import RegistrySearch


class BiologyRegistryTests(unittest.TestCase):
    def test_biology_subject_and_human_body_category_exist(self):
        biology = REGISTRY.subject("biology")
        self.assertEqual(biology.title, "生物")
        categories = {item.id for item in REGISTRY.subcategories("biology")}
        self.assertIn("human_body", categories)

    def test_biology_is_visible_even_before_demos_exist(self):
        visible = {item.id for item in REGISTRY.subjects()}
        self.assertIn("biology", visible)

    def test_human_body_demo_can_reference_related_subjects(self):
        registry = LearningRegistry(
            subjects=[
                Subject("biology", "生物"),
                Subject("health", "保健"),
                Subject("chemistry", "化学"),
                Subject("physics", "物理"),
            ],
            subcategories=[Subcategory("human_body", "biology", "人体")],
            demos=[
                DemoDescriptor(
                    "heart",
                    "心臓",
                    "heart",
                    "biology",
                    "human_body",
                    related_subjects=("health", "chemistry", "physics"),
                )
            ],
        )
        self.assertEqual(registry.demo("heart").subject_id, "biology")

    def test_search_can_find_biology_subject(self):
        results = RegistrySearch(REGISTRY).search("生物")
        self.assertTrue(any(item.kind == "subject" and item.id == "biology" for item in results))


if __name__ == "__main__":
    unittest.main()
