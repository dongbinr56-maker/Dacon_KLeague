from fastapi import APIRouter, HTTPException

from app.schemas.session import (
    AlertsResponse,
    Session,
    SessionCreateRequest,
    SessionsResponse,
    StartSessionRequest,
    StopSessionRequest,
)
from app.services.sessions.manager import session_manager

router = APIRouter()


@router.post("/", response_model=Session)
async def create_session(payload: SessionCreateRequest) -> Session:
    return await session_manager.create_session(payload)


@router.post("/{session_id}/start", response_model=Session)
async def start_session(session_id: str, payload: StartSessionRequest | None = None) -> Session:
    try:
        return await session_manager.start_session(session_id)
    except KeyError as exc:  # pragma: no cover - defensive path
        raise HTTPException(status_code=404, detail="Session not found") from exc


@router.post("/{session_id}/stop", response_model=Session)
async def stop_session(session_id: str, payload: StopSessionRequest | None = None) -> Session:
    try:
        return await session_manager.stop_session(session_id, reason=payload.reason if payload else None)
    except KeyError as exc:  # pragma: no cover
        raise HTTPException(status_code=404, detail="Session not found") from exc


@router.get("/", response_model=SessionsResponse)
async def list_sessions() -> SessionsResponse:
    sessions = await session_manager.list_sessions()
    return SessionsResponse(sessions=sessions)


@router.get("/{session_id}/alerts", response_model=AlertsResponse)
async def alerts(session_id: str) -> AlertsResponse:
    try:
        return await session_manager.get_alerts(session_id)
    except KeyError as exc:  # pragma: no cover
        raise HTTPException(status_code=404, detail="Session not found") from exc
