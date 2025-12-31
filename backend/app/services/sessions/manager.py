import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List

from app.schemas.session import (
    Alert,
    AlertsResponse,
    Evidence,
    EvidenceMetric,
    Session,
    SessionCreateRequest,
    SessionMode,
    SessionSourceType,
    SessionStatus,
    SessionStatusEvent,
)
from app.services.ingest.factory import ingest_factory
from app.services.uploads.store import upload_store


@dataclass
class SessionState:
    session: Session
    session_create_payload: SessionCreateRequest
    alerts: List[Alert] = field(default_factory=list)
    status_events: List[SessionStatusEvent] = field(default_factory=list)
    task: asyncio.Task | None = None


class SessionManager:
    def __init__(self) -> None:
        self._sessions: Dict[str, SessionState] = {}
        self._lock = asyncio.Lock()

    async def create_session(self, payload: SessionCreateRequest) -> Session:
        async with self._lock:
            session_id = str(uuid.uuid4())
            source_uri = self._resolve_source_uri(payload)
            session = Session(
                id=session_id,
                created_at=datetime.utcnow(),
                status=SessionStatus.created,
                source_type=payload.source_type,
                mode=payload.mode,
                fps=payload.fps,
                buffer_ms=payload.buffer_ms,
                source_uri=source_uri,
                download_url=self._resolve_download_url(payload),
            )
            state = SessionState(session=session, session_create_payload=payload)
            self._sessions[session_id] = state
            await self._push_status(state, SessionStatus.created, "Session created")
            return session

    async def start_session(self, session_id: str) -> Session:
        state = self._sessions[session_id]
        if state.session.status in {SessionStatus.running, SessionStatus.lost}:
            return state.session
        await self._push_status(state, SessionStatus.connecting, "Connecting to source")
        await asyncio.sleep(0.05)
        try:
            ingest_source = ingest_factory.build(state.session_create_payload)
            ingest_source.open()
        except Exception as exc:  # pragma: no cover - placeholder resilience
            await self._push_status(state, SessionStatus.lost, f"Failed to open source: {exc}")
            return state.session

        await self._push_status(state, SessionStatus.running, "Pipeline started")
        state.task = asyncio.create_task(self._simulate_analysis(session_id))
        return state.session

    async def stop_session(self, session_id: str, reason: str | None = None) -> Session:
        state = self._sessions[session_id]
        if state.task and not state.task.done():
            state.task.cancel()
        await self._push_status(state, SessionStatus.stopped, reason or "Stopped")
        return state.session

    async def list_sessions(self) -> List[Session]:
        return [s.session for s in self._sessions.values()]

    async def get_session(self, session_id: str) -> Session:
        state = self._sessions[session_id]
        return state.session

    async def get_alerts(self, session_id: str) -> AlertsResponse:
        state = self._sessions[session_id]
        return AlertsResponse(alerts=state.alerts)

    async def status_events(self, session_id: str) -> List[SessionStatusEvent]:
        state = self._sessions[session_id]
        return state.status_events

    async def _simulate_analysis(self, session_id: str) -> None:
        state = self._sessions[session_id]
        delay = 3
        while state.session.status == SessionStatus.running:
            await asyncio.sleep(delay)
            alert = self._make_placeholder_alert(session_id)
            state.alerts.append(alert)
            await self._push_status(state, SessionStatus.running, "Alert generated")

    def _make_placeholder_alert(self, session_id: str) -> Alert:
        ts = datetime.utcnow().timestamp()
        return Alert(
            id=str(uuid.uuid4()),
            ts_start=ts - 5,
            ts_end=ts,
            pattern_type="build_up_bias",
            severity="medium",
            claim_text="최근 전개가 우측으로 치우치고 있습니다.",
            recommendation_text="좌측 혹은 중앙 전환을 섞어 압박 균형을 무너뜨리세요.",
            risk_text="우측에서 볼을 잃을 시 역습 위험이 높습니다.",
            evidence=Evidence(
                clips=[f"/evidence/{session_id}/clip_placeholder.mp4"],
                overlays=[f"/evidence/{session_id}/overlay_placeholder.png"],
                metrics={
                    "right_bias_rate": EvidenceMetric(
                        name="right_bias_rate", value=0.72, unit="ratio"
                    ),
                    "line_height": EvidenceMetric(
                        name="line_height", value=43.2, unit="meters"
                    ),
                },
            ),
        )

    def _resolve_source_uri(self, payload: SessionCreateRequest) -> str:
        if payload.source_type == SessionSourceType.file:
            return payload.path or payload.file_id or ""
        if payload.source_type == SessionSourceType.rtsp:
            return payload.rtsp_url or ""
        return f"webcam://{payload.device_id}"

    def _resolve_download_url(self, payload: SessionCreateRequest) -> str | None:
        if payload.source_type != SessionSourceType.file:
            return None
        if payload.path:
            return payload.path
        if payload.file_id:
            return upload_store.resolve_download_url(payload.file_id)
        return None

    async def _push_status(self, state: SessionState, status: SessionStatus, detail: str) -> None:
        state.session.status = status
        event = SessionStatusEvent(
            session_id=state.session.id,
            status=status,
            timestamp=datetime.utcnow(),
            detail=detail,
        )
        state.status_events.append(event)


session_manager = SessionManager()
