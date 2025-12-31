import os
from typing import Dict, List, Tuple

import cv2
import numpy as np

from app.core.config import get_settings
from app.schemas.event import EventRecord

PITCH_LENGTH = 105.0
PITCH_WIDTH = 68.0
SCALE = 8
FRAME_WIDTH = int(PITCH_LENGTH * SCALE)
FRAME_HEIGHT = int(PITCH_WIDTH * SCALE)


class EvidenceBuilder:
    def __init__(self) -> None:
        settings = get_settings()
        self.evidence_root = settings.evidence_path
        self.api_prefix = settings.api_prefix
        os.makedirs(self.evidence_root, exist_ok=True)

    def build_evidence(
        self,
        session_id: str,
        alert_id: str,
        ts_center: float,
        pattern_type: str,
        severity: str,
        metrics: Dict[str, float],
        events: List[EventRecord],
    ) -> Tuple[str, str]:
        session_dir = os.path.join(self.evidence_root, session_id)
        os.makedirs(session_dir, exist_ok=True)

        clip_path = os.path.join(session_dir, f"clip_{alert_id}.mp4")
        overlay_path = os.path.join(session_dir, f"overlay_{alert_id}.png")

        start_ts = max(0.0, ts_center - 5.0)
        end_ts = ts_center + 5.0

        sorted_events = sorted(events, key=lambda e: e.time_seconds)
        self._render_clip(sorted_events, start_ts, end_ts, clip_path)
        self._render_overlay(sorted_events, overlay_path, pattern_type, severity, metrics, ts_center)

        clip_url = f"{self.api_prefix}/evidence/{session_id}/clip_{alert_id}.mp4"
        overlay_url = f"{self.api_prefix}/evidence/{session_id}/overlay_{alert_id}.png"
        return clip_url, overlay_url

    def _render_clip(self, events: List[EventRecord], start_ts: float, end_ts: float, output_path: str) -> None:
        fps = 10
        duration = max(0.1, end_ts - start_ts)
        frame_count = max(1, int(duration * fps))
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(output_path, fourcc, fps, (FRAME_WIDTH, FRAME_HEIGHT))
        if not writer.isOpened():  # pragma: no cover - defensive
            return

        for frame_idx in range(frame_count):
            current_ts = start_ts + frame_idx / fps
            frame = self._draw_pitch()
            for ev in events:
                if start_ts <= ev.time_seconds <= current_ts:
                    self._draw_event(frame, ev)
            writer.write(frame)
        writer.release()

    def _render_overlay(
        self,
        events: List[EventRecord],
        output_path: str,
        pattern_type: str,
        severity: str,
        metrics: Dict[str, float],
        ts_center: float,
    ) -> None:
        frame = self._draw_pitch()
        for ev in events:
            if abs(ev.time_seconds - ts_center) <= 5:
                self._draw_event(frame, ev)

        y = 30
        cv2.putText(frame, f"Pattern: {pattern_type}", (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
        y += 35
        cv2.putText(frame, f"Severity: {severity}", (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
        y += 35
        for key, value in metrics.items():
            cv2.putText(
                frame,
                f"{key}: {value:.3f}",
                (20, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2,
            )
            y += 30

        cv2.imwrite(output_path, frame)

    def _draw_pitch(self) -> np.ndarray:
        frame = np.zeros((FRAME_HEIGHT, FRAME_WIDTH, 3), dtype=np.uint8)
        frame[:] = (0, 85, 0)
        cv2.rectangle(frame, (0, 0), (FRAME_WIDTH - 1, FRAME_HEIGHT - 1), (255, 255, 255), 2)
        mid_x = FRAME_WIDTH // 2
        cv2.line(frame, (mid_x, 0), (mid_x, FRAME_HEIGHT), (255, 255, 255), 2)
        center = (mid_x, FRAME_HEIGHT // 2)
        cv2.circle(frame, center, 40, (255, 255, 255), 2)

        penalty_w = int(16.5 * SCALE)
        box_h = int(40.3 * SCALE)
        cv2.rectangle(frame, (0, (FRAME_HEIGHT - box_h) // 2), (penalty_w, (FRAME_HEIGHT + box_h) // 2), (255, 255, 255), 2)
        cv2.rectangle(
            frame,
            (FRAME_WIDTH - penalty_w, (FRAME_HEIGHT - box_h) // 2),
            (FRAME_WIDTH, (FRAME_HEIGHT + box_h) // 2),
            (255, 255, 255),
            2,
        )
        return frame

    def _draw_event(self, frame: np.ndarray, event: EventRecord) -> None:
        start_px = self._to_px(event.start_x, event.start_y)
        end_px = self._to_px(event.end_x, event.end_y)
        color = self._color_for_event(event)

        if start_px and end_px:
            cv2.arrowedLine(frame, start_px, end_px, color, 3, tipLength=0.2)
        elif start_px:
            cv2.circle(frame, start_px, 6, color, -1)
        elif end_px:
            cv2.circle(frame, end_px, 6, color, -1)

    def _to_px(self, x: float | None, y: float | None) -> Tuple[int, int] | None:
        if x is None or y is None:
            return None
        px = int((x / PITCH_LENGTH) * FRAME_WIDTH)
        py = int((y / PITCH_WIDTH) * FRAME_HEIGHT)
        return (px, py)

    def _color_for_event(self, event: EventRecord) -> Tuple[int, int, int]:
        type_name = (event.type_name or "").lower()
        if type_name == "shot":
            return (0, 0, 255)
        if type_name == "pass":
            return (0, 200, 255)
        if type_name == "carry":
            return (255, 140, 0)
        if "turnover" in type_name or (event.result_name or "").lower() == "unsuccessful":
            return (180, 180, 180)
        return (255, 255, 0)


evidence_builder = EvidenceBuilder()
