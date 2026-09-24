from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


NORTH, EAST, SOUTH, WEST = 1, 2, 4, 8
DEFAULT_PLAYBACK_SPEEDS = (0.25, 0.5, 1.0, 2.0, 4.0)


class MazePageState:
    __slots__ = (
        "_result",
        "_race_results",
        "_mode",
        "_player",
        "_playing",
        "_moves",
        "_backtracks",
        "_visited_cells",
        "_start_time",
        "_elapsed",
        "_hint",
        "_replay_frame",
        "_replaying",
        "_replay_speed",
        "_replay_job",
    )

    def __init__(
        self,
        *,
        result: dict[str, Any] | None = None,
        race_results: list[tuple[str, dict[str, Any]]] | None = None,
        mode: str = "search",
        player: tuple[int, int] = (0, 0),
        playing: bool = False,
        moves: int = 0,
        backtracks: int = 0,
        visited_cells: set[tuple[int, int]] | None = None,
        start_time: float | None = None,
        elapsed: float = 0.0,
        hint: tuple[int, int] | None = None,
        replay_frame: int = 0,
        replaying: bool = False,
        replay_speed: float = 1.0,
        replay_job: str | None = None,
    ) -> None:
        self._result = result
        self._race_results = list(race_results or [])
        self._mode = mode
        self._player = player
        self._playing = playing
        self._moves = moves
        self._backtracks = backtracks
        self._visited_cells = set(visited_cells or {(0, 0)})
        self._start_time = start_time
        self._elapsed = elapsed
        self._hint = hint
        self._replay_frame = replay_frame
        self._replaying = replaying
        self._replay_speed = replay_speed
        self._replay_job = replay_job

    @property
    def result(self) -> dict[str, Any] | None:
        return self._result

    @property
    def race_results(self) -> tuple[tuple[str, dict[str, Any]], ...]:
        return tuple(self._race_results)

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def player(self) -> tuple[int, int]:
        return self._player

    @property
    def playing(self) -> bool:
        return self._playing

    @property
    def moves(self) -> int:
        return self._moves

    @property
    def backtracks(self) -> int:
        return self._backtracks

    @property
    def visited_cells(self) -> frozenset[tuple[int, int]]:
        return frozenset(self._visited_cells)

    @property
    def start_time(self) -> float | None:
        return self._start_time

    @property
    def elapsed(self) -> float:
        return self._elapsed

    @property
    def hint(self) -> tuple[int, int] | None:
        return self._hint

    @property
    def replay_frame(self) -> int:
        return self._replay_frame

    @property
    def replaying(self) -> bool:
        return self._replaying

    @property
    def replay_speed(self) -> float:
        return self._replay_speed

    @property
    def replay_job(self) -> str | None:
        return self._replay_job

    def get(self, key: str, default: Any = None) -> Any:
        if not hasattr(type(self), key):
            return default
        return getattr(self, key)

    def load_result(self, result: dict[str, Any]) -> None:
        self._result = result
        self._race_results = []
        self._mode = "search"
        self.reset_play_session()
        self._replay_frame = 0
        self._replaying = False
        self._replay_job = None

    def prepare_generation_replay(self) -> None:
        self._mode = "generation"
        self._race_results = []
        self._playing = False
        self._replay_frame = 0
        self._replaying = False

    def load_race(
        self,
        rows: list[tuple[str, dict[str, Any]]],
    ) -> None:
        if not rows:
            raise ValueError("race results must not be empty")
        self._result = rows[0][1]
        self._race_results = list(rows)
        self._mode = "race"
        self._playing = False
        self._replay_frame = 0
        self._replaying = False

    def switch_to_search(self) -> None:
        self._mode = "search"
        self._replay_frame = 0

    def reset_play_session(self) -> None:
        self._player = (0, 0)
        self._moves = 0
        self._backtracks = 0
        self._visited_cells = {(0, 0)}
        self._start_time = None
        self._elapsed = 0.0
        self._hint = None
        self._playing = False

    def begin_play(self, now: float) -> None:
        self.reset_play_session()
        self._start_time = now
        self._playing = True

    def finish_play(self, now: float | None = None) -> None:
        if now is not None and self._playing and self._start_time is not None:
            self._elapsed = now - self._start_time
        self._playing = False

    def update_elapsed(self, now: float) -> float:
        if self._playing and self._start_time is not None:
            self._elapsed = now - self._start_time
        return self._elapsed

    def record_move(
        self,
        position: tuple[int, int],
    ) -> None:
        self._moves += 1
        if position in self._visited_cells:
            self._backtracks += 1
        self._visited_cells.add(position)
        self._player = position
        self._hint = None

    def set_hint(self, hint: tuple[int, int]) -> None:
        self._hint = hint

    def clear_hint(self) -> None:
        self._hint = None

    def set_replaying(self, replaying: bool) -> None:
        self._replaying = replaying

    def set_replay_frame(self, frame: int) -> None:
        if frame < 0:
            raise ValueError("replay frame must be non-negative")
        self._replay_frame = frame

    def set_replay_speed(self, speed: float) -> None:
        if speed <= 0:
            raise ValueError("replay speed must be positive")
        self._replay_speed = speed

    def set_replay_job(self, job: str) -> None:
        self._replay_job = job

    def clear_replay_job(self) -> None:
        self._replay_job = None

    def reset_replay(self, mode: str = "search") -> None:
        self._mode = mode
        self._replay_frame = 0
        self._replaying = False
        self._replay_job = None


