import asyncio
import contextlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

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
            state.ingest_source = ingest_source
        except Exception as exc:  # pragma: no cover - placeholder resilience
            await self._push_status(state, SessionStatus.lost, f"Failed to open source: {exc}")
            return state.session

        await self._push_status(state, SessionStatus.running, "Pipeline started")
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
        state = self._sessions[session_id]
        ingest_source = state.ingest_source
        if ingest_source is None:
            await self._push_status(state, SessionStatus.lost, "Ingest source missing")
            return

        prev_gray: Optional[np.ndarray] = None
        metrics_window: List[Tuple[float, float, float]] = []
        last_eval_ts = 0.0
        window_seconds = 30.0

        try:
            while state.session.status == SessionStatus.running:
                frame_data = await asyncio.to_thread(ingest_source.read_frame)
                if frame_data is None:
                    break
                frame, ts = frame_data
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                if prev_gray is not None:
                    flow = cv2.calcOpticalFlowFarneback(
                        prev_gray, gray, None, 0.5, 3, 15, 3, 5, 1.2, 0
                    )
                    fx = flow[..., 0]
                    fy = flow[..., 1]
                    fx_adj = fx - np.median(fx)
                    fy_adj = fy - np.median(fy)
                    flow_x_bias = float(np.mean(fx_adj) / (np.mean(np.abs(fx_adj)) + 1e-6))
                    motion_intensity = float(np.mean(np.sqrt(fx_adj**2 + fy_adj**2)))

                    metrics_window.append((ts, flow_x_bias, motion_intensity))
                    metrics_window = [m for m in metrics_window if ts - m[0] <= window_seconds]

                    if ts - last_eval_ts >= 1.0:
                        last_eval_ts = ts
                        await self._evaluate_and_alert(
                            state=state,
                            ts=ts,
                            metrics_window=metrics_window,
                            flow_x_bias=flow_x_bias,
                            motion_intensity=motion_intensity,
                        )

                prev_gray = gray
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

    async def _evaluate_and_alert(
        self,
        state: SessionState,
        ts: float,
        metrics_window: List[Tuple[float, float, float]],
        flow_x_bias: float,
        motion_intensity: float,
    ) -> None:
        bias_severity = self._evaluate_bias_window(metrics_window)
        transition_severity, transition_metric = self._evaluate_transition_risk(metrics_window)
        triggered = False

        if bias_severity:
            alert = self._create_alert(
                session_id=state.session.id,
                ts=ts,
                pattern_type="build_up_bias",
                severity=bias_severity,
                metrics={"flow_x_bias": flow_x_bias, "motion_intensity": motion_intensity},
            )
            state.alerts.append(alert)
            triggered = True
            await self._push_status(state, SessionStatus.running, "build_up_bias alert generated")

        if transition_severity:
            alert = self._create_alert(
                session_id=state.session.id,
                ts=ts,
                pattern_type="transition_risk",
                severity=transition_severity,
                metrics={
                    "flow_x_bias": flow_x_bias,
                    "motion_intensity": motion_intensity,
                    "transition_ratio": transition_metric,
                },
            )
            state.alerts.append(alert)
            triggered = True
            await self._push_status(state, SessionStatus.running, "transition_risk alert generated")

        if not triggered and ts >= 30 and not state.alerts and metrics_window:
            fallback_severity = Severity.medium
            alert = self._create_alert(
                session_id=state.session.id,
                ts=ts,
                pattern_type="build_up_bias",
                severity=fallback_severity,
                metrics={"flow_x_bias": flow_x_bias, "motion_intensity": motion_intensity},
            )
            state.alerts.append(alert)
            await self._push_status(state, SessionStatus.running, "fallback alert generated")

    def _evaluate_bias_window(self, metrics_window: List[Tuple[float, float, float]]) -> Severity | None:
        if not metrics_window:
            return None
        biases = [abs(bias) for _, bias, _ in metrics_window]
        count_high = sum(1 for b in biases if b > 0.25)
        count_med = sum(1 for b in biases if b > 0.15)
        window_len = len(biases)

        if window_len >= 10 and count_high >= max(5, int(0.6 * window_len)):
            return Severity.high
        if window_len >= 10 and count_med >= max(6, int(0.4 * window_len)):
            return Severity.medium
        return None

    def _evaluate_transition_risk(
        self, metrics_window: List[Tuple[float, float, float]]
    ) -> Tuple[Severity | None, float]:
        if len(metrics_window) < 12:
            return None, 0.0
        intensities = [m[2] for m in metrics_window]
        recent = intensities[-5:]
        previous = intensities[:-5]
        if not previous:
            return None, 0.0
        base_mean = float(np.mean(previous)) + 1e-6
        recent_mean = float(np.mean(recent))
        ratio = recent_mean / base_mean
        if recent_mean < 0.02:
            return None, ratio
        if ratio > 3.0:
            return Severity.high, ratio
        if ratio > 2.0:
            return Severity.medium, ratio
        return None, ratio

    def _create_alert(
        self,
        session_id: str,
        ts: float,
        pattern_type: str,
        severity: Severity,
        metrics: Dict[str, float],
    ) -> Alert:
        alert_id = str(uuid.uuid4())
        clip_url, overlay_url = evidence_builder.build_evidence(
            session_id=session_id,
            alert_id=alert_id,
            video_path=self._sessions[session_id].session.source_uri,
            ts_center=ts,
            pattern_type=pattern_type,
            severity=severity.value,
            metrics=metrics,
        )
        evidence_metrics = {
            key: EvidenceMetric(name=key, value=value) for key, value in metrics.items()
        }
        claim = "최근 전개가 우측으로 치우치고 있습니다." if pattern_type == "build_up_bias" else "전환 속도가 급격히 증가하고 있습니다."
        recommendation = (
            "좌측 혹은 중앙 전환을 섞어 압박 균형을 무너뜨리세요."
            if pattern_type == "build_up_bias"
            else "급격한 전환 구간에서 안정적으로 볼을 순환하세요."
        )
        risk = (
            "우측에서 볼을 잃을 시 역습 위험이 높습니다."
            if pattern_type == "build_up_bias"
            else "지속적인 전환 압박으로 인한 실점 위험이 있습니다."
        )

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
