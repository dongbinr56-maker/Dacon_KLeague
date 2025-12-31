import os
import subprocess
from typing import Dict, Tuple

import cv2
import numpy as np

from app.core.config import get_settings


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
        video_path: str,
        ts_center: float,
        pattern_type: str,
        severity: str,
        metrics: Dict[str, float],
    ) -> Tuple[str, str]:
        session_dir = os.path.join(self.evidence_root, session_id)
        os.makedirs(session_dir, exist_ok=True)

        clip_path = os.path.join(session_dir, f"clip_{alert_id}.mp4")
        overlay_path = os.path.join(session_dir, f"overlay_{alert_id}.png")

        self._extract_clip(video_path, ts_center, clip_path)
        self._build_overlay(video_path, ts_center, overlay_path, pattern_type, severity, metrics)

        clip_url = f"{self.api_prefix}/evidence/{session_id}/clip_{alert_id}.mp4"
        overlay_url = f"{self.api_prefix}/evidence/{session_id}/overlay_{alert_id}.png"
        return clip_url, overlay_url

    def _extract_clip(self, video_path: str, ts_center: float, output_path: str) -> None:
        start = max(0.0, ts_center - 5.0)
        duration = 10.0

        copy_cmd = [
            "ffmpeg",
            "-y",
            "-ss",
            f"{start:.3f}",
            "-t",
            f"{duration:.3f}",
            "-i",
            video_path,
            "-c",
            "copy",
            output_path,
        ]

        result = subprocess.run(copy_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            return

        fallback_cmd = [
            "ffmpeg",
            "-y",
            "-ss",
            f"{start:.3f}",
            "-t",
            f"{duration:.3f}",
            "-i",
            video_path,
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "23",
            "-c:a",
            "aac",
            output_path,
        ]
        subprocess.run(fallback_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)

    def _build_overlay(
        self,
        video_path: str,
        ts_center: float,
        output_path: str,
        pattern_type: str,
        severity: str,
        metrics: Dict[str, float],
    ) -> None:
        cap = cv2.VideoCapture(video_path)
        cap.set(cv2.CAP_PROP_POS_MSEC, ts_center * 1000)
        ok, frame = cap.read()
        cap.release()

        if not ok or frame is None:
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(frame, "No frame available", (30, 240), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)

        overlay = frame.copy()
        text_lines = [
            f"Pattern: {pattern_type}",
            f"Severity: {severity}",
        ]
        for key, value in metrics.items():
            text_lines.append(f"{key}: {value:.3f}")

        y = 30
        for line in text_lines:
            cv2.putText(overlay, line, (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            y += 35

        flow_x_bias = metrics.get("flow_x_bias", 0.0)
        direction = (1 if flow_x_bias >= 0 else -1) * min(max(abs(flow_x_bias), 0.1), 1.0)
        center_y = overlay.shape[0] // 2
        center_x = overlay.shape[1] // 2
        arrow_length = int(150 * abs(direction))
        end_x = center_x + arrow_length if direction >= 0 else center_x - arrow_length
        cv2.arrowedLine(
            overlay,
            (center_x, center_y),
            (end_x, center_y),
            (255, 0, 0),
            4,
            tipLength=0.2,
        )

        cv2.imwrite(output_path, overlay)


evidence_builder = EvidenceBuilder()
