# 고정캠 기반 전술 피드백 서비스 아키텍처 (MVP)

본 문서는 고정캠 영상 기반 전술 피드백 서비스의 MVP 아키텍처를 요약한다. 추가 요구사항인 **입력 소스 선택(Live RTSP / 업로드 파일)**을 반영하여 설계하였다.

## 구성 요소

- **Backend (FastAPI)**: 세션 생성/시작/정지, 업로드 처리, WebSocket 알림 스트림.
- **Ingest 모듈**: 통합 인터페이스 `IngestSource` 기반의 File / RTSP / Webcam 구현.
- **Analysis Pipeline (향후 확장)**: 캘리브레이션 → 탐지/트래킹 → 피처 → 패턴 → Evidence → Feedback.
- **Frontend (Next.js)**: 입력 소스 선택 화면, 세션 목록, 알림 표시(placeholder).
- **Infra**: Docker Compose로 backend/frontend/redis/postgres/minio 실행.

## Ingest 인터페이스

`app/services/ingest/base.py`

```python
class IngestSource(ABC):
    def open(self) -> None: ...
    def read_frame(self) -> Optional[Tuple[object, float]]: ...
    def close(self) -> None: ...

class FileIngestSource(IngestSource):
    ...
class RtspIngestSource(IngestSource):
    ...
class WebcamIngestSource(IngestSource):
    ...
```

- 파일 모드: `FileIngestSource(path, fps)`
- 라이브 모드: `RtspIngestSource(rtsp_url, fps, buffer_ms)`
- 데모 캡처: `WebcamIngestSource(device_id, fps)`
- 동일 파이프라인에서 소스만 교체 가능.

## 세션/알림 흐름

1. **POST /api/sessions**: 소스 타입(file/rtsp/webcam), 모드(offline_realtime/live), fps, buffer_ms 입력.
2. **POST /api/sessions/{id}/start**: 상태 `CONNECTING → RUNNING` 전환 후 분석 태스크 시작(현재는 placeholder 알림).
3. **WebSocket /api/ws/sessions/{id}**: 상태 이벤트 및 알림 실시간 push.
4. **POST /api/uploads**: mp4 업로드 → `file_id, storage_url` 반환. 반환된 `file_id`를 세션 생성 시 `path` 또는 `file_id`로 사용.

## 상태 머신

- CREATED → CONNECTING → RUNNING → STOPPED
- 라이브 연결 문제 발생 시: RUNNING → LOST (향후 재연결 로직 추가 예정)

## Docker Compose 서비스

- backend (FastAPI)
- frontend (Next.js)
- redis (분산 작업 큐 예정)
- postgres (메타데이터 저장 예정)
- minio (클립/오버레이 저장 예정)

## 향후 확장 포인트

- 캘리브레이션, 탐지/트래킹, 패턴 탐지, Evidence 생성 모듈 연결.
- 알림 근거 강제(클립/오버레이/수치) 로직 추가.
- 업로드 모드: Offline-RealTime 시뮬레이션, Faster-than-real-time 옵션.
- 라이브 모드: 프레임 드롭/버퍼 정책, LOST → RUNNING 재연결.
