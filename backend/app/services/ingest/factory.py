from app.core.config import get_settings
from app.schemas.session import SessionCreateRequest, SessionSourceType
from app.services.data.track2 import ensure_game_id_exists, ensure_track2_ready
from app.services.ingest.base import FileIngestSource, IngestSource, RtspIngestSource, WebcamIngestSource
from app.services.ingest.events import EventIngestSource
from app.services.uploads.store import get_upload_store


class IngestFactory:
    """Create ingest source instances based on session payload."""

    @staticmethod
    def build(payload: SessionCreateRequest) -> IngestSource:
        if payload.source_type == SessionSourceType.event_log:
            ensure_track2_ready()
            path = payload.dataset_path or payload.path
            if not path and payload.file_id:
                path = get_upload_store().resolve_path(payload.file_id)
            if not path:
                settings = get_settings()
                path = settings.events_data_path
            if not path:
                raise ValueError("dataset_path or file_id is required for event_log source")
            if not payload.game_id:
                raise ValueError("game_id is required for event_log source")
            ensure_game_id_exists(payload.game_id)
            return EventIngestSource(path, payload.game_id, playback_speed=payload.playback_speed)

        if payload.source_type == SessionSourceType.file:
            path = payload.path
            if not path and payload.file_id:
                path = get_upload_store().resolve_path(payload.file_id)
            if not path:
                raise ValueError("File path is required for file source")
            return FileIngestSource(path, fps=payload.fps)

        if payload.source_type == SessionSourceType.rtsp:
            if not payload.rtsp_url:
                raise ValueError("rtsp_url is required for rtsp source")
            return RtspIngestSource(payload.rtsp_url, fps=payload.fps, buffer_ms=payload.buffer_ms or 300)

        return WebcamIngestSource(device_id=payload.device_id or 0, fps=payload.fps)


ingest_factory = IngestFactory()
