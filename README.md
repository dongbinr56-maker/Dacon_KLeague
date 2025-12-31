# 고정캠 기반 전술 피드백 데모 (Track2 이벤트 로그 우선)

Track2 이벤트 로그(`00_data/Track2/raw_data.csv`)를 기본 입력으로 삼아 **세션 생성 → 이벤트 재생 → Alert 생성 → Evidence(mp4/png) 서빙**까지 End-to-End로 돌릴 수 있는 MVP입니다.

## 데모 실행(10줄 내 요약)
1) Track2 데이터를 로컬에 준비한다: `00_data/Track2/raw_data.csv`, `00_data/Track2/match_info.csv` (레포에 포함하면 안 됨)  
2) `.env.example`를 `.env`로 복사 후 필요 시 경로/포트/오리진을 수정한다(`EVENTS_DATA_PATH`, `MATCH_INFO_PATH`, `FRONTEND_ORIGIN`, `EVIDENCE_PATH` 등)  
3) `docker-compose up --build`  
4) 백엔드: `http://localhost:8000/api/health`에서 Track2 검증 상태 확인(데이터 없으면 degraded와 원인 메시지 노출)  
5) 프론트: `http://localhost:3000` → 입력 모드에서 **Event Log (Track2)** 선택  
6) `game_id` 선택 + playback speed 입력 후 세션 생성 → 자동으로 Analysis 화면 이동  
7) Start 버튼 → 30~60초 내 Alert 생성(패턴: build_up_bias / transition_risk / final_third_pressure)  
8) Alert 클릭 → Evidence 링크(mp4/png)가 `/api/evidence/...` 경로로 열리고 404가 아니다  
9) 업로드한 파일은 `upload_index.json`으로 persist되어 재시작 후에도 다운로드 가능  
10) 문제가 있으면 `/api/health`의 `track2_error` 메시지를 확인하고 데이터/경로를 조정한다

## 구성 요소
- **Backend (FastAPI)**: Track2 이벤트 ingest, 세션/알림/업로드, evidence 서빙, health 체크
- **Frontend (Next.js)**: Event Log 입력 모드 + `game_id` 선택, 세션/알림 뷰어, evidence 링크 노출
- **Evidence 생성**: 이벤트 윈도우를 10초 mp4/overlay png로 렌더링

## 핵심 엔드포인트
- `GET /api/health` : Track2 검증 상태 확인
- `GET /api/track2/games` : 사용 가능한 `game_id` 목록
- `POST /api/sessions` : `source_type=event_log`, `game_id`, `playback_speed` 등으로 세션 생성
- `POST /api/sessions/{id}/start|stop` : 세션 제어
- `GET /api/sessions/{id}/alerts` / `WS /api/ws/sessions/{id}` : 알림 수신
- Evidence 정적 서빙: `/api/evidence/{session_id}/clip_{alert_id}.mp4`, `overlay_{alert_id}.png`

## 데이터/재현성
- Track2가 기본 입력이며, 외부 데이터는 필요하지 않습니다.
- 데이터 경로 기본값은 `backend/app/core/config.py`에 정의되어 있으며 ENV로 덮어쓸 수 있습니다. 데이터가 없으면 `/api/health`가 degraded 상태와 원인을 반환합니다.
- 외부 데이터를 추가로 쓸 경우 **무료/재현 가능/라이선스 명시** + 수집 스크립트를 `docs/external_data.md`에 기록해야 합니다.

## 스모크/데모 테스트
- `scripts/demo.sh`는 health → game 목록 → 세션 생성/시작 → alert 확인 → evidence mp4/png 200 응답까지 자동 검증합니다.
- 기존 `scripts/smoke_demo.sh`도 동일 플로우를 빠르게 확인할 수 있습니다.

## 문서
- `docs/ARCHITECTURE.md` : 전체 아키텍처 개요
- `docs/MVP_DEMO_GUIDE.md` : 추가 데모 팁
