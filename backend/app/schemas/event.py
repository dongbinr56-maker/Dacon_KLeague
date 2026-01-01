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
    # Track2 스키마 확장 필드
    team_id: Optional[int] = None
    player_id: Optional[int] = None
    period_id: Optional[int] = None
    dx: Optional[float] = None
    dy: Optional[float] = None

