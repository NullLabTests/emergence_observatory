from __future__ import annotations
import json
import os
from pathlib import Path
from datetime import datetime, timezone


class Recorder:
    """Records every agent interaction as JSONL for replay.

    One file per simulation run, timestamped.
    """

    def __init__(self, base_path: str = "data/replay"):
        self._dir = Path(base_path)
        self._dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self._path = self._dir / f"run_{ts}.jsonl"
        self._buffer: list[str] = []

    def record(self, event: dict) -> None:
        line = json.dumps(event, default=str)
        self._buffer.append(line)
        if len(self._buffer) >= 10:
            self.flush()

    def flush(self) -> None:
        if not self._buffer:
            return
        with open(self._path, "a") as f:
            f.write("\n".join(self._buffer) + "\n")
        self._buffer.clear()

    def close(self) -> None:
        self.flush()

    @property
    def path(self) -> str:
        return str(self._path)
