from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path


class EventLogger:
    """Structured JSON logger for every simulation event.

    Writes to a timestamped log file in ``logs/`` and keeps an in-memory
    circular buffer for the live visualiser.
    """

    def __init__(self, log_dir: str = "logs", buffer_size: int = 500):
        self.buffer: list[dict] = []
        self.buffer_size = buffer_size

        self._log_dir = Path(log_dir)
        self._log_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self._file = self._log_dir / f"sim_{ts}.jsonl"
        self._handle = open(self._file, "w", buffering=1)  # line-buffered

    def log(self, event: dict) -> None:
        event["_ts"] = datetime.now(timezone.utc).isoformat()
        line = json.dumps(event, default=str)
        self._handle.write(line + "\n")

        self.buffer.append(event)
        if len(self.buffer) > self.buffer_size:
            self.buffer.pop(0)

    def recent(self, n: int = 50) -> list[dict]:
        return self.buffer[-n:]

    def close(self) -> None:
        if self._handle and not self._handle.closed:
            self._handle.close()

    def __del__(self):
        self.close()
