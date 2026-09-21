from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence


@dataclass(frozen=True)
class EngineProcess:
    name: str
    timeout_seconds: float = 30.0

    @property
    def executable_name(self) -> str:
        return f"{self.name}.exe" if sys.platform.startswith("win") else self.name

    def resolve(self) -> Path:
        executable_dir = Path(sys.executable).resolve().parent
        packaged = executable_dir / "engines" / self.executable_name
        if packaged.exists():
            return packaged

        repo_root = Path(__file__).resolve().parents[3]
        candidates = (
            repo_root / "build" / "engines" / self.executable_name,
            repo_root / "build" / self.executable_name,
            repo_root / "build" / "Release" / "engines" / self.executable_name,
            repo_root / "build" / "Debug" / "engines" / self.executable_name,
        )
        for candidate in candidates:
            if candidate.exists():
                return candidate

        raise FileNotFoundError(
            f"Engine '{self.name}' was not found. Build it into build/engines/ "
            "for development or package it in engines/ beside the parent app."
        )

    def run_json(
        self,
        arguments: Sequence[str],
        *,
        timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        command = [str(self.resolve()), *arguments]
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=self.timeout_seconds if timeout_seconds is None else timeout_seconds,
        )
        if completed.returncode != 0:
            stderr = completed.stderr.strip()
            raise RuntimeError(
                f"Engine '{self.name}' exited with code {completed.returncode}: "
                f"{stderr or 'no stderr output'}"
            )
        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Engine '{self.name}' returned invalid JSON"
            ) from exc
        if not isinstance(payload, dict):
            raise RuntimeError(
                f"Engine '{self.name}' JSON root must be an object"
            )
        return payload
