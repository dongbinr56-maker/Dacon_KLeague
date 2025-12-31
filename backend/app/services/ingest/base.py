from abc import ABC, abstractmethod
from typing import Optional, Tuple

import cv2


class IngestSource(ABC):
    """Unified ingest interface for file, RTSP, and webcam sources."""

    @abstractmethod
    def open(self) -> None:
        ...

    @abstractmethod
    def read_frame(self) -> Optional[Tuple[object, float]]:
        """Returns a (frame, timestamp_seconds) tuple or None when stream ends."""
        ...

    @abstractmethod
    def close(self) -> None:
        ...


class _CvCaptureSource(IngestSource):
    def __init__(self, uri: str, fps: int) -> None:
        self.uri = uri
        self.fps = fps
        self.cap: Optional[cv2.VideoCapture] = None

    def open(self) -> None:
        self.cap = cv2.VideoCapture(self.uri)

    def read_frame(self) -> Optional[Tuple[object, float]]:
        if self.cap is None:
            return None
        ok, frame = self.cap.read()
        if not ok:
            return None
        ts = self.cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
        return frame, ts

    def close(self) -> None:
        if self.cap is not None:
            self.cap.release()
            self.cap = None


class FileIngestSource(_CvCaptureSource):
    def __init__(self, path: str, fps: int = 25) -> None:
        super().__init__(path, fps)


class RtspIngestSource(_CvCaptureSource):
    def __init__(self, rtsp_url: str, fps: int = 25, buffer_ms: int = 300) -> None:
        # RTSP buffering can be tuned via query params; keep it simple for MVP
        super().__init__(rtsp_url, fps)
        self.buffer_ms = buffer_ms


class WebcamIngestSource(_CvCaptureSource):
    def __init__(self, device_id: int = 0, fps: int = 25) -> None:
        super().__init__(str(device_id), fps)
