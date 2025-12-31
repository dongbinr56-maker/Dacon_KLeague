from app.schemas.session import SessionCreateRequest, SessionSourceType
from app.services.ingest.base import FileIngestSource, IngestSource, RtspIngestSource, WebcamIngestSource
from app.services.uploads.store import upload_store


class IngestFactory:
    """Create ingest source instances based on session payload."""

    @staticmethod
    def build(payload: SessionCreateRequest) -> IngestSource:
        if payload.source_type == SessionSourceType.file:
            path = payload.path
            if not path and payload.file_id:
                path = upload_store.resolve_path(payload.file_id)
            if not path:
                raise ValueError("File path is required for file source")
            return FileIngestSource(path, fps=payload.fps)

        if payload.source_type == SessionSourceType.rtsp:
            if not payload.rtsp_url:
                raise ValueError("rtsp_url is required for rtsp source")
            return RtspIngestSource(payload.rtsp_url, fps=payload.fps, buffer_ms=payload.buffer_ms or 300)

        return WebcamIngestSource(device_id=payload.device_id or 0, fps=payload.fps)


ingest_factory = IngestFactory()
