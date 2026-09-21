import unittest

from math_sim.navigation import NavigationModel


class NavigationModelTests(unittest.TestCase):
    def test_demo_back_returns_to_subject_then_home(self):
        nav = NavigationModel()
        nav.go_demo("maze", subject_id="information", subcategory_id="algorithms")
        context = nav.back()
        self.assertEqual(context.route, "home")
        self.assertEqual(context.subject_id, "information")
        context = nav.back()
        self.assertEqual(context.route, "home")
        self.assertIsNone(context.subject_id)

    def test_direct_demo_falls_back_to_home(self):
        nav = NavigationModel()
        nav.go_demo("maze")
        context = nav.back()
        self.assertEqual(context.route, "home")
        self.assertIsNone(context.subject_id)

    def test_breadcrumb_tracks_context(self):
        nav = NavigationModel()
        nav.go_demo("mlp", subject_id="information")
        self.assertEqual(nav.breadcrumb(), ("Subjects", "information", "mlp"))


if __name__ == "__main__":
    unittest.main()