@dataclass(frozen=True, slots=True)
class MazePlayMetrics:
    moves: int
    elapsed: float
    optimal_steps: int
    extra_steps: int
    loss_percent: float
    efficiency_percent: float
    backtracks: int


@dataclass(frozen=True, slots=True)
class MazeMoveResult:
    moved: bool
    finished: bool
    position: tuple[int, int]


class MazePlaybackController:
    def __init__(
        self,
        state: MazePageState,
        speeds: tuple[float, ...] = DEFAULT_PLAYBACK_SPEEDS,
    ) -> None:
        if not speeds:
            raise ValueError("playback speeds must not be empty")
        self._state = state
        self._speeds = speeds

    def search_trace(self) -> list:
        result = self._state.result
        trace = result.get("trace", []) if isinstance(result, dict) else []
        return trace if isinstance(trace, list) else []

    def generation_trace(self) -> list:
        result = self._state.result
        trace = result.get("generation_trace", []) if isinstance(result, dict) else []
        return trace if isinstance(trace, list) else []

    def total_frames(self) -> int:
        if self._state.mode == "race":
            return max(
                (
                    len(result.get("trace", []))
                    for _, result in self._state.race_results
                ),
                default=0,
            )
        if self._state.mode == "generation":
            return len(self.generation_trace())
        return len(self.search_trace())

    def pause(self) -> None:
        self._state.set_replaying(False)

    def start(self) -> bool:
        total = self.total_frames()
        if total <= 0:
            return False
        if self._state.replay_frame >= total:
            self._state.set_replay_frame(0)
        self._state.set_replaying(True)
        return True

    def reset(self) -> None:
        self.pause()
        self._state.set_replay_frame(0)

    def step(self) -> int:
        self.pause()
        self._state.set_replay_frame(
            min(self._state.replay_frame + 1, self.total_frames())
        )
        return self._state.replay_frame

    def advance(self) -> bool:
        if not self._state.replaying:
            return False
        total = self.total_frames()
        if self._state.replay_frame >= total:
            self._state.set_replaying(False)
            return False
        self._state.set_replay_frame(self._state.replay_frame + 1)
        return True

    def change_speed(self, delta: int) -> float:
        current = self._state.replay_speed
        index = min(
            range(len(self._speeds)),
            key=lambda i: abs(self._speeds[i] - current),
        )
        index = max(0, min(len(self._speeds) - 1, index + delta))
        self._state.set_replay_speed(self._speeds[index])
        return self._state.replay_speed

    def generation_walls(
        self,
        width: int,
        height: int,
        frame: int,
    ) -> list[int]:
        walls = [15] * (width * height)
        for edge in self.generation_trace()[:frame]:
            if not isinstance(edge, (list, tuple)) or len(edge) != 4:
                continue
            ax, ay, bx, by = map(int, edge)
            ai = ay * width + ax
            bi = by * width + bx
            dx = bx - ax
            dy = by - ay
            if dx == 1:
                walls[ai] &= ~EAST
                walls[bi] &= ~WEST
            elif dx == -1:
                walls[ai] &= ~WEST
                walls[bi] &= ~EAST
            elif dy == 1:
                walls[ai] &= ~SOUTH
                walls[bi] &= ~NORTH
            elif dy == -1:
                walls[ai] &= ~NORTH
                walls[bi] &= ~SOUTH
        return walls


