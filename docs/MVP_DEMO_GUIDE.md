# MVP 데모 가이드 (고정캠 전술 피드백)

본 가이드는 업로드/라이브 입력 모드 선택을 포함한 데모 진행 방법을 설명한다.

## 준비

- Docker와 Docker Compose 설치
- `.env` (선택)에서 `FRONTEND_ORIGIN`, `STORAGE_PATH` 등 환경 설정

## 실행

```bash
docker-compose up --build
```

- 백엔드: http://localhost:8000
- 프론트엔드: http://localhost:3000

## 입력 모드 선택

### 1) 업로드/파일 재생 모드 (Upload / Offline-RealTime)
1. 프론트엔드 시작 화면에서 "업로드/파일 재생" 선택
2. mp4 경로 입력 또는 업로드 API(`/api/uploads`)로 업로드하여 받은 `file_id` 입력
3. 세션 생성 버튼 클릭 → 목록에서 세션 선택 후 시작
4. WebSocket을 통해 placeholder 알림 수신(실제 분석 파이프라인 연결 예정)

### 2) 라이브 RTSP 모드 (Live Capture)
1. 시작 화면에서 "라이브 RTSP" 선택
2. RTSP URL 입력 (예: `rtsp://localhost:8554/live`)
3. 세션 생성 후 시작 → 상태 `CONNECTING → RUNNING` 전환
4. WebSocket을 통해 실시간 알림 수신

## API 요약

- `POST /api/uploads`: mp4 업로드 → `{file_id, storage_url}` 반환
- `POST /api/sessions`: {source_type(file/rtsp/webcam), mode, fps, buffer_ms, path/rtsp_url/device_id}
- `POST /api/sessions/{id}/start`: 세션 시작
- `POST /api/sessions/{id}/stop`: 세션 정지
- `GET /api/sessions/{id}/alerts`: 알림 조회
- `WS /api/ws/sessions/{id}`: 상태/알림 스트림

## 데모 시나리오

1. 샘플 mp4 업로드 → 세션 생성(offline_realtime) → 시작
2. 30~60초 분석 롤링 윈도우를 가정한 placeholder 알림 확인
3. 라이브 RTSP 스트림 연결 테스트: ffmpeg -re로 송출 후 상태 전환 확인

## 향후 고도화 체크리스트

- 실제 분석 파이프라인 연결 및 근거(클립/오버레이/수치) 생성
- LOST 상태 및 재연결 처리
- Upload 모드의 Faster-than-real-time 옵션 지원
- UI: 알림 타임라인, 근거 패널, 오버레이, 진행률 표시
