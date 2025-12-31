import csv
import os
from typing import Dict, List, Set

from fastapi import HTTPException

from app.core.config import get_settings

REQUIRED_EVENT_COLUMNS: Set[str] = {
    "game_id",
    "game_episode",
    "action_id",
    "time_seconds",
    "type_name",
    "result_name",
    "start_x",
    "start_y",
    "end_x",
    "end_y",
}


def _ensure_file(path: str, label: str) -> None:
    if not os.path.exists(path):
        raise FileNotFoundError(f"{label} 파일이 존재하지 않습니다: {path}")


def _ensure_columns(path: str, label: str, required: Set[str]) -> None:
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = set(reader.fieldnames or [])
    missing = required - headers
    if missing:
        raise ValueError(f"{label}에 필요한 컬럼이 없습니다: {', '.join(sorted(missing))}")


def validate_track2_data() -> Dict[str, str]:
    settings = get_settings()
    _ensure_file(settings.events_data_path, "Track2 raw_data")
    _ensure_file(settings.match_info_path, "Track2 match_info")
    _ensure_columns(settings.events_data_path, "Track2 raw_data", REQUIRED_EVENT_COLUMNS)
    return {
        "events_data_path": settings.events_data_path,
        "match_info_path": settings.match_info_path,
    }


def ensure_track2_ready() -> Dict[str, str]:
    try:
        return validate_track2_data()
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def list_game_ids(limit: int | None = None) -> List[Dict[str, str]]:
    """Return available game_id list with optional metadata from match_info."""
    settings = get_settings()
    _ensure_file(settings.events_data_path, "Track2 raw_data")

    game_ids: List[str] = []
    with open(settings.events_data_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        seen = set()
        for row in reader:
            gid = row.get("game_id")
            if gid and gid not in seen:
                seen.add(gid)
                game_ids.append(gid)
                if limit and len(game_ids) >= limit:
                    break

    meta: Dict[str, Dict[str, str]] = {}
    if os.path.exists(settings.match_info_path):
        with open(settings.match_info_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                gid = row.get("game_id")
                if gid:
                    meta[gid] = {
                        "home_team": row.get("home_team", ""),
                        "away_team": row.get("away_team", ""),
                        "match_date": row.get("match_date", ""),
                        "stadium": row.get("stadium", ""),
                    }

    result: List[Dict[str, str]] = []
    for gid in game_ids:
        info = meta.get(gid, {})
        result.append(
            {
                "game_id": gid,
                "home_team": info.get("home_team", ""),
                "away_team": info.get("away_team", ""),
                "match_date": info.get("match_date", ""),
                "stadium": info.get("stadium", ""),
            }
        )
    return result


def ensure_game_id_exists(game_id: str) -> None:
    settings = get_settings()
    try:
        _ensure_file(settings.events_data_path, "Track2 raw_data")
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    with open(settings.events_data_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("game_id") == game_id:
                return
    raise HTTPException(status_code=404, detail=f"game_id '{game_id}'를 raw_data에서 찾을 수 없습니다.")
