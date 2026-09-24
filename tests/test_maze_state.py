import unittest

from math_sim.application import MazePageState


class MazePageStateTests(unittest.TestCase):
    def test_defaults_are_isolated(self):
        first = MazePageState()
        second = MazePageState()
        first.visited_cells.add((1, 1))
        first.race_results.append(("A", {}))
        self.assertNotIn((1, 1), second.visited_cells)
        self.assertEqual(second.race_results, [])

    def test_state_is_read_only_from_callers(self):
        state = MazePageState(moves=3)
        self.assertEqual(state.moves, 3)
        with self.assertRaises(AttributeError):
            state.moves = 4

    def test_reset_play_session_restores_owned_state(self):
        state = MazePageState(
            player=(3, 4),
            playing=True,
            moves=8,
            backtracks=2,
            visited_cells={(0, 0), (1, 0)},
            start_time=1.0,
            elapsed=3.5,
            hint=(2, 2),
        )
        state.reset_play_session()
        self.assertEqual(state.player, (0, 0))
        self.assertFalse(state.playing)
        self.assertEqual(state.moves, 0)
        self.assertEqual(state.backtracks, 0)
        self.assertEqual(state.visited_cells, {(0, 0)})
        self.assertIsNone(state.start_time)
        self.assertEqual(state.elapsed, 0.0)
        self.assertIsNone(state.hint)

    def test_reset_replay_preserves_simulation_result(self):
        result = {"width": 3, "height": 3}
        state = MazePageState(
            result=result,
            mode="race",
            replay_frame=9,
            replaying=True,
            replay_job="job",
        )
        state.reset_replay("generation")
        self.assertIs(state.result, result)
        self.assertEqual(state.mode, "generation")
        self.assertEqual(state.replay_frame, 0)
        self.assertFalse(state.replaying)
        self.assertIsNone(state.replay_job)


if __name__ == "__main__":
    unittest.main()
