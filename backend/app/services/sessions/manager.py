import asyncio
import contextlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from app.core.config import get_settings
from app.schemas.event import EventRecord
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
    Severity,
)
from app.services.evidence.builder import evidence_builder
from app.services.ingest.base import IngestSource
from app.services.ingest.factory import ingest_factory
from app.services.uploads.store import upload_store


@dataclass
class SessionState:
    session: Session
    session_create_payload: SessionCreateRequest
    alerts: List[Alert] = field(default_factory=list)
    status_events: List[SessionStatusEvent] = field(default_factory=list)
    task: asyncio.Task | None = None
    ingest_source: Optional[IngestSource] = None
    last_pattern_ts: Dict[str, float] = field(default_factory=dict)


class SessionManager:
    def __init__(self) -> None:
        self._sessions: Dict[str, SessionState] = {}
        self._lock = asyncio.Lock()
        self._settings = get_settings()

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
                game_id=payload.game_id,
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
            state.ingest_source = ingest_source
        except Exception as exc:  # pragma: no cover - placeholder resilience
            await self._push_status(state, SessionStatus.lost, f"Failed to open source: {exc}")
            return state.session

        await self._push_status(state, SessionStatus.running, "Pipeline started")
        if state.session_create_payload.source_type == SessionSourceType.event_log:
            state.task = asyncio.create_task(self._run_event_realtime(session_id))
        else:
            state.task = asyncio.create_task(self._run_offline_realtime(session_id))
        return state.session

    async def stop_session(self, session_id: str, reason: str | None = None) -> Session:
        state = self._sessions[session_id]
        if state.task and not state.task.done():
            state.task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await state.task
        if state.ingest_source:
            state.ingest_source.close()
            state.ingest_source = None
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

    async def _run_offline_realtime(self, session_id: str) -> None:
        """Fallback pipeline for non-event sources; emits a stub alert to keep demo resilient."""
        state = self._sessions[session_id]
        ingest_source = state.ingest_source
        try:
            await asyncio.sleep(3)
            alert = self._create_alert(
                session_id=session_id,
                ts=5.0,
                pattern_type="build_up_bias",
                severity=Severity.medium,
                metrics={"flow_x_bias": 0.2},
                events_slice=[],
            )
            state.alerts.append(alert)
            await self._push_status(state, SessionStatus.running, "Fallback alert generated")
        except asyncio.CancelledError:  # pragma: no cover
            pass
        finally:
            if ingest_source:
                ingest_source.close()
                state.ingest_source = None
            if state.session.status != SessionStatus.stopped:
                await self._push_status(state, SessionStatus.stopped, "Stream completed")
            state.task = None

    async def _run_event_realtime(self, session_id: str) -> None:
        state = self._sessions[session_id]
        ingest_source = state.ingest_source
        if ingest_source is None:
            await self._push_status(state, SessionStatus.lost, "Ingest source missing")
            return

        window: List[EventRecord] = []
        last_eval_ts = 0.0
        window_seconds = 45.0

        try:
            while state.session.status == SessionStatus.running:
                frame_data = await asyncio.to_thread(ingest_source.read_frame)
                if frame_data is None:
                    break
                event, ts = frame_data
                if not isinstance(event, EventRecord):
                    continue
                window.append(event)
                window = [ev for ev in window if ts - ev.time_seconds <= window_seconds]

                if ts - last_eval_ts >= 1.0:
                    last_eval_ts = ts
                    await self._evaluate_event_alerts(state, window, ts)
                await asyncio.sleep(0)
        except asyncio.CancelledError:  # pragma: no cover - cooperative cancel
            pass
        finally:
            ingest_source.close()
            state.ingest_source = None
            if state.session.status != SessionStatus.stopped:
                await self._push_status(state, SessionStatus.stopped, "Stream completed")
            state.task = None

    def _resolve_source_uri(self, payload: SessionCreateRequest) -> str:
        if payload.source_type == SessionSourceType.event_log:
            settings = get_settings()
            if payload.dataset_path:
                return payload.dataset_path
            if payload.path:
                return payload.path
            if payload.file_id:
                return upload_store.resolve_path(payload.file_id) or payload.file_id
            return settings.events_data_path
        if payload.source_type == SessionSourceType.file:
            if payload.path:
                return payload.path
            if payload.file_id:
                return upload_store.resolve_path(payload.file_id) or payload.file_id
            return ""
        if payload.source_type == SessionSourceType.rtsp:
            return payload.rtsp_url or ""
        return f"webcam://{payload.device_id}"

    def _resolve_download_url(self, payload: SessionCreateRequest) -> str | None:
        if payload.source_type != SessionSourceType.file:
            return None
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

    async def _evaluate_event_alerts(self, state: SessionState, window: List[EventRecord], ts: float) -> None:
        patterns_triggered = False
        build_up = self._detect_build_up_bias(window)
        if build_up:
            severity, metrics = build_up
            if self._should_emit(state, "build_up_bias", ts):
                alert = self._try_create_alert(
                    session_id=state.session.id,
                    ts=ts,
                    pattern_type="build_up_bias",
                    severity=severity,
                    metrics=metrics,
                    events_slice=self._events_for_evidence(window, ts),
                )
                if alert:
                    state.alerts.append(alert)
                    state.last_pattern_ts["build_up_bias"] = ts
                    patterns_triggered = True
                    await self._push_status(state, SessionStatus.running, "build_up_bias alert generated")

        transition = self._detect_transition_risk(window)
        if transition:
            severity, metrics = transition
            if self._should_emit(state, "transition_risk", ts):
                alert = self._try_create_alert(
                    session_id=state.session.id,
                    ts=ts,
                    pattern_type="transition_risk",
                    severity=severity,
                    metrics=metrics,
                    events_slice=self._events_for_evidence(window, ts),
                )
                if alert:
                    state.alerts.append(alert)
                    state.last_pattern_ts["transition_risk"] = ts
                    patterns_triggered = True
                    await self._push_status(state, SessionStatus.running, "transition_risk alert generated")

        pressure = self._detect_final_third_pressure(window)
        if pressure:
            severity, metrics = pressure
            if self._should_emit(state, "final_third_pressure", ts):
                alert = self._try_create_alert(
                    session_id=state.session.id,
                    ts=ts,
                    pattern_type="final_third_pressure",
                    severity=severity,
                    metrics=metrics,
                    events_slice=self._events_for_evidence(window, ts),
                )
                if alert:
                    state.alerts.append(alert)
                    state.last_pattern_ts["final_third_pressure"] = ts
                    patterns_triggered = True
                await self._push_status(state, SessionStatus.running, "final_third_pressure alert generated")

        if not patterns_triggered and ts >= 30 and not state.alerts and window:
            if self._settings.demo_mode:
                metrics = self._demo_metrics(window)
            else:
                metrics = {"event_count": float(len(window))}
            alert = self._try_create_alert(
                session_id=state.session.id,
                ts=ts,
                pattern_type="build_up_bias",
                severity=Severity.medium,
                metrics=metrics,
                events_slice=self._events_for_evidence(window, ts),
            )
            if alert:
                state.alerts.append(alert)
                state.last_pattern_ts["build_up_bias"] = ts
                await self._push_status(state, SessionStatus.running, "fallback alert generated")

    def _detect_build_up_bias(self, window: List[EventRecord]) -> Optional[Tuple[Severity, Dict[str, float]]]:
        passes = [
            ev
            for ev in window
            if (ev.type_name or "").lower() in {"pass", "carry"} and ev.start_x is not None and ev.end_x is not None
        ]
        if len(passes) < 8:
            return None
        dx = [ev.end_x - ev.start_x for ev in passes]
        mean_dx = sum(dx) / len(dx)
        right_channel = sum(1 for ev in passes if ev.start_y is not None and ev.start_y > (68 * 2 / 3))
        left_channel = sum(1 for ev in passes if ev.start_y is not None and ev.start_y < (68 / 3))
        total_channel = right_channel + left_channel + sum(
            1 for ev in passes if ev.start_y is not None and (68 / 3) <= ev.start_y <= (68 * 2 / 3)
        )
        right_ratio = right_channel / total_channel if total_channel else 0.0
        metrics = {
            "mean_dx": float(mean_dx),
            "right_channel_ratio": float(right_ratio),
            "event_count": float(len(passes)),
        }
        severity: Optional[Severity] = None
        if abs(mean_dx) > 8 or right_ratio > 0.6:
            severity = Severity.high
        elif abs(mean_dx) > 5 or right_ratio > 0.5:
            severity = Severity.medium
        return (severity, metrics) if severity else None

    def _detect_transition_risk(self, window: List[EventRecord]) -> Optional[Tuple[Severity, Dict[str, float]]]:
        if not window:
            return None
        turnover_candidates = [
            ev
            for ev in window
            if (ev.result_name or "").lower() == "unsuccessful"
            or "turnover" in (ev.type_name or "").lower()
        ]
        if not turnover_candidates:
            return None
        last_turnover = max(turnover_candidates, key=lambda ev: ev.time_seconds)
        followups = [
            ev
            for ev in window
            if last_turnover.time_seconds < ev.time_seconds <= last_turnover.time_seconds + 8
            and (ev.type_name.lower() == "shot" or (ev.end_x is not None and ev.end_x > 88))
        ]
        if not followups:
            return None
        metrics = {
            "turnover_x": float(last_turnover.end_x or last_turnover.start_x or 0.0),
            "followup_attack_count": float(len(followups)),
        }
        severity = Severity.high if len(followups) >= 2 else Severity.medium
        return severity, metrics

    def _detect_final_third_pressure(self, window: List[EventRecord]) -> Optional[Tuple[Severity, Dict[str, float]]]:
        entries = [ev for ev in window if ev.end_x is not None and ev.end_x > 70]
        if len(entries) < 5:
            return None
        metrics = {"final_third_entries": float(len(entries))}
        severity = Severity.high if len(entries) >= 10 else Severity.medium
        return severity, metrics

    def _events_for_evidence(self, window: List[EventRecord], ts: float) -> List[EventRecord]:
        return [ev for ev in window if abs(ev.time_seconds - ts) <= 5]

    def _should_emit(self, state: SessionState, pattern_type: str, ts: float, cooldown: float = 8.0) -> bool:
        last_ts = state.last_pattern_ts.get(pattern_type)
        if last_ts is None:
            return True
        return (ts - last_ts) >= cooldown

    def _demo_metrics(self, window: List[EventRecord]) -> Dict[str, float]:
        dx = [ev.end_x - ev.start_x for ev in window if ev.start_x is not None and ev.end_x is not None]
        mean_dx = float(sum(dx) / len(dx)) if dx else 0.0
        right_entries = [ev for ev in window if ev.end_x and ev.end_x > 70]
        shots = [ev for ev in window if (ev.type_name or "").lower() == "shot"]
        return {
            "event_count": float(len(window)),
            "mean_dx": mean_dx,
            "final_third_entries": float(len(right_entries)),
            "shot_count": float(len(shots)),
        }

    def _try_create_alert(
        self,
        session_id: str,
        ts: float,
        pattern_type: str,
        severity: Severity,
        metrics: Dict[str, float],
        events_slice: List[EventRecord],
    ) -> Alert | None:
        alert_id = str(uuid.uuid4())
        try:
            clip_url, overlay_url = evidence_builder.build_evidence(
                session_id=session_id,
                alert_id=alert_id,
                ts_center=ts,
                pattern_type=pattern_type,
                severity=severity.value,
                metrics=metrics,
                events=events_slice,
            )
        except Exception as exc:  # noqa: BLE001 - defensive path to avoid publishing without evidence
            detail = f"evidence_generation_failed: {exc}"
            asyncio.create_task(self._push_status(self._sessions[session_id], SessionStatus.running, detail))
            return None
        evidence_metrics = {key: EvidenceMetric(name=key, value=value) for key, value in metrics.items()}
        if pattern_type == "build_up_bias":
            claim = "최근 전개가 우측으로 치우치고 있습니다."
            recommendation = "좌측 혹은 중앙 전환을 섞어 압박 균형을 무너뜨리세요."
            risk = "우측에서 볼을 잃을 시 역습 위험이 높습니다."
        elif pattern_type == "transition_risk":
            claim = "턴오버 직후 전환 압박이 증가했습니다."
            recommendation = "턴오버 직후 안정화 패턴을 가동해 위험 구간을 줄이세요."
            risk = "지속적인 전환 압박으로 인한 실점 위험이 있습니다."
        else:
            claim = "상대가 파이널 서드 진입을 반복하고 있습니다."
            recommendation = "박스 근처 압박 라인을 재정렬해 진입 빈도를 낮추세요."
            risk = "박스 부근 진입이 누적되면 실점 확률이 높아집니다."

        return Alert(
            id=alert_id,
            ts_start=max(0.0, ts - 5.0),
            ts_end=ts,
            pattern_type=pattern_type,
            severity=severity,
            claim_text=claim,
            recommendation_text=recommendation,
            risk_text=risk,
            evidence=Evidence(
                clips=[clip_url],
                overlays=[overlay_url],
                metrics=evidence_metrics,
            ),
        )


session_manager = SessionManager()
