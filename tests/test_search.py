import unittest

from math_sim.catalog import REGISTRY
from math_sim.search import RegistrySearch, normalize_query


class RegistrySearchTests(unittest.TestCase):
    def setUp(self):
        self.search = RegistrySearch(REGISTRY)

    def test_empty_query_returns_no_results(self):
        self.assertEqual(self.search.search("   "), ())

    def test_nfkc_and_casefold(self):
        self.assertEqual(normalize_query(" ＧＡ "), "ga")

    def test_exact_title_beats_description_match(self):
        results = self.search.search("Perceptron")
        self.assertTrue(results)
        self.assertEqual(results[0].id, "perceptron")

    def test_alias_and_tag_search(self):
        self.assertEqual(self.search.search("Monte Carlo")[0].id, "monte_carlo")
        self.assertIn("maze", {item.id for item in self.search.search("迷路")})

    def test_subject_search(self):
        results = self.search.search("情報")
        self.assertTrue(any(item.kind == "subject" and item.id == "information" for item in results))

    def test_limit(self):
        self.assertLessEqual(len(self.search.search("a", limit=2)), 2)


if __name__ == "__main__":
    unittest.main()
