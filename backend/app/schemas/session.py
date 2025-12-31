from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class SessionSourceType(str, Enum):
    file = "file"
    rtsp = "rtsp"
    webcam = "webcam"


class SessionMode(str, Enum):
    offline_realtime = "offline_realtime"
    live = "live"


class SessionStatus(str, Enum):
    created = "CREATED"
    connecting = "CONNECTING"
    running = "RUNNING"
    lost = "LOST"
    stopped = "STOPPED"


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class EvidenceMetric(BaseModel):
    name: str
    value: float
    unit: Optional[str] = None


class Evidence(BaseModel):
    clips: List[str] = Field(default_factory=list)
    overlays: List[str] = Field(default_factory=list)
    metrics: Dict[str, EvidenceMetric] = Field(default_factory=dict)


class Alert(BaseModel):
    id: str
    ts_start: float
    ts_end: float
    pattern_type: str
    severity: Severity
    claim_text: str
    recommendation_text: str
    risk_text: str
    evidence: Evidence


class SessionCreateRequest(BaseModel):
    source_type: SessionSourceType
    mode: SessionMode = SessionMode.offline_realtime
    fps: int = Field(default=25, ge=1, le=60)
    buffer_ms: Optional[int] = Field(default=300, ge=0)
    path: Optional[str] = None
    rtsp_url: Optional[str] = None
    device_id: Optional[int] = Field(default=0, ge=0)
    file_id: Optional[str] = None


class Session(BaseModel):
    id: str
    created_at: datetime
    status: SessionStatus
    source_type: SessionSourceType
    mode: SessionMode
    fps: int
    source_uri: str
    buffer_ms: Optional[int] = None


class SessionStatusEvent(BaseModel):
    session_id: str
    status: SessionStatus
    timestamp: datetime
    detail: Optional[str] = None


class SessionsResponse(BaseModel):
    sessions: List[Session]


class AlertsResponse(BaseModel):
    alerts: List[Alert]


class StartSessionRequest(BaseModel):
    target_status: SessionStatus = SessionStatus.running


class StopSessionRequest(BaseModel):
    reason: Optional[str] = None
