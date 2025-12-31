# 고정캠 기반 실시간 전술 피드백 서비스 (MVP)

본 레포는 고정캠(전술캠) 영상을 입력으로 **실시간/준실시간 전술 패턴**을 탐지하고 **근거(클립/오버레이/수치)**와 함께 피드백을 제공하는 End-to-End 데모 구현을 목표로 합니다. 추가 요구사항인 **입력 모드 선택(Live RTSP vs 업로드 파일)**을 반영했습니다.

## 주요 구성

- **Backend (FastAPI)**: 세션 생성/시작/정지, 업로드, WebSocket 알림
- **Ingest 인터페이스**: 파일 / RTSP / 웹캠 소스를 통합하는 `IngestSource`
- **Frontend (Next.js)**: 입력 모드 선택 UI, 세션 목록, 알림 표시(placeholder)
- **Docker Compose**: backend, frontend, redis, postgres, minio 구성
- **Docs**: 아키텍처 및 데모 가이드

## 빠른 시작

```bash
docker-compose up --build
```
- Backend: http://localhost:8000
- Frontend: http://localhost:3000

## 파일 업로드 흐름
1. `POST /api/uploads`로 mp4 업로드 → `{file_id, storage_url}` 응답
2. `POST /api/sessions`에 `source_type: "file"` 및 `path` 또는 `file_id` 전달
3. `POST /api/sessions/{id}/start`로 세션 시작 → WebSocket으로 상태/알림 수신

## 라이브 RTSP 흐름
1. `POST /api/sessions`에 `source_type: "rtsp"`, `rtsp_url`, `mode: "live"` 전달
2. `POST /api/sessions/{id}/start` → 상태 `CONNECTING → RUNNING` 전환
3. WebSocket(`/api/ws/sessions/{id}`)으로 상태/알림 실시간 수신

## 현재 상태 (MVP Skeleton)
- 분석 파이프라인은 placeholder 알림을 주기적으로 송출하도록 시뮬레이션되어 있습니다.
- Ingest 인터페이스를 통해 파일/RTSP/웹캠 소스를 동일 파이프라인에 연결할 수 있는 구조를 마련했습니다.
- 추후 캘리브레이션, 탐지/트래킹, 패턴 룰, Evidence 생성 모듈을 연동할 수 있도록 디렉터리/스켈레톤을 준비했습니다.
