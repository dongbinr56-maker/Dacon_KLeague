from fastapi import APIRouter, HTTPException, Query

from app.services.data.track2 import ensure_game_id_exists, list_game_ids

router = APIRouter()


@router.get("/games")
async def games(recommend: bool = Query(default=False)) -> dict:
    try:
        return {"games": list_game_ids(recommend=recommend)}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/games/{game_id}")
async def game_exists(game_id: str) -> dict:
    ensure_game_id_exists(game_id)
    return {"game_id": game_id, "exists": True}
