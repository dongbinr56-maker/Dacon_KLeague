from dataclasses import dataclass
from typing import Optional


@dataclass
class EventRecord:
    game_id: str
    game_episode: Optional[int]
    action_id: Optional[int]
    time_seconds: float
    type_name: str
    result_name: str
    start_x: Optional[float]
    start_y: Optional[float]
    end_x: Optional[float]
    end_y: Optional[float]