class MazePlaySessionController:
    def __init__(self, state: MazePageState) -> None:
        self._state = state

    def start(self, now: float) -> None:
        self._state.begin_play(now)

    def stop(self, now: float | None = None) -> None:
        self._state.finish_play(now)

    def move(
        self,
        result: dict[str, Any],
        dx: int,
        dy: int,
        now: float,
    ) -> MazeMoveResult:
        if not self._state.playing:
            return MazeMoveResult(False, False, self._state.player)

        walls = result.get("walls")
        if not isinstance(walls, list):
            return MazeMoveResult(False, False, self._state.player)

        width = int(result["width"])
        height = int(result["height"])
        x, y = self._state.player
        wall = int(walls[y * width + x])

        if dx == 1:
            required = EAST
        elif dx == -1:
            required = WEST
        elif dy == 1:
            required = SOUTH
        elif dy == -1:
            required = NORTH
        else:
            return MazeMoveResult(False, False, self._state.player)

        next_x = x + dx
        next_y = y + dy
        if wall & required or not (0 <= next_x < width and 0 <= next_y < height):
            return MazeMoveResult(False, False, self._state.player)

        self._state.record_move((next_x, next_y))

        finished = next_x == width - 1 and next_y == height - 1
        if finished:
            self.stop(now)

        return MazeMoveResult(True, finished, self._state.player)

    def metrics(
        self,
        optimal_steps: int,
        now: float | None = None,
    ) -> MazePlayMetrics:
        elapsed = (
            self._state.update_elapsed(now)
            if now is not None
            else self._state.elapsed
        )

        moves = self._state.moves
        extra_steps = max(moves - optimal_steps, 0) if moves else 0
        loss_percent = (
            100.0 * extra_steps / optimal_steps
            if optimal_steps
            else 0.0
        )
        efficiency = (
            100.0 * optimal_steps / moves
            if moves and optimal_steps
            else 0.0
        )
        return MazePlayMetrics(
            moves=moves,
            elapsed=elapsed,
            optimal_steps=optimal_steps,
            extra_steps=extra_steps,
            loss_percent=loss_percent,
            efficiency_percent=efficiency,
            backtracks=self._state.backtracks,
        )

    def next_hint(
        self,
        optimal_path: Iterable[Iterable[int]],
    ) -> tuple[int, int] | None:
        path = [tuple(map(int, point)) for point in optimal_path]
        try:
            index = path.index(self._state.player)
        except ValueError:
            return None
        if index + 1 >= len(path):
            return None
        self._state.set_hint(path[index + 1])
        return self._state.hint


class MazeRaceController:
    @staticmethod
    def race_table(
        rows: list[tuple[str, dict[str, Any]]],
        frame: int | None = None,
    ) -> str:
        if not rows:
            return ""

        head = "AI                    status       steps   loss%   calculations"
        completed: list[tuple[int, str, dict[str, Any]]] = []
        running: list[tuple[str, dict[str, Any]]] = []

        for label, result in rows:
            finish = len(result.get("trace", []))
            if frame is None or frame >= finish:
                completed.append((finish, label, result))
            else:
                running.append((label, result))

        completed.sort(key=lambda item: item[0])
        ranks = {
            label: index + 1
            for index, (_, label, _) in enumerate(completed)
        }

        output = []
        for _, label, result in completed:
            status = "done" if frame is None else f"#{ranks[label]} FINISH"
            output.append(
                f"{label:<21} {status:<11} "
                f"{int(result.get('steps', 0)):>5} "
                f"{float(result.get('loss_percent', 0.0)):>7.1f}% "
                f"{int(result.get('calculation_count', 0)):>12}"
            )

        for label, result in running:
            finish = len(result.get("trace", []))
            progress = f"{min(frame or 0, finish)}/{finish}"
            output.append(
                f"{label:<21} {progress:<11} "
                f"{int(result.get('steps', 0)):>5} "
                f"{float(result.get('loss_percent', 0.0)):>7.1f}% "
                f"{int(result.get('calculation_count', 0)):>12}"
            )

        return head + "\n" + "\n".join(output)

    @staticmethod
    def comparison_table(
        rows: list[tuple[str, dict[str, Any]]],
    ) -> str:
        head = "AI                    steps  loss      loss%    calculations"
        body = []
        for label, result in rows:
            if not result.get("found", False):
                body.append(
                    f"{label:<21} {'FAIL':>5}  {'—':>8}  {'—':>7}  "
                    f"{int(result.get('calculation_count', 0)):>12}"
                )
            else:
                body.append(
                    f"{label:<21} {int(result.get('steps', 0)):>5}  "
                    f"+{int(result.get('extra_steps', 0)):<7}  "
                    f"{float(result.get('loss_percent', 0)):>6.1f}%  "
                    f"{int(result.get('calculation_count', 0)):>12}"
                )
        return head + "\n" + "\n".join(body)
