import unittest

from math_sim.application import (
    MazePageState,
    MazePlaybackController,
    MazePlaySessionController,
    MazeRaceController,
)


class MazePlaybackControllerTests(unittest.TestCase):
    def test_search_generation_and_race_totals(self):
        search_state = MazePageState(result={"trace": [[0, 0], [1, 0]]})
        self.assertEqual(MazePlaybackController(search_state).total_frames(), 2)

        generation_state = MazePageState(
            result={"generation_trace": [[0, 0, 1, 0]]},
            mode="generation",
        )
        self.assertEqual(
            MazePlaybackController(generation_state).total_frames(),
            1,
        )

        race_state = MazePageState(
            race_results=[
                ("A", {"trace": [1, 2, 3]}),
                ("B", {"trace": [1]}),
            ],
            mode="race",
        )
        self.assertEqual(MazePlaybackController(race_state).total_frames(), 3)

    def test_step_start_advance_and_speed(self):
        state = MazePageState(result={"trace": [1, 2]})
        controller = MazePlaybackController(state)

        self.assertTrue(controller.start())
        self.assertTrue(state.replaying)
        self.assertTrue(controller.advance())
        self.assertEqual(state.replay_frame, 1)
        self.assertTrue(controller.advance())
        self.assertEqual(state.replay_frame, 2)
        self.assertFalse(controller.advance())
        self.assertFalse(state.replaying)

        self.assertEqual(state.replay_speed, 1.0)
        self.assertEqual(controller.change_speed(1), 2.0)
        self.assertEqual(controller.change_speed(-1), 1.0)

    def test_generation_walls_replays_removed_edge(self):
        state = MazePageState(
            result={"generation_trace": [[0, 0, 1, 0]]},
            mode="generation",
        )
        controller = MazePlaybackController(state)
        walls = controller.generation_walls(2, 1, 1)

        east = 2
        west = 8
        self.assertEqual(walls[0] & east, 0)
        self.assertEqual(walls[1] & west, 0)


class MazePlaySessionControllerTests(unittest.TestCase):
    def test_move_to_goal_finishes_session(self):
        state = MazePageState()
        controller = MazePlaySessionController(state)
        controller.start(10.0)

        result = {
            "width": 2,
            "height": 1,
            "walls": [0, 0],
            "optimal_steps": 1,
        }
        move = controller.move(result, 1, 0, 12.5)

        self.assertTrue(move.moved)
        self.assertTrue(move.finished)
        self.assertEqual(move.position, (1, 0))
        self.assertFalse(state.playing)
        self.assertEqual(state.elapsed, 2.5)

        metrics = controller.metrics(1)
        self.assertEqual(metrics.moves, 1)
        self.assertEqual(metrics.extra_steps, 0)
        self.assertEqual(metrics.efficiency_percent, 100.0)

    def test_backtrack_and_hint_are_owned_by_session(self):
        state = MazePageState()
        controller = MazePlaySessionController(state)
        controller.start(1.0)

        result = {
            "width": 2,
            "height": 2,
            "walls": [0, 0, 0, 0],
        }
        controller.move(result, 1, 0, 1.5)
        controller.move(result, -1, 0, 2.0)
        self.assertEqual(state.backtracks, 1)

        self.assertEqual(state.player, (0, 0))
        hint = controller.next_hint([[0, 0], [0, 1], [1, 1]])
        self.assertEqual(hint, (0, 1))
        self.assertEqual(state.hint, (0, 1))


class MazeRaceControllerTests(unittest.TestCase):
    def test_race_table_ranks_completed_solvers_by_trace_length(self):
        rows = [
            ("Slow", {"trace": [1, 2, 3], "steps": 3, "loss_percent": 0, "calculation_count": 4}),
            ("Fast", {"trace": [1], "steps": 1, "loss_percent": 0, "calculation_count": 2}),
        ]
        table = MazeRaceController.race_table(rows, frame=3)
        self.assertIn("#1 FINISH", table)
        self.assertLess(table.index("Fast"), table.index("Slow"))

    def test_comparison_table_marks_failures(self):
        rows = [
            ("A", {"found": False, "calculation_count": 5}),
            ("B", {"found": True, "steps": 4, "extra_steps": 1, "loss_percent": 25, "calculation_count": 7}),
        ]
        table = MazeRaceController.comparison_table(rows)
        self.assertIn("FAIL", table)
        self.assertIn("25.0%", table)


if __name__ == "__main__":
    unittest.main()
