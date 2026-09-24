from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable


NORTH, EAST, SOUTH, WEST = 1, 2, 4, 8
DEFAULT_PLAYBACK_SPEEDS = (0.25, 0.5, 1.0, 2.0, 4.0)


@dataclass
class MazePageState:
    result: dict[str, Any] | None = None
    race_results: list[tuple[str, dict[str, Any]]] = field(default_factory=list)
    mode: str = "search"
    player: tuple[int, int] = (0, 0)
    playing: bool = False
    moves: int = 0
    backtracks: int = 0
    visited_cells: set[tuple[int, int]] = field(default_factory=lambda: {(0, 0)})
    start_time: float | None = None
    elapsed: float = 0.0
    hint: tuple[int, int] | None = None
    replay_frame: int = 0
    replaying: bool = False
    replay_speed: float = 1.0
    replay_job: str | None = None

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def __getitem__(self, key: str) -> Any:
        if not hasattr(self, key):
            raise KeyError(key)
        return getattr(self, key)

    def __setitem__(self, key: str, value: Any) -> None:
        if not hasattr(self, key):
            raise KeyError(key)
        setattr(self, key, value)

    def update(self, values: dict[str, Any]) -> None:
        for key, value in values.items():
            self[key] = value

    def reset_play_session(self) -> None:
        self.player = (0, 0)
        self.moves = 0
        self.backtracks = 0
        self.visited_cells = {(0, 0)}
        self.start_time = None
        self.elapsed = 0.0
        self.hint = None
        self.playing = False

    def reset_replay(self, mode: str = "search") -> None:
        self.mode = mode
        self.replay_frame = 0
        self.replaying = False
        self.replay_job = None


@dataclass(frozen=True)
class MazePlayMetrics:
    moves: int
    elapsed: float
    optimal_steps: int
    extra_steps: int
    loss_percent: float
    efficiency_percent: float
    backtracks: int


@dataclass(frozen=True)
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
        self._state.replaying = False

    def start(self) -> bool:
        total = self.total_frames()
        if total <= 0:
            return False
        if self._state.replay_frame >= total:
            self._state.replay_frame = 0
        self._state.replaying = True
        return True

    def reset(self) -> None:
        self.pause()
        self._state.replay_frame = 0

    def step(self) -> int:
        self.pause()
        self._state.replay_frame = min(
            self._state.replay_frame + 1,
            self.total_frames(),
        )
        return self._state.replay_frame

    def advance(self) -> bool:
        if not self._state.replaying:
            return False
        total = self.total_frames()
        if self._state.replay_frame >= total:
            self._state.replaying = False
            return False
        self._state.replay_frame += 1
        return True

    def change_speed(self, delta: int) -> float:
        current = self._state.replay_speed
        index = min(
            range(len(self._speeds)),
            key=lambda i: abs(self._speeds[i] - current),
        )
        index = max(0, min(len(self._speeds) - 1, index + delta))
        self._state.replay_speed = self._speeds[index]
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
        self._state.player = (0, 0)
        self._state.moves = 0
        self._state.backtracks = 0
        self._state.visited_cells = {(0, 0)}
        self._state.elapsed = 0.0
        self._state.start_time = now
        self._state.playing = True
        self._state.hint = None

    def stop(self, now: float | None = None) -> None:
        if (
            now is not None
            and self._state.playing
            and self._state.start_time is not None
        ):
            self._state.elapsed = now - self._state.start_time
        self._state.playing = False

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

        self._state.moves += 1
        if (next_x, next_y) in self._state.visited_cells:
            self._state.backtracks += 1
        self._state.visited_cells.add((next_x, next_y))
        self._state.player = (next_x, next_y)
        self._state.hint = None

        finished = next_x == width - 1 and next_y == height - 1
        if finished:
            self.stop(now)

        return MazeMoveResult(True, finished, self._state.player)

    def metrics(
        self,
        optimal_steps: int,
        now: float | None = None,
    ) -> MazePlayMetrics:
        elapsed = self._state.elapsed
        if (
            now is not None
            and self._state.playing
            and self._state.start_time is not None
        ):
            elapsed = now - self._state.start_time
            self._state.elapsed = elapsed

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

    def next_hint(self, optimal_path: Iterable[Iterable[int]]) -> tuple[int, int] | None:
        path = [tuple(map(int, point)) for point in optimal_path]
        try:
            index = path.index(self._state.player)
        except ValueError:
            return None
        if index + 1 >= len(path):
            return None
        self._state.hint = path[index + 1]
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
    def comparison_table(rows: list[tuple[str, dict[str, Any]]]) -> str:
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
