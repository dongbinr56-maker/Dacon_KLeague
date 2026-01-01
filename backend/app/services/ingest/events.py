import csv
import time
from typing import List, Optional, Tuple

from app.schemas.event import EventRecord
from app.services.ingest.base import IngestSource


class EventIngestSource(IngestSource):
    """Stream event rows as if they were frames, ordered by time_seconds."""

    def __init__(self, csv_path: str, game_id: str, playback_speed: float = 5.0) -> None:
        self.csv_path = csv_path
        self.game_id = game_id
        self.playback_speed = playback_speed if playback_speed > 0 else 1.0
        self._events: List[EventRecord] = []
        self._cursor = 0
        self._last_ts: Optional[float] = None

    def open(self) -> None:
        self._load_events()
        self._cursor = 0
        self._last_ts = None

    def read_frame(self) -> Optional[Tuple[EventRecord, float]]:
        if self._cursor >= len(self._events):
            return None

        event = self._events[self._cursor]
        self._cursor += 1
        current_ts = float(event.time_seconds)

        if self._last_ts is not None:
            delta = (current_ts - self._last_ts) / self.playback_speed
            if delta > 0:
                time.sleep(min(delta, 0.2))
        self._last_ts = current_ts
        return event, current_ts

    def close(self) -> None:
        self._events = []
        self._cursor = 0
        self._last_ts = None

    def _load_events(self) -> None:
        with open(self.csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = [
                row
                for row in reader
                if row.get("game_id") == self.game_id
            ]
        events: List[EventRecord] = []
        for row in rows:
            try:
                start_x = _try_float(row.get("start_x"))
                start_y = _try_float(row.get("start_y"))
                end_x = _try_float(row.get("end_x"))
                end_y = _try_float(row.get("end_y"))
                
                # dx, dy 계산 (Track2에 있으면 사용, 없으면 계산)
                dx = _try_float(row.get("dx"))
                dy = _try_float(row.get("dy"))
                if dx is None and start_x is not None and end_x is not None:
                    dx = end_x - start_x
                if dy is None and start_y is not None and end_y is not None:
                    dy = end_y - start_y
                
                events.append(
                    EventRecord(
                        game_id=row.get("game_id", ""),
                        game_episode=_try_int(row.get("game_episode")),
                        action_id=_try_int(row.get("action_id")),
                        time_seconds=float(row.get("time_seconds", 0.0)),
                        type_name=row.get("type_name", ""),
                        result_name=row.get("result_name", ""),
                        start_x=start_x,
                        start_y=start_y,
                        end_x=end_x,
                        end_y=end_y,
                        team_id=_try_int(row.get("team_id")),
                        player_id=_try_int(row.get("player_id")),
                        period_id=_try_int(row.get("period_id")),
                        dx=dx,
                        dy=dy,
                    )
                )
            except ValueError:
                continue
        events.sort(key=lambda e: (e.time_seconds, e.action_id or 0))
        self._events = events


def _try_float(value: Optional[str]) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _try_int(value: Optional[str]) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except ValueError:
        return None
